"""
Notificaciones in-app (T-V6-61) y calendario (T-V6-62).

  GET  /me/notifications             → las últimas 50 + nº sin leer
  POST /me/notifications/read-all    → marcar todas como leídas
  POST /me/notifications/{id}/read   → marcar una
  POST /me/calendar-token            → crea/rota el enlace de suscripción (webcal) de MIS eventos
  DELETE /me/calendar-token          → lo revoca
  GET  /public/calendar/{token}.ics  → feed iCalendar (sin sesión: el token es el secreto)
  GET  /bands/{id}/events/{eid}/ics  → un evento como .ics (miembros)
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.band_auth import require_band_member
from ..services.db import get_db
from ..services.models import (
    Band,
    BandMembership,
    Event,
    MusicianProfile,
    Notification,
    Venue,
    _utcnow,
)
from ..services.ratelimit import check_rate
from ..services.schemas import NotificationList, NotificationOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["notifications"])


@router.get("/me/notifications", response_model=NotificationList)
def my_notifications(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    rows = (db.query(Notification).filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc()).limit(50).all())
    unread = (db.query(Notification)
              .filter(Notification.user_id == user_id, Notification.read_at.is_(None)).count())
    return NotificationList(unread=unread, items=[NotificationOut.model_validate(n) for n in rows])


@router.post("/me/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
def read_all(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    (db.query(Notification)
     .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
     .update({Notification.read_at: _utcnow()}, synchronize_session=False))
    db.commit()


@router.post("/me/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def read_one(notification_id: str, db: Session = Depends(get_db),
             user_id: str = Depends(get_current_user)):
    n = (db.query(Notification)
         .filter(Notification.id == notification_id, Notification.user_id == user_id).first())
    if n is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    if n.read_at is None:
        n.read_at = _utcnow()
        db.commit()


# ── Calendario (.ics) ─────────────────────────────────────────────────────────
def _ics_escape(s: str) -> str:
    out = (s or "").replace("\\", "\\\\")
    for a, b in ((";", "\\;"), (",", "\\,"), ("\r\n", "\\n"), ("\n", "\\n")):
        out = out.replace(a, b)
    return out


def _fmt(dt: datetime) -> str:
    # Las fechas de la API son "hora de pared" sin zona (contrato actual, ver T-V6-18): se emiten
    # como hora LOCAL flotante (sin Z) para que el calendario las muestre tal cual.
    return dt.strftime("%Y%m%dT%H%M%S")


def _vevent(ev: Event, band_name: str, venue_name: str | None) -> List[str]:
    start = ev.starts_at
    end = ev.ends_at or (start + timedelta(hours=2))
    place = ", ".join(x for x in (venue_name, ev.address or ev.location) if x)
    kind = {"concert": "Concierto", "rehearsal": "Ensayo"}.get(ev.type, "Evento")
    lines = [
        "BEGIN:VEVENT",
        f"UID:{ev.id}@bandflow",
        f"DTSTAMP:{_utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{_fmt(start)}",
        f"DTEND:{_fmt(end)}",
        f"SUMMARY:{_ics_escape(f'{ev.title} · {band_name}')}",
        f"DESCRIPTION:{_ics_escape(kind + ' de ' + band_name)}",
    ]
    if place:
        lines.append(f"LOCATION:{_ics_escape(place)}")
    if ev.status == "cancelled":
        lines.append("STATUS:CANCELLED")
    lines.append("END:VEVENT")
    return lines


def _calendar(events, names, venues, title="BandFlow") -> str:
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BandFlow//ES", "CALSCALE:GREGORIAN",
           f"X-WR-CALNAME:{_ics_escape(title)}"]
    for ev in events:
        if ev.starts_at:
            out += _vevent(ev, names.get(ev.band_id, "Banda"), venues.get(ev.venue_id))
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"


@router.post("/me/calendar-token")
def create_calendar_token(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    p = db.get(MusicianProfile, user_id)
    if p is None:
        p = MusicianProfile(id=user_id)
        db.add(p)
    p.calendar_token = secrets.token_urlsafe(24)
    db.commit()
    return {"token": p.calendar_token, "path": f"/public/calendar/{p.calendar_token}.ics"}


@router.delete("/me/calendar-token", status_code=status.HTTP_204_NO_CONTENT)
def revoke_calendar_token(db: Session = Depends(get_db),
                          user_id: str = Depends(get_current_user)):
    p = db.get(MusicianProfile, user_id)
    if p is not None:
        p.calendar_token = None
        db.commit()


@router.get("/public/calendar/{token}.ics")
def calendar_feed(token: str, request: Request, db: Session = Depends(get_db)):
    check_rate(f"ics:{request.client.host if request.client else '-'}", 60, 60)
    p = (db.query(MusicianProfile).filter(MusicianProfile.calendar_token == token).first()
         if len(token) >= 20 else None)
    if p is None:
        raise HTTPException(status_code=404, detail="Calendario no disponible")
    band_ids = [b for (b,) in db.query(BandMembership.band_id)
                .join(Band, Band.id == BandMembership.band_id)
                .filter(BandMembership.user_id == p.id, BandMembership.status == "active",
                        Band.deleted_at.is_(None)).all()]
    since = _utcnow().replace(tzinfo=None) - timedelta(days=60)
    events = (db.query(Event).filter(Event.band_id.in_(band_ids or [""]),
                                     Event.deleted_at.is_(None), Event.starts_at >= since)
              .order_by(Event.starts_at).limit(500).all())
    names = dict(db.query(Band.id, Band.name).filter(Band.id.in_(band_ids or [""])).all())
    venues = dict(db.query(Venue.id, Venue.name).filter(
        Venue.id.in_([e.venue_id for e in events if e.venue_id] or [""])).all())
    return Response(_calendar(events, names, venues, "BandFlow · mis bandas"),
                    media_type="text/calendar; charset=utf-8")


@router.get("/bands/{band_id}/events/{event_id}/ics")
def event_ics(band_id: str, event_id: str, db: Session = Depends(get_db),
              membership: BandMembership = Depends(require_band_member)):
    ev = (db.query(Event).filter(Event.id == event_id, Event.band_id == band_id,
                                 Event.deleted_at.is_(None)).first())
    if ev is None or ev.starts_at is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado o sin fecha")
    band = db.get(Band, band_id)
    venue = db.get(Venue, ev.venue_id) if ev.venue_id else None
    body = _calendar([ev], {band_id: band.name}, {ev.venue_id: venue.name} if venue else {})
    return Response(body, media_type="text/calendar; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="evento-{ev.id[:8]}.ics"'})
