"""
Salas reutilizables de la banda (Fase 14, T-116) — `Venue`.

`GET    /bands/{id}/venues`        → lista las salas de la banda (miembros).
`POST   /bands/{id}/venues`        → crea una sala (solo admin).
`GET    /bands/{id}/venues/{vid}`  → detalle (miembros).
`PATCH  /bands/{id}/venues/{vid}`  → editar (solo admin).
`DELETE /bands/{id}/venues/{vid}`  → soft delete (solo admin).

Las salas son infraestructura de booking (las gestiona un admin, como los eventos). Un concierto las
enlaza con `Event.venue_id`. Aislamiento por `require_band_member`/`require_band_admin` + filtro
`band_id` (regla de oro).
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.band_auth import require_band_admin, require_band_member
from ..services.db import get_db
from ..services.models import BandMembership, Venue, _utcnow
from ..services.schemas import VenueCreate, VenueResponse, VenueUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands/{band_id}/venues", tags=["venues"])


def _get_venue(db: Session, band_id: str, venue_id: str) -> Venue:
    v = (db.query(Venue)
         .filter(Venue.id == venue_id, Venue.band_id == band_id, Venue.deleted_at.is_(None))
         .first())
    if v is None:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    return v


@router.get("/", response_model=List[VenueResponse])
def list_venues(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    return (db.query(Venue)
            .filter(Venue.band_id == band_id, Venue.deleted_at.is_(None))
            .order_by(Venue.name.asc()).all())


@router.post("/", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
def create_venue(
    band_id: str,
    payload: VenueCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    v = Venue(band_id=band_id, **payload.model_dump(exclude_none=True))
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.get("/{venue_id}", response_model=VenueResponse)
def get_venue(
    band_id: str,
    venue_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    return _get_venue(db, band_id, venue_id)


@router.patch("/{venue_id}", response_model=VenueResponse)
def update_venue(
    band_id: str,
    venue_id: str,
    payload: VenueUpdate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    v = _get_venue(db, band_id, venue_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(v, field, value)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(
    band_id: str,
    venue_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    v = _get_venue(db, band_id, venue_id)
    v.deleted_at = _utcnow()
    db.commit()
