"""
Agenda de la banda — eventos + asistencia (Fase 10, Áreas 2/3).

`GET    /bands/{id}/events`               → lista la agenda (miembros), con mi asistencia.
`POST   /bands/{id}/events`               → crear evento (**solo admin**).
`GET    /bands/{id}/events/{eid}`         → detalle con la asistencia de todos (miembros).
`PATCH  /bands/{id}/events/{eid}`         → editar (**solo admin**).
`DELETE /bands/{id}/events/{eid}`         → borrar (soft delete, **solo admin**).
`PUT    /bands/{id}/events/{eid}/attendance` → marcar mi asistencia voy/no voy/quizás (miembros).

Decisión §2.8: crear/editar/borrar eventos es solo de admins; los miembros ven, confirman y comentan.
Aislamiento por `require_band_member`/`require_band_admin` + filtro `band_id`.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.band_auth import require_band_admin, require_band_member
from ..services.db import get_db
from ..services.models import (
    BandMembership,
    Event,
    EventAttendance,
    MusicianProfile,
    Setlist,
    Venue,
    _utcnow,
)
from ..services.schemas import (
    AttendanceOut,
    AttendanceSet,
    EventCreate,
    EventResponse,
    EventSummary,
    EventUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands/{band_id}/events", tags=["events"])


def _get_event(db: Session, band_id: str, event_id: str) -> Event:
    ev = (db.query(Event)
          .filter(Event.id == event_id, Event.band_id == band_id, Event.deleted_at.is_(None))
          .first())
    if ev is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return ev


def _validate_setlist(db: Session, band_id: str, setlist_id: Optional[str], event_type: str) -> None:
    """El setlist solo se adjunta a conciertos y debe ser de ESTA banda (§C.4.1 #5)."""
    if setlist_id is None:
        return
    if event_type != "concert":
        raise HTTPException(status_code=400, detail="El setlist solo se adjunta a conciertos")
    ok = (db.query(Setlist.id)
          .filter(Setlist.id == setlist_id, Setlist.band_id == band_id,
                  Setlist.deleted_at.is_(None)).first())
    if not ok:
        raise HTTPException(status_code=400, detail="El setlist no es de esta banda")


def _validate_venue(db: Session, band_id: str, venue_id: Optional[str], event_type: str) -> None:
    """La sala solo se adjunta a conciertos y debe ser de ESTA banda (T-116)."""
    if venue_id is None:
        return
    if event_type != "concert":
        raise HTTPException(status_code=400, detail="La sala solo se adjunta a conciertos")
    ok = (db.query(Venue.id)
          .filter(Venue.id == venue_id, Venue.band_id == band_id,
                  Venue.deleted_at.is_(None)).first())
    if not ok:
        raise HTTPException(status_code=400, detail="La sala no es de esta banda")


def _my_status(db: Session, event_id: str, user_id: str) -> Optional[str]:
    row = (db.query(EventAttendance.status)
           .filter(EventAttendance.event_id == event_id, EventAttendance.user_id == user_id)
           .first())
    return row[0] if row else None


@router.get("/", response_model=List[EventSummary])
def list_events(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Agenda completa de la banda (ascendente por fecha), con mi asistencia en cada evento.
    El front separa próximos/pasados."""
    events = (db.query(Event)
              .filter(Event.band_id == band_id, Event.deleted_at.is_(None))
              .order_by(Event.starts_at.asc().nullslast()).all())
    if not events:
        return []
    event_ids = [e.id for e in events]
    mine = dict(
        db.query(EventAttendance.event_id, EventAttendance.status)
        .filter(EventAttendance.event_id.in_(event_ids),
                EventAttendance.user_id == membership.user_id).all()
    )
    # Asistencia de TODOS por evento (con nombre real), en UNA query agregada (sin N+1) → el front
    # muestra una línea discreta de "quién ha confirmado" en cada evento.
    by_event: dict[str, list[AttendanceOut]] = {}
    rows = (db.query(EventAttendance, MusicianProfile.display_name)
            .outerjoin(MusicianProfile, MusicianProfile.id == EventAttendance.user_id)
            .filter(EventAttendance.event_id.in_(event_ids)).all())
    for att, display_name in rows:
        by_event.setdefault(att.event_id, []).append(
            AttendanceOut(user_id=att.user_id, status=att.status,
                          display_name=display_name, responded_at=att.responded_at))
    # Nombre de la sala por evento (denormalizado, UNA query) → la agenda lo muestra en el concierto.
    venue_ids = [e.venue_id for e in events if e.venue_id]
    venue_names = (dict(db.query(Venue.id, Venue.name).filter(Venue.id.in_(venue_ids)).all())
                   if venue_ids else {})
    out = []
    for e in events:
        s = EventSummary.model_validate(e)
        s.my_status = mine.get(e.id)
        s.attendance = by_event.get(e.id, [])
        s.venue_name = venue_names.get(e.venue_id) if e.venue_id else None
        out.append(s)
    return out


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    band_id: str,
    payload: EventCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Crear un evento (solo admin)."""
    _validate_setlist(db, band_id, payload.setlist_id, payload.type)
    _validate_venue(db, band_id, payload.venue_id, payload.type)
    # exclude_none: los campos no enviados (incl. status) usan el default del modelo ('confirmed').
    ev = Event(band_id=band_id, created_by=membership.user_id,
               **payload.model_dump(exclude_none=True))
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return _to_event_response(db, ev, membership.user_id)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    band_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Detalle del evento con la asistencia de todos los miembros (nombre real)."""
    ev = _get_event(db, band_id, event_id)
    return _to_event_response(db, ev, membership.user_id)


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(
    band_id: str,
    event_id: str,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Editar un evento (solo admin)."""
    ev = _get_event(db, band_id, event_id)
    data = payload.model_dump(exclude_unset=True)
    # Validar setlist/sala contra el tipo resultante (el del payload o el actual).
    if "setlist_id" in data or "type" in data:
        _validate_setlist(db, band_id, data.get("setlist_id", ev.setlist_id),
                          data.get("type", ev.type))
    if "venue_id" in data or "type" in data:
        _validate_venue(db, band_id, data.get("venue_id", ev.venue_id),
                        data.get("type", ev.type))
    for field, value in data.items():
        setattr(ev, field, value)
    db.commit()
    db.refresh(ev)
    return _to_event_response(db, ev, membership.user_id)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    band_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Borrar un evento (soft delete, solo admin)."""
    ev = _get_event(db, band_id, event_id)
    ev.deleted_at = _utcnow()
    db.commit()


@router.put("/{event_id}/attendance", response_model=EventResponse)
def set_attendance(
    band_id: str,
    event_id: str,
    payload: AttendanceSet,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Marcar mi asistencia (voy / no voy / quizás). Cualquier miembro activo, incluido guest."""
    ev = _get_event(db, band_id, event_id)
    att = (db.query(EventAttendance)
           .filter(EventAttendance.event_id == ev.id,
                   EventAttendance.user_id == membership.user_id).first())
    if att is None:
        att = EventAttendance(event_id=ev.id, user_id=membership.user_id, status=payload.status)
        db.add(att)
    else:
        att.status = payload.status
        att.responded_at = _utcnow()
    db.commit()
    db.refresh(ev)
    return _to_event_response(db, ev, membership.user_id)


def _to_event_response(db: Session, ev: Event, user_id: str) -> EventResponse:
    """Arma la respuesta con la lista de asistencia (nombre real) y mi estado."""
    rows = (db.query(EventAttendance, MusicianProfile.display_name)
            .outerjoin(MusicianProfile, MusicianProfile.id == EventAttendance.user_id)
            .filter(EventAttendance.event_id == ev.id).all())
    attendance = []
    my_status = None
    for att, display_name in rows:
        attendance.append(AttendanceOut(user_id=att.user_id, status=att.status,
                                        display_name=display_name, responded_at=att.responded_at))
        if att.user_id == user_id:
            my_status = att.status
    resp = EventResponse.model_validate(ev)
    resp.attendance = attendance
    resp.my_status = my_status
    if ev.venue_id:
        resp.venue_name = db.query(Venue.name).filter(Venue.id == ev.venue_id).scalar()
    return resp
