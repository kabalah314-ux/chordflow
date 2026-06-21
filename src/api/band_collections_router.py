"""
Repertorios de banda — colecciones temáticas (T-114) — `SongCollection`/`SongCollectionItem`.

`GET    /bands/{id}/collections`        → lista las colecciones de la banda (miembros).
`POST   /bands/{id}/collections`        → crea una colección con canciones del REPERTORIO (no guest).
`GET    /bands/{id}/collections/{cid}`  → detalle con sus canciones (miembros).
`PATCH  /bands/{id}/collections/{cid}`  → renombrar / cambiar canciones (no guest).
`DELETE /bands/{id}/collections/{cid}`  → soft delete (no guest).

Diferenciación con Setlist: una colección AGRUPA por tema ("acústico", "cañero", "bodas"), sin orden
de bolo ni notas por canción. Sus canciones solo pueden ser del repertorio de ESA banda
(`Song.band_id == band`). Aislamiento por `require_band_member` + filtro `band_id` (regla de oro).
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.band_auth import require_band_member
from ..services.db import get_db
from ..services.models import BandMembership, Song, SongCollection, SongCollectionItem, _utcnow
from ..services.schemas import (
    CollectionCreate,
    CollectionItemOut,
    CollectionResponse,
    CollectionSummary,
    CollectionUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands/{band_id}/collections", tags=["band-collections"])


def _deny_guests(membership: BandMembership) -> None:
    if membership.role == "guest":
        raise HTTPException(status_code=403, detail="Un invitado no puede editar los repertorios")


def _valid_band_song_ids(db: Session, band_id: str, song_ids: List[str]) -> List[str]:
    """Filtra `song_ids` dejando solo los del REPERTORIO de la banda (no borrados), preservando orden
    y sin duplicados."""
    if not song_ids:
        return []
    rows = (db.query(Song.id)
            .filter(Song.band_id == band_id, Song.deleted_at.is_(None), Song.id.in_(song_ids))
            .all())
    en_repertorio = {r[0] for r in rows}
    out, seen = [], set()
    for sid in song_ids:
        if sid in en_repertorio and sid not in seen:
            out.append(sid)
            seen.add(sid)
    return out


def _set_items(db: Session, col: SongCollection, song_ids: List[str], band_id: str) -> None:
    """Reemplaza las canciones de la colección por las válidas del repertorio (en orden de llegada)."""
    for it in list(col.items):
        db.delete(it)
    db.flush()
    for pos, sid in enumerate(_valid_band_song_ids(db, band_id, song_ids)):
        col.items.append(SongCollectionItem(song_id=sid, position=pos))


def _to_response(col: SongCollection) -> CollectionResponse:
    """Respuesta con las canciones de la colección, omitiendo las borradas."""
    items = []
    for it in col.items:
        song = it.song
        if song is None or song.deleted_at is not None:
            continue
        items.append(CollectionItemOut(song_id=song.id, position=it.position,
                                       title=song.title, artist=song.artist, bpm=song.bpm))
    return CollectionResponse(id=col.id, name=col.name, band_id=col.band_id,
                              created_at=col.created_at, updated_at=col.updated_at, items=items)


def _get_collection(db: Session, band_id: str, collection_id: str) -> SongCollection:
    col = (db.query(SongCollection)
           .filter(SongCollection.id == collection_id, SongCollection.band_id == band_id,
                   SongCollection.deleted_at.is_(None)).first())
    if col is None:
        raise HTTPException(status_code=404, detail="Repertorio no encontrado")
    return col


@router.get("/", response_model=List[CollectionSummary])
def list_collections(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    cols = (db.query(SongCollection)
            .filter(SongCollection.band_id == band_id, SongCollection.deleted_at.is_(None))
            .order_by(SongCollection.updated_at.desc()).all())
    return [CollectionSummary(id=c.id, name=c.name, band_id=c.band_id,
                              updated_at=c.updated_at, song_count=len(c.items)) for c in cols]


@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    band_id: str,
    payload: CollectionCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    _deny_guests(membership)
    col = SongCollection(name=payload.name, band_id=band_id)
    db.add(col)
    _set_items(db, col, payload.song_ids, band_id)
    db.commit()
    db.refresh(col)
    return _to_response(col)


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    band_id: str,
    collection_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    return _to_response(_get_collection(db, band_id, collection_id))


@router.patch("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    band_id: str,
    collection_id: str,
    payload: CollectionUpdate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    _deny_guests(membership)
    col = _get_collection(db, band_id, collection_id)
    if payload.name is not None:
        col.name = payload.name
    if payload.song_ids is not None:
        _set_items(db, col, payload.song_ids, band_id)
    db.commit()
    db.refresh(col)
    return _to_response(col)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    band_id: str,
    collection_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    _deny_guests(membership)
    col = _get_collection(db, band_id, collection_id)
    col.deleted_at = _utcnow()
    db.commit()
