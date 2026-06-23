import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.db import get_db
from ..services.models import BandMembership, Setlist, SetlistItem, Song, _utcnow
from ..services.schemas import (
    SetlistCreate,
    SetlistItemOut,
    SetlistResponse,
    SetlistSummary,
    SetlistUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/setlists", tags=["setlists"])


def _is_active_member(db: Session, band_id: str, user_id: str) -> bool:
    return (
        db.query(BandMembership)
        .filter(
            BandMembership.band_id == band_id,
            BandMembership.user_id == user_id,
            BandMembership.status == "active",
        )
        .first()
        is not None
    )


def _valid_song_ids(db: Session, user_id: str, song_ids: List[str]) -> List[str]:
    """Filtra `song_ids` dejando solo los que son del usuario y no están borrados,
    PRESERVANDO el orden recibido. Evita meter canciones ajenas o inexistentes."""
    if not song_ids:
        return []
    rows = (db.query(Song.id)
            .filter(Song.owner_id == user_id, Song.deleted_at.is_(None), Song.id.in_(song_ids))
            .all())
    propias = {r[0] for r in rows}
    return [sid for sid in song_ids if sid in propias]


def _pairs_from_payload(payload) -> list:
    """[(song_id, note)] en orden: prioriza `items` (con nota); si no, `song_ids` (compat, sin nota)."""
    if payload.items is not None:
        return [(i.song_id, i.note) for i in payload.items]
    return [(sid, None) for sid in (payload.song_ids or [])]


def _set_items(db: Session, setlist: Setlist, pairs: list, user_id: str) -> None:
    """Reemplaza las entradas del repertorio por `pairs` [(song_id, note)] (validadas), en orden."""
    for it in list(setlist.items):
        db.delete(it)
    db.flush()
    valid = set(_valid_song_ids(db, user_id, [sid for sid, _ in pairs]))
    pos = 0
    for sid, note in pairs:
        if sid not in valid:
            continue
        setlist.items.append(SetlistItem(song_id=sid, position=pos, note=note))
        pos += 1


def _to_response(setlist: Setlist) -> SetlistResponse:
    """Construye la respuesta con las canciones en orden, omitiendo las borradas."""
    items = []
    for it in setlist.items:
        song = it.song
        if song is None or song.deleted_at is not None:
            continue
        items.append(SetlistItemOut(song_id=song.id, position=it.position,
                                    title=song.title, artist=song.artist, bpm=song.bpm,
                                    note=it.note))
    return SetlistResponse(id=setlist.id, name=setlist.name, owner_id=setlist.owner_id,
                           band_id=setlist.band_id, created_at=setlist.created_at,
                           updated_at=setlist.updated_at, items=items)


@router.get("/", response_model=List[SetlistSummary])
def list_setlists(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """Lista los repertorios PERSONALES del usuario (band_id IS NULL), no borrados. Los de banda
    se listan en /bands/{id}/setlists."""
    try:
        setlists = (db.query(Setlist)
                    .filter(Setlist.owner_id == user_id, Setlist.deleted_at.is_(None),
                            Setlist.band_id.is_(None))
                    .order_by(Setlist.updated_at.desc()).all())
        return [SetlistSummary(id=s.id, name=s.name, updated_at=s.updated_at,
                               song_count=len(s.items)) for s in setlists]
    except SQLAlchemyError as e:
        logger.error(f"Error listando setlists: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")


@router.post("/", response_model=SetlistResponse, status_code=status.HTTP_201_CREATED)
def create_setlist(payload: SetlistCreate, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    """Crea un repertorio con sus canciones en orden."""
    try:
        sl = Setlist(name=payload.name, owner_id=user_id)
        db.add(sl)
        _set_items(db, sl, _pairs_from_payload(payload), user_id)
        db.commit()
        db.refresh(sl)
        logger.info(f"Setlist creado: {sl.id}")
        return _to_response(sl)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creando setlist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")


@router.get("/{setlist_id}", response_model=SetlistResponse)
def get_setlist(setlist_id: str, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    """Detalle de un setlist. Lo usa el reproductor: autoriza al dueño (personal) o a un miembro
    activo de la banda (setlist de banda); ajeno → 404."""
    try:
        sl = (db.query(Setlist)
              .filter(Setlist.id == setlist_id, Setlist.deleted_at.is_(None)).first())
        if not sl:
            raise HTTPException(status_code=404, detail="Repertorio no encontrado")
        if sl.band_id is None:
            if sl.owner_id != user_id:
                raise HTTPException(status_code=404, detail="Repertorio no encontrado")
        elif not _is_active_member(db, sl.band_id, user_id):
            raise HTTPException(status_code=404, detail="Repertorio no encontrado")
        return _to_response(sl)
    except SQLAlchemyError as e:
        logger.error(f"Error recuperando setlist {setlist_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")
    except HTTPException:
        raise


@router.patch("/{setlist_id}", response_model=SetlistResponse)
def update_setlist(setlist_id: str, payload: SetlistUpdate, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    """Renombra y/o reemplaza la lista de canciones (reordenar/añadir/quitar)."""
    try:
        sl = (db.query(Setlist)
              .filter(Setlist.id == setlist_id, Setlist.owner_id == user_id,
                      Setlist.deleted_at.is_(None), Setlist.band_id.is_(None)).first())
        if not sl:
            raise HTTPException(status_code=404, detail="Repertorio no encontrado")
        if payload.name is not None:
            sl.name = payload.name
        if payload.song_ids is not None or payload.items is not None:
            _set_items(db, sl, _pairs_from_payload(payload), user_id)
        db.commit()
        db.refresh(sl)
        return _to_response(sl)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error actualizando setlist {setlist_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")
    except HTTPException:
        db.rollback()
        raise


@router.delete("/{setlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_setlist(setlist_id: str, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    """Soft delete del repertorio PERSONAL (los de banda se borran en /bands/{id}/setlists)."""
    try:
        sl = (db.query(Setlist)
              .filter(Setlist.id == setlist_id, Setlist.owner_id == user_id,
                      Setlist.deleted_at.is_(None), Setlist.band_id.is_(None)).first())
        if not sl:
            raise HTTPException(status_code=404, detail="Repertorio no encontrado")
        sl.deleted_at = _utcnow()
        db.commit()
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error eliminando setlist {setlist_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")
    except HTTPException:
        db.rollback()
        raise
