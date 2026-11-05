"""
Notificaciones in-app (T-V6-61). Un único punto para crearlas: `notify(...)` añade filas a la
sesión SIN hacer commit (lo hace el endpoint que provoca el aviso, en la misma transacción) y
nunca rompe el flujo principal: si algo falla, se registra y se sigue.
"""

import logging
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from .models import BandMembership, Notification

logger = logging.getLogger(__name__)


def band_member_ids(db: Session, band_id: str, exclude: Optional[str] = None) -> list:
    rows = (db.query(BandMembership.user_id)
            .filter(BandMembership.band_id == band_id, BandMembership.status == "active").all())
    return [u for (u,) in rows if u != exclude]


def notify(db: Session, user_ids: Iterable[str], *, kind: str, title: str,
           body: Optional[str] = None, link: Optional[str] = None,
           band_id: Optional[str] = None) -> None:
    try:
        for uid in {u for u in user_ids if u}:
            db.add(Notification(user_id=uid, kind=kind[:32], title=title[:255],
                                body=(body or None) and body[:500], link=link and link[:512],
                                band_id=band_id))
    except Exception:  # noqa: BLE001 — un aviso nunca debe tumbar la acción del usuario
        logger.exception("No se pudo crear la notificación %s", kind)
