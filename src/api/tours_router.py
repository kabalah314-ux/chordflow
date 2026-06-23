"""
Giras de la banda (V3-F5, §4 de GUIA_MAESTRA_V3.md).

Una gira agrupa varios conciertos (paradas) en una ruta + un presupuesto estimado. NO duplica
Agenda ni Finanzas: las **agrega**. Cada parada puede ligarse a un `Event(concert)` ya existente
de la banda; el gasto real sigue yendo a `Transaction` (Finanzas) — aquí solo va la **estimación**.

`GET    /bands/{id}/tours`                      → lista de giras (miembros).
`POST   /bands/{id}/tours`                      → crear gira (**solo admin**).
`GET    /bands/{id}/tours/{tid}`                → detalle con paradas + presupuesto (miembros).
`PATCH  /bands/{id}/tours/{tid}`                → editar (**solo admin**).
`DELETE /bands/{id}/tours/{tid}`                → borrar (soft delete, **solo admin**).
`POST   /bands/{id}/tours/{tid}/stops`         → añadir parada (**solo admin**).
`DELETE /bands/{id}/tours/{tid}/stops/{sid}`   → quitar parada (**solo admin**).
`POST   /bands/{id}/tours/{tid}/budget`        → añadir línea de presupuesto (**solo admin**).
`DELETE /bands/{id}/tours/{tid}/budget/{lid}`  → quitar línea (**solo admin**).

Aislamiento (regla de oro): `require_band_member`/`require_band_admin` + filtro `band_id`.
"""

import logging
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..services.band_auth import require_band_admin, require_band_member
from ..services.db import get_db
from ..services.models import (
    BandMembership,
    Event,
    Tour,
    TourBudgetLine,
    TourStop,
    _utcnow,
)
from ..services.schemas import (
    TourBudgetLineCreate,
    TourCreate,
    TourResponse,
    TourStopCreate,
    TourSummary,
    TourUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands/{band_id}/tours", tags=["tours"])


def _get_tour(db: Session, band_id: str, tour_id: str) -> Tour:
    t = (db.query(Tour)
         .filter(Tour.id == tour_id, Tour.band_id == band_id, Tour.deleted_at.is_(None))
         .first())
    if t is None:
        raise HTTPException(status_code=404, detail="Gira no encontrada")
    return t


def _total_budget(tour: Tour) -> Decimal:
    return sum((ln.estimated_amount for ln in tour.budget_lines), Decimal("0.00"))


def _to_response(db: Session, tour: Tour) -> TourResponse:
    """Detalle con paradas enriquecidas (título/fecha del evento ligado) y el presupuesto total."""
    resp = TourResponse.model_validate(tour)
    # Enriquecer cada parada con los datos del evento ligado (si lo hay), sin otra llamada.
    ev_ids = [s.event_id for s in tour.stops if s.event_id]
    titles = {}
    total_fee = Decimal("0.00")
    if ev_ids:
        for ev in (db.query(Event)
                   .filter(Event.id.in_(ev_ids), Event.deleted_at.is_(None)).all()):
            titles[ev.id] = (ev.title, ev.starts_at)
            if ev.fee is not None:
                total_fee += ev.fee
    for stop_resp, stop in zip(resp.stops, tour.stops):
        if stop.event_id in titles:
            stop_resp.event_title, stop_resp.event_starts_at = titles[stop.event_id]
    resp.total_budget = _total_budget(tour)
    resp.total_fee = total_fee
    return resp


@router.get("/", response_model=List[TourSummary])
def list_tours(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Giras de la banda (más recientes primero por fecha de inicio)."""
    tours = (db.query(Tour)
             .filter(Tour.band_id == band_id, Tour.deleted_at.is_(None))
             .order_by(Tour.start_date.desc().nullslast(), Tour.created_at.desc()).all())
    # Caché por gira (Σ del fee de los conciertos ligados) en UNA query agregada (sin N+1).
    fee_by_tour = {}
    tour_ids = [t.id for t in tours]
    if tour_ids:
        rows = (db.query(TourStop.tour_id, func.sum(Event.fee))
                .join(Event, Event.id == TourStop.event_id)
                .filter(TourStop.tour_id.in_(tour_ids), Event.deleted_at.is_(None))
                .group_by(TourStop.tour_id).all())
        fee_by_tour = {tid: (amt or Decimal("0.00")) for tid, amt in rows}
    out = []
    for t in tours:
        s = TourSummary.model_validate(t)
        s.stop_count = len(t.stops)
        s.total_budget = _total_budget(t)
        s.total_fee = fee_by_tour.get(t.id, Decimal("0.00"))
        out.append(s)
    return out


@router.post("/", response_model=TourResponse, status_code=status.HTTP_201_CREATED)
def create_tour(
    band_id: str,
    payload: TourCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Crear una gira (solo admin)."""
    t = Tour(band_id=band_id, created_by=membership.user_id, **payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return _to_response(db, t)


@router.get("/{tour_id}", response_model=TourResponse)
def get_tour(
    band_id: str,
    tour_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Detalle de la gira: paradas (ruta) + presupuesto."""
    return _to_response(db, _get_tour(db, band_id, tour_id))


@router.patch("/{tour_id}", response_model=TourResponse)
def update_tour(
    band_id: str,
    tour_id: str,
    payload: TourUpdate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Editar una gira (solo admin)."""
    t = _get_tour(db, band_id, tour_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return _to_response(db, t)


@router.delete("/{tour_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tour(
    band_id: str,
    tour_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Borrar una gira (soft delete, solo admin)."""
    t = _get_tour(db, band_id, tour_id)
    t.deleted_at = _utcnow()
    db.commit()


@router.post("/{tour_id}/stops", response_model=TourResponse, status_code=status.HTTP_201_CREATED)
def add_stop(
    band_id: str,
    tour_id: str,
    payload: TourStopCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Añadir una parada a la ruta (solo admin). Si se liga a un evento, debe ser de ESTA banda."""
    t = _get_tour(db, band_id, tour_id)
    if payload.event_id is not None:
        ok = (db.query(Event.id)
              .filter(Event.id == payload.event_id, Event.band_id == band_id,
                      Event.deleted_at.is_(None)).first())
        if not ok:
            raise HTTPException(status_code=400, detail="El evento no es de esta banda")
    next_pos = (max((s.position for s in t.stops), default=-1)) + 1
    stop = TourStop(tour_id=t.id, position=next_pos, **payload.model_dump())
    db.add(stop)
    db.commit()
    db.refresh(t)
    return _to_response(db, t)


@router.delete("/{tour_id}/stops/{stop_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_stop(
    band_id: str,
    tour_id: str,
    stop_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Quitar una parada (solo admin)."""
    t = _get_tour(db, band_id, tour_id)
    stop = db.query(TourStop).filter(TourStop.id == stop_id, TourStop.tour_id == t.id).first()
    if stop is None:
        raise HTTPException(status_code=404, detail="Parada no encontrada")
    db.delete(stop)
    db.commit()


@router.post("/{tour_id}/budget", response_model=TourResponse, status_code=status.HTTP_201_CREATED)
def add_budget_line(
    band_id: str,
    tour_id: str,
    payload: TourBudgetLineCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Añadir una línea de presupuesto estimado (solo admin)."""
    t = _get_tour(db, band_id, tour_id)
    line = TourBudgetLine(tour_id=t.id, **payload.model_dump())
    db.add(line)
    db.commit()
    db.refresh(t)
    return _to_response(db, t)


@router.delete("/{tour_id}/budget/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_budget_line(
    band_id: str,
    tour_id: str,
    line_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Quitar una línea de presupuesto (solo admin)."""
    t = _get_tour(db, band_id, tour_id)
    line = (db.query(TourBudgetLine)
            .filter(TourBudgetLine.id == line_id, TourBudgetLine.tour_id == t.id).first())
    if line is None:
        raise HTTPException(status_code=404, detail="Línea de presupuesto no encontrada")
    db.delete(line)
    db.commit()
