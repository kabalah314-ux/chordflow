"""
Setlists de banda (Fase 9, T-061) — `Setlist.band_id`.

`GET    /bands/{id}/setlists`        → lista los setlists de la banda (miembros).
`POST   /bands/{id}/setlists`        → crea un setlist sacado del REPERTORIO de la banda (no guest).
`GET    /bands/{id}/setlists/{sid}`  → detalle (miembros).
`PATCH  /bands/{id}/setlists/{sid}`  → renombrar / reordenar / añadir-quitar (no guest).
`DELETE /bands/{id}/setlists/{sid}`  → soft delete (no guest).

Las canciones de un setlist de banda solo pueden ser del **repertorio de esa banda** (Song.band_id ==
band). El reproductor reusa `/setlists/{id}`, que ya autoriza a los miembros. Aislamiento por
`require_band_member` + filtro `band_id`.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.band_auth import require_band_member
from ..services.db import get_db
from ..services.models import BandMembership, Setlist, SetlistItem, Song, _utcnow
from ..services.schemas import SetlistCreate, SetlistResponse, SetlistSummary, SetlistUpdate
from .setlists_router import _to_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands/{band_id}/setlists", tags=["band-setlists"])


def _deny_guests(membership: BandMembership) -> None:
    if membership.role == "guest":
        raise HTTPException(status_code=403, detail="Un invitado no puede editar los setlists")


def _valid_band_song_ids(db: Session, band_id: str, song_ids: List[str]) -> List[str]:
    """Filtra `song_ids` dejando solo los del REPERTORIO de la banda (no borrados), en orden."""
    if not song_ids:
        return []
    rows = (db.query(Song.id)
            .filter(Song.band_id == band_id, Song.deleted_at.is_(None), Song.id.in_(song_ids))
            .all())
    en_repertorio = {r[0] for r in rows}
    return [sid for sid in song_ids if sid in en_repertorio]


def _set_band_items(db: Session, sl: Setlist, song_ids: List[str], band_id: str) -> None:
    for it in list(sl.items):
        db.delete(it)
    db.flush()
    for pos, sid in enumerate(_valid_band_song_ids(db, band_id, song_ids)):
        sl.items.append(SetlistItem(song_id=sid, position=pos))


def _get_band_setlist(db: Session, band_id: str, setlist_id: str) -> Setlist:
    sl = (db.query(Setlist)
          .filter(Setlist.id == setlist_id, Setlist.band_id == band_id,
                  Setlist.deleted_at.is_(None)).first())
    if sl is None:
        raise HTTPException(status_code=404, detail="Setlist no encontrado")
    return sl


@router.get("/", response_model=List[SetlistSummary])
def list_band_setlists(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    setlists = (db.query(Setlist)
                .filter(Setlist.band_id == band_id, Setlist.deleted_at.is_(None))
                .order_by(Setlist.updated_at.desc()).all())
    return [SetlistSummary(id=s.id, name=s.name, band_id=s.band_id,
                           updated_at=s.updated_at, song_count=len(s.items)) for s in setlists]


@router.post("/", response_model=SetlistResponse, status_code=status.HTTP_201_CREATED)
def create_band_setlist(
    band_id: str,
    payload: SetlistCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Crea un setlist de banda; sus canciones se sacan del repertorio de la banda."""
    _deny_guests(membership)
    sl = Setlist(name=payload.name, owner_id=membership.user_id, band_id=band_id)
    db.add(sl)
    _set_band_items(db, sl, payload.song_ids, band_id)
    db.commit()
    db.refresh(sl)
    return _to_response(sl)


@router.get("/{setlist_id}", response_model=SetlistResponse)
def get_band_setlist(
    band_id: str,
    setlist_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    return _to_response(_get_band_setlist(db, band_id, setlist_id))


@router.patch("/{setlist_id}", response_model=SetlistResponse)
def update_band_setlist(
    band_id: str,
    setlist_id: str,
    payload: SetlistUpdate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    _deny_guests(membership)
    sl = _get_band_setlist(db, band_id, setlist_id)
    if payload.name is not None:
        sl.name = payload.name
    if payload.song_ids is not None:
        _set_band_items(db, sl, payload.song_ids, band_id)
    db.commit()
    db.refresh(sl)
    return _to_response(sl)


@router.delete("/{setlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_band_setlist(
    band_id: str,
    setlist_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    _deny_guests(membership)
    sl = _get_band_setlist(db, band_id, setlist_id)
    sl.deleted_at = _utcnow()
    db.commit()
