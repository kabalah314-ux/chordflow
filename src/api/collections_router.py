"""
Colecciones PERSONALES — agrupaciones temáticas de TUS canciones (sin orden de bolo), el equivalente
personal de los "Repertorios" de banda (T-114). `SongCollection`/`SongCollectionItem` con
`band_id` NULL + `owner_id`.

`GET    /collections`        → lista mis colecciones personales.
`POST   /collections`        → crea una con mis canciones.
`GET    /collections/{id}`   → detalle con sus canciones.
`PATCH  /collections/{id}`   → renombrar / cambiar canciones.
`DELETE /collections/{id}`   → soft delete.

Las canciones de una colección personal solo pueden ser MÍAS y personales (`Song.owner_id == yo`,
`band_id` NULL), igual que las que muestra `GET /songs/`. Aislamiento por `owner_id` (ajeno → 404).
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.db import get_db
from ..services.models import Song, SongCollection, SongCollectionItem, _utcnow
from ..services.schemas import (
    CollectionCreate,
    CollectionItemOut,
    CollectionResponse,
    CollectionSummary,
    CollectionUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["collections"])


def _valid_song_ids(db: Session, user_id: str, song_ids: List[str]) -> List[str]:
    """Filtra `song_ids` dejando solo MIS canciones personales (owner, band_id NULL, no borradas),
    preservando el orden de llegada y sin duplicados."""
    if not song_ids:
        return []
    rows = (db.query(Song.id)
            .filter(Song.owner_id == user_id, Song.band_id.is_(None),
                    Song.deleted_at.is_(None), Song.id.in_(song_ids))
            .all())
    mias = {r[0] for r in rows}
    out, seen = [], set()
    for sid in song_ids:
        if sid in mias and sid not in seen:
            out.append(sid)
            seen.add(sid)
    return out


def _set_items(db: Session, col: SongCollection, song_ids: List[str], user_id: str) -> None:
    """Reemplaza las canciones de la colección por las válidas (mías y personales), en orden."""
    for it in list(col.items):
        db.delete(it)
    db.flush()
    for pos, sid in enumerate(_valid_song_ids(db, user_id, song_ids)):
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


def _get_collection(db: Session, user_id: str, collection_id: str) -> SongCollection:
    """Mi colección personal o 404 (aislamiento: ajena/de banda/borrada → 404)."""
    col = (db.query(SongCollection)
           .filter(SongCollection.id == collection_id, SongCollection.owner_id == user_id,
                   SongCollection.band_id.is_(None), SongCollection.deleted_at.is_(None)).first())
    if col is None:
        raise HTTPException(status_code=404, detail="Colección no encontrada")
    return col


@router.get("/", response_model=List[CollectionSummary])
def list_collections(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """Mis colecciones personales (band_id NULL), no borradas, más recientes primero."""
    cols = (db.query(SongCollection)
            .filter(SongCollection.owner_id == user_id, SongCollection.band_id.is_(None),
                    SongCollection.deleted_at.is_(None))
            .order_by(SongCollection.updated_at.desc()).all())
    return [CollectionSummary(id=c.id, name=c.name, band_id=None,
                              updated_at=c.updated_at, song_count=len(c.items)) for c in cols]


@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db),
                      user_id: str = Depends(get_current_user)):
    """Crea una colección personal con mis canciones (las ajenas/no personales se descartan)."""
    col = SongCollection(name=payload.name, owner_id=user_id)
    db.add(col)
    _set_items(db, col, payload.song_ids, user_id)
    db.commit()
    db.refresh(col)
    return _to_response(col)


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: str, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    return _to_response(_get_collection(db, user_id, collection_id))


@router.patch("/{collection_id}", response_model=CollectionResponse)
def update_collection(collection_id: str, payload: CollectionUpdate, db: Session = Depends(get_db),
                      user_id: str = Depends(get_current_user)):
    """Renombra y/o reemplaza las canciones de la colección."""
    col = _get_collection(db, user_id, collection_id)
    if payload.name is not None:
        col.name = payload.name
    if payload.song_ids is not None:
        _set_items(db, col, payload.song_ids, user_id)
    db.commit()
    db.refresh(col)
    return _to_response(col)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: str, db: Session = Depends(get_db),
                      user_id: str = Depends(get_current_user)):
    """Soft delete de mi colección personal."""
    col = _get_collection(db, user_id, collection_id)
    col.deleted_at = _utcnow()
    db.commit()
