"""
Biblioteca global / catálogo público (V3-F9, D9).

El RECLAMO de la app: un buscador de un catálogo de muchos artistas que crece con lo que sube la
gente ("¿no la encuentras? ponla aquí"). Es un **plano de datos separado** (copia desacoplada, D1):
publicar crea un snapshot independiente; los datos privados de la banda NUNCA entran aquí.

`POST /catalog/publish`                 → subir una de mis canciones al catálogo (flujo "ponla aquí").
`GET  /catalog/search?q=`               → buscar por título/artista (cualquier usuario autenticado).
`GET  /catalog/scores/{id}`             → detalle (partitura + comentarios + mi valoración).
`POST /catalog/scores/{id}/import`      → importar a mi banda o a mi espacio personal (1 clic).
`PUT  /catalog/scores/{id}/rating`      → valorar (1–5, lo fiel/completa que es).
`POST /catalog/scores/{id}/comments`    → comentar ("falta el puente", etc.).

Auth: `get_current_user` (cualquier usuario autenticado; la navegación SIN login + SEO se añade
después con el plano público). Importar a una banda valida pertenencia.
"""

import logging
import re
import unicodedata
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.db import get_db
from ..services.models import (
    Band,
    BandMembership,
    MusicalWork,
    MusicianProfile,
    PublicScore,
    ScoreComment,
    ScoreRating,
    Song,
)
from ..services.schemas import (
    CatalogCommentCreate,
    CatalogImportRequest,
    CatalogPublishRequest,
    PublicScoreDetail,
    PublicScoreSummary,
    ScoreCommentOut,
    ScoreRatingSet,
    SectionCreate,
)
from .songs_router import _append_sections

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _norm(s: Optional[str]) -> str:
    """Normaliza artista/título para buscar y agrupar versiones (sin acentos, minúsculas)."""
    s = unicodedata.normalize("NFKD", (s or "").strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _song_to_content(song: Song) -> list:
    """Snapshot COMPLETO del árbol de la canción en la forma de SectionCreate (round-trip exacto al
    importar): incluye acordes, tablaturas y los campos de sección/línea (repeat/color/hint)."""
    out = []
    for sec in song.sections:
        lines = []
        for ln in sec.lines:
            chords = [{
                "chord_name": c.chord_name, "char_position": c.char_position,
                "beat_offset": c.beat_offset, "duration_beats": c.duration_beats,
            } for c in ln.chords]
            tab_strings = [{
                "string_number": t.string_number, "fret_sequence": t.fret_sequence,
            } for t in ln.tab_strings]
            lines.append({
                "order": ln.order, "type": ln.type, "content": ln.content,
                "beat_start": ln.beat_start, "beat_duration": ln.beat_duration,
                "display_hint": ln.display_hint, "chords": chords, "tab_strings": tab_strings,
            })
        out.append({
            "name": sec.name, "order": sec.order, "repeat_count": sec.repeat_count,
            "color_tag": sec.color_tag, "lines": lines,
        })
    return out


# La vista PÚBLICA del catálogo recorta la letra (D2): se muestran acordes + estructura, pero la
# letra solo como preview; la letra completa va en el `content_json` de BD y solo se entrega al
# IMPORTAR a tu copia privada. Umbral ajustable (decisión legal de Oscar).
_LYRIC_PREVIEW = 40


def _public_sections(sections: list) -> list:
    """Copia de las secciones con la letra RECORTADA para la vista pública (no muta el snapshot)."""
    pub = []
    for sec in sections or []:
        lines = []
        for ln in (sec.get("lines") or []):
            ln2 = dict(ln)
            if ln2.get("type") == "lyric":
                c = ln2.get("content") or ""
                if len(c) > _LYRIC_PREVIEW:
                    ln2["content"] = c[:_LYRIC_PREVIEW].rstrip() + "…"
            lines.append(ln2)
        sec2 = dict(sec)
        sec2["lines"] = lines
        pub.append(sec2)
    return pub


def _name_of(db: Session, user_id: str) -> Optional[str]:
    row = db.query(MusicianProfile.display_name).filter(MusicianProfile.id == user_id).first()
    return row[0] if row else None


def _get_score(db: Session, score_id: str) -> PublicScore:
    sc = (db.query(PublicScore)
          .filter(PublicScore.id == score_id, PublicScore.deleted_at.is_(None),
                  PublicScore.status == "published")
          .first())
    if sc is None:
        raise HTTPException(status_code=404, detail="Partitura no encontrada en el catálogo")
    return sc


def _summary(sc: PublicScore, publisher_name: Optional[str]) -> PublicScoreSummary:
    s = PublicScoreSummary.model_validate(sc)
    s.publisher_name = publisher_name
    return s


@router.post("/publish", response_model=PublicScoreSummary, status_code=status.HTTP_201_CREATED)
def publish(
    payload: CatalogPublishRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Sube una de mis canciones al catálogo global (flujo "ponla aquí", D9)."""
    song = (db.query(Song)
            .filter(Song.id == payload.song_id, Song.deleted_at.is_(None)).first())
    if song is None:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    # Debe ser mía: personal (owner_id) o de una banda en la que soy miembro activo.
    if song.band_id is None:
        if song.owner_id != user_id:
            raise HTTPException(status_code=403, detail="No es tu canción")
    else:
        member = (db.query(BandMembership.id)
                  .filter(BandMembership.band_id == song.band_id,
                          BandMembership.user_id == user_id,
                          BandMembership.status == "active").first())
        if not member:
            raise HTTPException(status_code=403, detail="No perteneces a esa banda")

    # D9: una canción → una publicación. Evita duplicados al re-pulsar "publicar".
    dup = (db.query(PublicScore.id)
           .filter(PublicScore.source_song_id == song.id,
                   PublicScore.publisher_id == user_id,
                   PublicScore.deleted_at.is_(None)).first())
    if dup:
        raise HTTPException(status_code=409, detail="Ya has publicado esta canción al catálogo")

    norm_title, norm_artist = _norm(song.title), _norm(song.artist)

    def _get_or_create_work():
        w = (db.query(MusicalWork)
             .filter(MusicalWork.norm_title == norm_title,
                     MusicalWork.norm_artist == norm_artist).first())
        if w is None:
            w = MusicalWork(title=song.title, artist=song.artist,
                            norm_title=norm_title, norm_artist=norm_artist)
            db.add(w)
            db.flush()
        return w

    try:
        work = _get_or_create_work()
        sc = PublicScore(
            work_id=work.id, publisher_id=user_id, source_band_id=song.band_id,
            source_song_id=song.id, title=song.title, artist=song.artist,
            key_root=song.key_root, key_mode=song.key_mode, bpm=song.bpm,
            reference_url=song.reference_url, content_json=_song_to_content(song),
        )
        db.add(sc)
        db.commit()
    except IntegrityError:
        # Carrera: otro publicó la misma obra normalizada entre el SELECT y el INSERT del work.
        db.rollback()
        work = (db.query(MusicalWork)
                .filter(MusicalWork.norm_title == norm_title,
                        MusicalWork.norm_artist == norm_artist).first())
        sc = PublicScore(
            work_id=work.id, publisher_id=user_id, source_band_id=song.band_id,
            source_song_id=song.id, title=song.title, artist=song.artist,
            key_root=song.key_root, key_mode=song.key_mode, bpm=song.bpm,
            reference_url=song.reference_url, content_json=_song_to_content(song),
        )
        db.add(sc)
        db.commit()
    db.refresh(sc)
    return _summary(sc, _name_of(db, user_id))


@router.get("/search", response_model=List[PublicScoreSummary])
def search(
    q: str = Query("", max_length=120),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
):
    """Busca en el catálogo por título/artista. Sin `q`, devuelve lo más popular/reciente."""
    query = db.query(PublicScore).filter(
        PublicScore.deleted_at.is_(None), PublicScore.status == "published")
    term = _norm(q)
    if term:
        like = f"%{term}%"
        query = query.filter(
            func.lower(PublicScore.title).like(like) | func.lower(PublicScore.artist).like(like))
    scores = query.order_by(PublicScore.import_count.desc(),
                            PublicScore.created_at.desc()).limit(limit).all()
    if not scores:
        return []
    names = dict(
        db.query(MusicianProfile.id, MusicianProfile.display_name)
        .filter(MusicianProfile.id.in_([s.publisher_id for s in scores])).all())
    return [_summary(s, names.get(s.publisher_id)) for s in scores]


@router.get("/scores/{score_id}", response_model=PublicScoreDetail)
def get_score(
    score_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Detalle: partitura (para el visor), valoración, comentarios y mi voto."""
    sc = _get_score(db, score_id)
    detail = PublicScoreDetail.model_validate(sc)
    detail.publisher_name = _name_of(db, sc.publisher_id)
    # D2: letra RECORTADA en el catálogo público; la completa solo al importar.
    detail.sections = _public_sections(sc.content_json or [])
    rows = (db.query(ScoreComment, MusicianProfile.display_name)
            .outerjoin(MusicianProfile, MusicianProfile.id == ScoreComment.user_id)
            .filter(ScoreComment.public_score_id == sc.id, ScoreComment.deleted_at.is_(None))
            .order_by(ScoreComment.created_at.asc()).all())
    detail.comments = [
        ScoreCommentOut(id=c.id, user_id=c.user_id, author_name=name, body=c.body,
                        created_at=c.created_at)
        for c, name in rows]
    mine = (db.query(ScoreRating.stars)
            .filter(ScoreRating.public_score_id == sc.id, ScoreRating.user_id == user_id).first())
    detail.my_rating = mine[0] if mine else None
    return detail


@router.post("/scores/{score_id}/import", status_code=status.HTTP_201_CREATED)
def import_score(
    score_id: str,
    payload: CatalogImportRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Copia la partitura del catálogo a mi espacio (banda mía o personal). Devuelve el id nuevo."""
    sc = _get_score(db, score_id)
    if payload.band_id is not None:
        # La banda destino debe existir (no borrada) y yo ser miembro activo.
        member = (db.query(BandMembership.id)
                  .join(Band, Band.id == BandMembership.band_id)
                  .filter(BandMembership.band_id == payload.band_id,
                          BandMembership.user_id == user_id,
                          BandMembership.status == "active",
                          Band.deleted_at.is_(None)).first())
        if not member:
            raise HTTPException(status_code=403, detail="No perteneces a esa banda")

    try:
        new_song = Song(title=sc.title, artist=sc.artist, bpm=sc.bpm or 120,
                        key_root=sc.key_root, key_mode=sc.key_mode,
                        reference_url=sc.reference_url, owner_id=user_id, band_id=payload.band_id)
        # Import = copia COMPLETA (con la letra íntegra del content_json de BD, no la recortada).
        _append_sections(new_song, [SectionCreate(**s) for s in (sc.content_json or [])])
        db.add(new_song)
        sc.import_count = (sc.import_count or 0) + 1
        db.commit()
        db.refresh(new_song)
    except Exception:
        db.rollback()
        logger.error("Error importando del catálogo", exc_info=True)
        raise HTTPException(status_code=400, detail="No se pudo importar la partitura")
    return {"song_id": new_song.id, "band_id": payload.band_id}


@router.put("/scores/{score_id}/rating", response_model=PublicScoreSummary)
def set_rating(
    score_id: str,
    payload: ScoreRatingSet,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Valorar (1–5, lo fiel/completa que es). Una valoración por usuario; recalcula la media."""
    sc = _get_score(db, score_id)
    rating = (db.query(ScoreRating)
              .filter(ScoreRating.public_score_id == sc.id, ScoreRating.user_id == user_id).first())
    if rating is None:
        db.add(ScoreRating(public_score_id=sc.id, user_id=user_id, stars=payload.stars))
    else:
        rating.stars = payload.stars
    db.flush()
    agg = (db.query(func.count(ScoreRating.id), func.avg(ScoreRating.stars))
           .filter(ScoreRating.public_score_id == sc.id).first())
    sc.rating_count = int(agg[0] or 0)
    sc.rating_avg = Decimal(str(round(float(agg[1] or 0), 2)))   # Decimal coherente con la columna
    db.commit()
    db.refresh(sc)
    return _summary(sc, _name_of(db, sc.publisher_id))


@router.post("/scores/{score_id}/comments", response_model=ScoreCommentOut,
             status_code=status.HTTP_201_CREATED)
def add_comment(
    score_id: str,
    payload: CatalogCommentCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Comentar una partitura del catálogo."""
    sc = _get_score(db, score_id)
    c = ScoreComment(public_score_id=sc.id, user_id=user_id, body=payload.body)
    db.add(c)
    db.commit()
    db.refresh(c)
    return ScoreCommentOut(id=c.id, user_id=user_id, author_name=_name_of(db, user_id),
                           body=c.body, created_at=c.created_at)
