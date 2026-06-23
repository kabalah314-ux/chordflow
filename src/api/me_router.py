"""
Inicio — dashboard agregado del contexto TÚ (Fase 13, T-076).

`GET /me/dashboard` → próximos eventos + últimos mensajes de TODAS mis bandas (con etiqueta de
banda). **Aislamiento inherente** (regla de oro multi-tenant): solo se consultan las bandas donde
el usuario es miembro ACTIVO, así que un evento/mensaje de una banda ajena nunca aparece.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.balances import compute_balances
from ..services.db import get_db
from ..services.models import (
    Band,
    BandMembership,
    Event,
    EventAttendance,
    Message,
    MusicianProfile,
    Settlement,
    Transaction,
)
from ..services.schemas import (
    AttendanceOut,
    DashboardEvent,
    DashboardMessage,
    DashboardResponse,
    MyBandBalance,
    MyConversation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/me", tags=["dashboard"])

UPCOMING_LIMIT = 10
MESSAGES_LIMIT = 10


def _my_band_names(db: Session, user_id: str) -> dict:
    """Mapa band_id→nombre de MIS bandas activas (no borradas). Define el universo aislado:
    cualquier consulta agregada filtra por estas claves → una banda ajena nunca aparece."""
    return dict(
        db.query(Band.id, Band.name)
        .join(BandMembership, BandMembership.band_id == Band.id)
        .filter(
            BandMembership.user_id == user_id,
            BandMembership.status == "active",
            Band.deleted_at.is_(None),
        )
        .all()
    )


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Próximos eventos + últimos mensajes de mis bandas activas (con etiqueta de banda)."""
    # Mis bandas activas (no borradas) → mapa id→nombre. Define el universo aislado.
    my_bands = _my_band_names(db, user_id)
    if not my_bands:
        return DashboardResponse()
    band_ids = list(my_bands.keys())

    # `now` naive (UTC) para comparar con `starts_at`, que se guarda naive desde el input.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ev_rows = (
        db.query(Event)
        .filter(
            Event.band_id.in_(band_ids),
            Event.deleted_at.is_(None),
            Event.status != "cancelled",
            Event.starts_at.isnot(None),
            Event.starts_at >= now,
        )
        .order_by(Event.starts_at.asc())
        .limit(UPCOMING_LIMIT)
        .all()
    )
    my_att = (
        dict(
            db.query(EventAttendance.event_id, EventAttendance.status)
            .filter(
                EventAttendance.event_id.in_([e.id for e in ev_rows]),
                EventAttendance.user_id == user_id,
            )
            .all()
        )
        if ev_rows
        else {}
    )
    upcoming = [
        DashboardEvent(
            band_id=e.band_id, band_name=my_bands[e.band_id], id=e.id,
            title=e.title, type=e.type, starts_at=e.starts_at, my_status=my_att.get(e.id),
        )
        for e in ev_rows
    ]

    # Solo el chat general (event_id NULL), coherente con messages_router; los comentarios de
    # hilo de evento (event_id != NULL) no son "últimos mensajes" del inicio (revisión T-078).
    msg_rows = (
        db.query(Message, MusicianProfile.display_name)
        .outerjoin(MusicianProfile, MusicianProfile.id == Message.author_id)
        .filter(Message.band_id.in_(band_ids), Message.deleted_at.is_(None),
                Message.event_id.is_(None))
        .order_by(Message.created_at.desc())
        .limit(MESSAGES_LIMIT)
        .all()
    )
    recent = [
        DashboardMessage(
            band_id=m.band_id, band_name=my_bands[m.band_id], id=m.id,
            author_name=name, body=m.body, is_pinned=m.is_pinned, created_at=m.created_at,
        )
        for m, name in msg_rows
    ]
    return DashboardResponse(upcoming_events=upcoming, recent_messages=recent)


@router.get("/events", response_model=list[DashboardEvent])
def list_my_events(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Agenda agregada (T-078): TODOS los eventos (próximos y pasados) de mis bandas, con
    etiqueta de banda y mi asistencia. El front separa próximos/pasados y filtra por banda.
    Aislamiento inherente: solo bandas donde soy miembro activo."""
    my_bands = _my_band_names(db, user_id)
    if not my_bands:
        return []
    band_ids = list(my_bands.keys())

    rows = (
        db.query(Event)
        .filter(
            Event.band_id.in_(band_ids),
            Event.deleted_at.is_(None),
            Event.status != "cancelled",
        )
        .order_by(Event.starts_at.asc().nullslast())
        .all()
    )
    my_att = (
        dict(
            db.query(EventAttendance.event_id, EventAttendance.status)
            .filter(
                EventAttendance.event_id.in_([e.id for e in rows]),
                EventAttendance.user_id == user_id,
            )
            .all()
        )
        if rows
        else {}
    )
    # Asistencia de TODOS por evento (con nombre real) en UNA query agregada (sin N+1), para mostrar
    # los confirmados en la agenda agregada igual que en la de cada banda (cola #4).
    by_event: dict[str, list[AttendanceOut]] = {}
    if rows:
        att_rows = (
            db.query(EventAttendance, MusicianProfile.display_name)
            .outerjoin(MusicianProfile, MusicianProfile.id == EventAttendance.user_id)
            .filter(EventAttendance.event_id.in_([e.id for e in rows]))
            .all()
        )
        for att, display_name in att_rows:
            by_event.setdefault(att.event_id, []).append(
                AttendanceOut(user_id=att.user_id, status=att.status,
                              display_name=display_name, responded_at=att.responded_at)
            )
    return [
        DashboardEvent(
            band_id=e.band_id, band_name=my_bands[e.band_id], id=e.id,
            title=e.title, type=e.type, starts_at=e.starts_at, my_status=my_att.get(e.id),
            attendance=by_event.get(e.id, []),
        )
        for e in rows
    ]


@router.get("/balances", response_model=list[MyBandBalance])
def list_my_balances(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Mi saldo neto en cada una de mis bandas (T-079). Reusa el servicio único `compute_balances`.
    Aislamiento inherente: solo mis bandas activas. Una banda ajena nunca aparece."""
    my_bands = _my_band_names(db, user_id)
    if not my_bands:
        return []
    out = []
    for bid, bname in my_bands.items():
        members = [r[0] for r in db.query(BandMembership.user_id)
                   .filter(BandMembership.band_id == bid,
                           BandMembership.status == "active").all()]
        txs = (db.query(Transaction)
               .filter(Transaction.band_id == bid, Transaction.deleted_at.is_(None)).all())
        settles = (db.query(Settlement)
                   .filter(Settlement.band_id == bid, Settlement.deleted_at.is_(None)).all())
        balances = compute_balances(txs, settles, members)
        out.append(MyBandBalance(band_id=bid, band_name=bname, balance=balances.get(user_id, 0)))
    out.sort(key=lambda b: b.band_name)
    return out


@router.get("/conversations", response_model=list[MyConversation])
def list_my_conversations(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Una conversación por banda (chat general), con su último mensaje (T-080). Aislado: solo mis
    bandas activas. Entrar abre el chat de esa banda en band.html. Bandas con mensajes primero
    (más reciente arriba); las que no tienen, por nombre."""
    my_bands = _my_band_names(db, user_id)
    if not my_bands:
        return []
    out = []
    for bid, bname in my_bands.items():
        last = (
            db.query(Message, MusicianProfile.display_name)
            .outerjoin(MusicianProfile, MusicianProfile.id == Message.author_id)
            .filter(Message.band_id == bid, Message.deleted_at.is_(None),
                    Message.event_id.is_(None))
            .order_by(Message.created_at.desc())
            .first()
        )
        if last:
            m, name = last
            out.append(MyConversation(band_id=bid, band_name=bname,
                                      last_body=m.body, last_author=name, last_at=m.created_at))
        else:
            out.append(MyConversation(band_id=bid, band_name=bname))
    with_msg = sorted([c for c in out if c.last_at], key=lambda c: c.last_at, reverse=True)
    without = sorted([c for c in out if not c.last_at], key=lambda c: c.band_name)
    return with_msg + without
