"""
Plano público (V3-F7, D1) — rutas SIN auth que sirven SOLO filas con `visibility` unlisted/public,
con proyección SEGURA. Separadas de las rutas privadas (que no cambian). Regla de oro pública:
una fila privada jamás aparece aquí (su propio test de aislamiento, distinto del de banda).

`GET /public/events/{event_id}` → proyección pública de un evento compartido por enlace (unlisted).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.db import get_db
from ..services.models import Band, Event, Venue
from ..services.schemas import PublicEventResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["public"])

# Visibilidades que un enlace público puede servir. `private` NUNCA se sirve aquí.
_SHAREABLE = ("unlisted", "public")


@router.get("/events/{event_id}", response_model=PublicEventResponse)
def public_event(event_id: str, db: Session = Depends(get_db)):
    """Evento compartido por enlace (sin login). 404 si no existe, está borrado, es privado o su
    banda fue borrada. Devuelve SOLO datos no sensibles — nunca caché (`fee`), contacto, notas,
    setlist, asistencia ni `band_id`."""
    ev = (
        db.query(Event)
        .filter(
            Event.id == event_id,
            Event.deleted_at.is_(None),
            Event.visibility.in_(_SHAREABLE),
        )
        .first()
    )
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no disponible")

    band = db.query(Band).filter(Band.id == ev.band_id, Band.deleted_at.is_(None)).first()
    if band is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no disponible")

    venue = db.query(Venue).filter(Venue.id == ev.venue_id).first() if ev.venue_id else None

    return PublicEventResponse(
        id=ev.id,
        type=ev.type,
        title=ev.title,
        starts_at=ev.starts_at,
        ends_at=ev.ends_at,
        band_name=band.name,
        venue_name=venue.name if venue else None,
        city=venue.city if venue else None,
        location=ev.location,
    )


@router.get("/events/{event_id}/ics")
def public_event_ics(event_id: str, db: Session = Depends(get_db)):
    """T-V6-52: el evento compartido como .ics ("Añadir a mi calendario") — misma proyección."""
    from fastapi import Response

    from .notifications_router import _calendar

    ev = (db.query(Event).filter(Event.id == event_id, Event.deleted_at.is_(None),
                                 Event.visibility.in_(_SHAREABLE)).first())
    band = (db.query(Band).filter(Band.id == ev.band_id, Band.deleted_at.is_(None)).first()
            if ev else None)
    if ev is None or band is None or ev.starts_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no disponible")
    venue = db.query(Venue).filter(Venue.id == ev.venue_id).first() if ev.venue_id else None
    # Proyección pública: sin dirección privada de la hoja del bolo (solo sala/lugar).
    ev_pub = Event(id=ev.id, band_id=ev.band_id, type=ev.type, title=ev.title,
                   starts_at=ev.starts_at, ends_at=ev.ends_at, location=ev.location,
                   status=ev.status, venue_id=ev.venue_id)
    body = _calendar([ev_pub], {band.id: band.name}, {ev.venue_id: venue.name} if venue else {})
    return Response(body, media_type="text/calendar; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="evento.ics"'})
