"""
Repertorio de banda (Fase 8, T-058) — canciones con `band_id`.

`GET    /bands/{id}/songs`        → lista el repertorio de la banda (miembros).
`POST   /bands/{id}/songs`        → crea una canción nueva en el repertorio (miembros, no guest).
`POST   /bands/{id}/songs/copy`   → copia una de MIS canciones personales a la banda (decisión §7:
                                    por COPIA → la banda tiene su propia versión autoritativa).
`DELETE /bands/{id}/songs/{sid}`  → quita (soft delete) una canción del repertorio (miembros, no guest).

Reproducir/editar una canción de banda usa las rutas `/songs/{id}` de siempre, que ya autorizan a
los miembros de la banda (la joya intacta). Aislamiento: todo pasa por `require_band_member` y filtra
por `band_id`; un ajeno → 404.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..services.band_auth import require_band_member
from ..services.db import get_db
from ..services.models import (
    BandMembership,
    ChordMarker,
    Line,
    Section,
    Song,
    TabLine,
    _utcnow,
)
from ..services.schemas import SongCopyToBand, SongCreate, SongResponse, SongSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands/{band_id}/songs", tags=["band-repertoire"])


def _deny_guests(membership: BandMembership) -> None:
    """Los invitados (guest) ven el repertorio pero no lo editan (matriz §C.2)."""
    if membership.role == "guest":
        raise HTTPException(status_code=403, detail="Un invitado no puede editar el repertorio")


def _append_sections(db_song: Song, sections) -> None:
    """Arma la estructura anidada (idéntico a songs_router; los cascades del ORM hacen el resto)."""
    for sec_data in sections:
        db_sec = Section(**sec_data.model_dump(exclude={"lines"}))
        db_song.sections.append(db_sec)
        for line_data in sec_data.lines:
            db_line = Line(**line_data.model_dump(exclude={"chords", "tab_strings"}))
            db_sec.lines.append(db_line)
            for chord_data in line_data.chords:
                db_line.chords.append(ChordMarker(**chord_data.model_dump()))
            for tab_data in line_data.tab_strings:
                db_line.tab_strings.append(TabLine(**tab_data.model_dump()))


# Columnas escalares de Song que se copian tal cual (todo menos id/owner/band/timestamps/relación).
_SONG_SCALAR_FIELDS = (
    "title", "artist", "album", "year", "bpm",
    "time_signature_num", "time_signature_den", "key_root", "key_mode",
    "tuning", "capo", "instrument", "format_version", "is_public",
    "source_type", "source_file_path", "tags", "duration_beats",
)


def _deep_copy_song(src: Song, *, band_id: str, owner_id: str) -> Song:
    """Copia profunda de una canción (metadatos + secciones→líneas→acordes/tabs) hacia una banda.
    La copia es independiente: editar el repertorio no toca la personal y viceversa (§7)."""
    dst = Song(band_id=band_id, owner_id=owner_id,
               **{f: getattr(src, f) for f in _SONG_SCALAR_FIELDS})
    for sec in sorted(src.sections, key=lambda s: s.order):
        d_sec = Section(name=sec.name, order=sec.order,
                        repeat_count=sec.repeat_count, color_tag=sec.color_tag)
        dst.sections.append(d_sec)
        for line in sorted(sec.lines, key=lambda x: x.order):
            d_line = Line(order=line.order, type=line.type, content=line.content,
                          beat_start=line.beat_start, beat_duration=line.beat_duration,
                          display_hint=line.display_hint)
            d_sec.lines.append(d_line)
            for ch in line.chords:
                d_line.chords.append(ChordMarker(
                    chord_name=ch.chord_name, char_position=ch.char_position,
                    beat_offset=ch.beat_offset, duration_beats=ch.duration_beats,
                    finger_diagram=ch.finger_diagram, barre=ch.barre,
                    muted_strings=ch.muted_strings))
            for tb in line.tab_strings:
                d_line.tab_strings.append(TabLine(
                    string_number=tb.string_number, fret_sequence=tb.fret_sequence))
    return dst


@router.get("/", response_model=List[SongSummary])
def list_band_songs(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Repertorio de la banda (ligero, con section_count en una query agregada)."""
    songs = (
        db.query(Song)
        .filter(Song.band_id == band_id, Song.deleted_at.is_(None))
        .all()
    )
    if not songs:
        return []
    counts = dict(
        db.query(Section.song_id, func.count(Section.id))
        .filter(Section.song_id.in_([s.id for s in songs]))
        .group_by(Section.song_id)
        .all()
    )
    for s in songs:
        s.section_count = counts.get(s.id, 0)
    return songs


@router.post("/", response_model=SongResponse, status_code=status.HTTP_201_CREATED)
def create_band_song(
    band_id: str,
    song: SongCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Crea una canción nueva directamente en el repertorio de la banda."""
    _deny_guests(membership)
    db_song = Song(**song.model_dump(exclude={"sections"}),
                   owner_id=membership.user_id, band_id=band_id)
    _append_sections(db_song, song.sections)
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


@router.post("/copy", response_model=SongResponse, status_code=status.HTTP_201_CREATED)
def copy_song_to_band(
    band_id: str,
    payload: SongCopyToBand,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Copia una de MIS canciones personales al repertorio de la banda (copia independiente)."""
    _deny_guests(membership)
    src = (
        db.query(Song)
        .filter(
            Song.id == payload.song_id,
            Song.owner_id == membership.user_id,
            Song.band_id.is_(None),          # solo se copian canciones personales propias
            Song.deleted_at.is_(None),
        )
        .first()
    )
    if src is None:
        raise HTTPException(status_code=404, detail="Canción personal no encontrada")
    dst = _deep_copy_song(src, band_id=band_id, owner_id=membership.user_id)
    db.add(dst)
    db.commit()
    db.refresh(dst)
    return dst


@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_band_song(
    band_id: str,
    song_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Quita (soft delete) una canción del repertorio de la banda."""
    _deny_guests(membership)
    song = (
        db.query(Song)
        .filter(Song.id == song_id, Song.band_id == band_id, Song.deleted_at.is_(None))
        .first()
    )
    if song is None:
        raise HTTPException(status_code=404, detail="Canción no encontrada en el repertorio")
    song.deleted_at = _utcnow()
    db.commit()
