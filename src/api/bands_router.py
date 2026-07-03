"""
Endpoints del núcleo de banda (Fase 7, T-051).

Crear banda (el creador entra como `admin`), listar "mis bandas", ver, editar y borrar
(soft delete). Cada ruta sobre una banda concreta pasa por las dependencias de aislamiento
(`require_band_member` / `require_band_admin`, T-050) → "regla de oro" multi-tenant.
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.balances import compute_balances
from ..services.band_auth import require_band_admin, require_band_member
from ..services.db import get_db
from ..services.models import (
    Band,
    BandInvite,
    BandMembership,
    Event,
    EventAttendance,
    Message,
    MusicianProfile,
    Setlist,
    Settlement,
    Song,
    SongCollection,
    Transaction,
    Venue,
    _utcnow,
)
from ..services.schemas import (
    AttendanceOut,
    BandCounts,
    BandCreate,
    BandDashboard,
    BandInviteCreate,
    BandInviteResponse,
    BandMembershipResponse,
    BandResponse,
    BandSummary,
    BandUpdate,
    EventSummary,
    MembershipRoleUpdate,
    MessageOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands", tags=["bands"])


def _active_member_counts(db: Session, band_ids: List[str]) -> dict[str, int]:
    """Nº de miembros activos por banda en UNA query agregada (evita N+1)."""
    if not band_ids:
        return {}
    rows = (
        db.query(BandMembership.band_id, func.count(BandMembership.id))
        .filter(BandMembership.band_id.in_(band_ids), BandMembership.status == "active")
        .group_by(BandMembership.band_id)
        .all()
    )
    return {bid: n for bid, n in rows}


def _song_counts(db: Session, band_ids: List[str]) -> dict[str, int]:
    """Nº de canciones (activas) por banda en UNA query agregada (evita N+1; T-132)."""
    if not band_ids:
        return {}
    rows = (
        db.query(Song.band_id, func.count(Song.id))
        .filter(Song.band_id.in_(band_ids), Song.deleted_at.is_(None))
        .group_by(Song.band_id)
        .all()
    )
    return {bid: n for bid, n in rows}


@router.post("/", response_model=BandResponse, status_code=status.HTTP_201_CREATED)
def create_band(
    payload: BandCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Crea una banda; el creador queda como `admin` (su primera membresía activa)."""
    band = Band(
        name=payload.name,
        description=payload.description,
        avatar_url=payload.avatar_url,
        created_by=user_id,
    )
    db.add(band)
    db.flush()  # asigna band.id antes de crear la membresía
    db.add(BandMembership(band_id=band.id, user_id=user_id, role="admin", status="active"))
    db.commit()
    db.refresh(band)
    return band


@router.get("/", response_model=List[BandSummary])
def list_my_bands(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """Lista las bandas donde soy miembro ACTIVO (no borradas), con mi rol y nº de miembros."""
    rows = (
        db.query(Band, BandMembership.role)
        .join(BandMembership, BandMembership.band_id == Band.id)
        .filter(
            BandMembership.user_id == user_id,
            BandMembership.status == "active",
            Band.deleted_at.is_(None),
        )
        .all()
    )
    band_ids = [b.id for b, _ in rows]
    counts = _active_member_counts(db, band_ids)
    scounts = _song_counts(db, band_ids)
    return [
        BandSummary(
            id=b.id,
            name=b.name,
            avatar_url=b.avatar_url,
            plan=b.plan,
            role=role,
            member_count=counts.get(b.id, 0),
            song_count=scounts.get(b.id, 0),
        )
        for b, role in rows
    ]


@router.get("/{band_id}", response_model=BandResponse)
def get_band(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Ver una banda (cualquier miembro activo). El aislamiento lo garantiza la dependencia."""
    return db.query(Band).filter(Band.id == band_id, Band.deleted_at.is_(None)).first()


@router.get("/{band_id}/summary", response_model=BandDashboard)
def get_band_summary(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Resumen de banda en UNA ida y vuelta (T-129), sin N+1: próximo evento (con asistencia,
    mi estado y sala), último mensaje del chat general, mi saldo y contadores. El aislamiento lo
    da `require_band_member` (un ajeno recibe 403/404 → regla de oro multi-tenant)."""
    user_id = membership.user_id
    # `now` naive (UTC) para comparar con `starts_at`, que se guarda naive desde el input.
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Próximo evento (futuro, no cancelado) con asistencia + mi estado + nombre de sala.
    ev = (
        db.query(Event)
        .filter(
            Event.band_id == band_id,
            Event.deleted_at.is_(None),
            Event.status != "cancelled",
            Event.starts_at.isnot(None),
            Event.starts_at >= now,
        )
        .order_by(Event.starts_at.asc())
        .first()
    )
    next_event = None
    if ev is not None:
        rows = (
            db.query(EventAttendance, MusicianProfile.display_name)
            .outerjoin(MusicianProfile, MusicianProfile.id == EventAttendance.user_id)
            .filter(EventAttendance.event_id == ev.id)
            .all()
        )
        next_event = EventSummary.model_validate(ev)
        next_event.attendance = [
            AttendanceOut(user_id=a.user_id, status=a.status,
                          display_name=name, responded_at=a.responded_at)
            for a, name in rows
        ]
        next_event.my_status = next((a.status for a, _ in rows if a.user_id == user_id), None)
        next_event.venue_name = (
            db.query(Venue.name).filter(Venue.id == ev.venue_id).scalar() if ev.venue_id else None
        )

    # Último mensaje del chat general (event_id IS NULL), con nombre real e is_mine.
    last = (
        db.query(Message, MusicianProfile.display_name)
        .outerjoin(MusicianProfile, MusicianProfile.id == Message.author_id)
        .filter(Message.band_id == band_id, Message.deleted_at.is_(None),
                Message.event_id.is_(None))
        .order_by(Message.created_at.desc())
        .first()
    )
    last_message = None
    if last is not None:
        m, name = last
        last_message = MessageOut.model_validate(m)
        last_message.author_name = name
        last_message.is_mine = m.author_id == user_id

    # Mi saldo en esta banda (servicio único `compute_balances`).
    members = [r[0] for r in db.query(BandMembership.user_id)
               .filter(BandMembership.band_id == band_id,
                       BandMembership.status == "active").all()]
    txs = (db.query(Transaction)
           .filter(Transaction.band_id == band_id, Transaction.deleted_at.is_(None)).all())
    settles = (db.query(Settlement)
               .filter(Settlement.band_id == band_id, Settlement.deleted_at.is_(None)).all())
    my_balance = compute_balances(txs, settles, members).get(user_id, 0)

    # Contadores (activos) de la banda.
    counts = BandCounts(
        songs=db.query(func.count(Song.id))
        .filter(Song.band_id == band_id, Song.deleted_at.is_(None)).scalar() or 0,
        setlists=db.query(func.count(Setlist.id))
        .filter(Setlist.band_id == band_id, Setlist.deleted_at.is_(None)).scalar() or 0,
        collections=db.query(func.count(SongCollection.id))
        .filter(SongCollection.band_id == band_id, SongCollection.deleted_at.is_(None)).scalar() or 0,
    )

    return BandDashboard(next_event=next_event, last_message=last_message,
                         my_balance=my_balance, counts=counts)


@router.patch("/{band_id}", response_model=BandResponse)
def update_band(
    band_id: str,
    payload: BandUpdate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Editar datos de la banda (solo admin)."""
    band = db.query(Band).filter(Band.id == band_id, Band.deleted_at.is_(None)).first()
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(band, field, value)
    db.commit()
    db.refresh(band)
    return band


@router.delete("/{band_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_band(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Borrar la banda (soft delete; solo admin). Las membresías permanecen para el histórico."""
    band = db.query(Band).filter(Band.id == band_id, Band.deleted_at.is_(None)).first()
    band.deleted_at = _utcnow()
    db.commit()


# ── Membresía (T-052): listar miembros, cambiar rol, baja blanda, reactivar ───

def _active_admin_count(db: Session, band_id: str) -> int:
    """Nº de admins ACTIVOS de la banda (para no dejarla nunca sin admin)."""
    return (
        db.query(func.count(BandMembership.id))
        .filter(
            BandMembership.band_id == band_id,
            BandMembership.status == "active",
            BandMembership.role == "admin",
        )
        .scalar()
    )


def _get_membership(db: Session, band_id: str, user_id: str) -> BandMembership:
    """Membresía concreta (cualquier estado) o 404."""
    m = (
        db.query(BandMembership)
        .filter(BandMembership.band_id == band_id, BandMembership.user_id == user_id)
        .first()
    )
    if m is None:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    return m


@router.get("/{band_id}/members", response_model=List[BandMembershipResponse])
def list_members(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Lista TODOS los miembros de la banda (incluidos los de baja, para el histórico), con su
    nombre real del perfil si lo tienen (evita mostrar UUIDs)."""
    rows = (
        db.query(BandMembership, MusicianProfile.display_name, MusicianProfile.avatar_url)
        .outerjoin(MusicianProfile, MusicianProfile.id == BandMembership.user_id)
        .filter(BandMembership.band_id == band_id)
        .all()
    )
    out = []
    for m, display_name, avatar_url in rows:
        resp = BandMembershipResponse.model_validate(m)
        resp.display_name = display_name
        resp.avatar_url = avatar_url
        resp.is_me = m.user_id == membership.user_id
        out.append(resp)
    return out


@router.patch("/{band_id}/members/{user_id}", response_model=BandMembershipResponse)
def change_member_role(
    band_id: str,
    user_id: str,
    payload: MembershipRoleUpdate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Cambiar el rol de un miembro (solo admin). No se puede degradar al último admin activo
    (la banda nunca puede quedarse sin administrador)."""
    target = _get_membership(db, band_id, user_id)
    if target.status != "active":
        raise HTTPException(status_code=400, detail="El miembro no está activo")
    if (
        target.role == "admin"
        and payload.role != "admin"
        and _active_admin_count(db, band_id) <= 1
    ):
        raise HTTPException(status_code=400, detail="La banda no puede quedarse sin admin")
    target.role = payload.role
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{band_id}/members/{user_id}", response_model=BandMembershipResponse)
def remove_member(
    band_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Dar de baja a un miembro (**baja blanda**: `status='left'` + `left_at`; la fila permanece
    para el histórico de finanzas/eventos/mensajes). No se puede dar de baja al último admin."""
    target = _get_membership(db, band_id, user_id)
    if target.status == "left":
        return target  # idempotente
    if target.role == "admin" and _active_admin_count(db, band_id) <= 1:
        raise HTTPException(status_code=400, detail="La banda no puede quedarse sin admin")
    target.status = "left"
    target.left_at = _utcnow()
    db.commit()
    db.refresh(target)
    return target


@router.post("/{band_id}/members/{user_id}/reactivate", response_model=BandMembershipResponse)
def reactivate_member(
    band_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Reactivar a un miembro dado de baja (solo admin): vuelve a `active`."""
    target = _get_membership(db, band_id, user_id)
    target.status = "active"
    target.left_at = None
    db.commit()
    db.refresh(target)
    return target


# ── Invitaciones (T-053): generar (admin) y listar las activas de la banda ────

@router.post(
    "/{band_id}/invites",
    response_model=BandInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invite(
    band_id: str,
    payload: BandInviteCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Genera una invitación con código único (solo admin). El enlace se comparte por fuera
    (WhatsApp, etc.); no depende del envío de emails."""
    invite = BandInvite(
        band_id=band_id,
        code=secrets.token_urlsafe(16),
        created_by=membership.user_id,
        role_to_grant=payload.role_to_grant,
        expires_at=payload.expires_at,
        max_uses=payload.max_uses,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("/{band_id}/invites", response_model=List[BandInviteResponse])
def list_invites(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Lista las invitaciones de la banda (solo admin)."""
    return (
        db.query(BandInvite)
        .filter(BandInvite.band_id == band_id)
        .order_by(BandInvite.created_at.desc())
        .all()
    )
