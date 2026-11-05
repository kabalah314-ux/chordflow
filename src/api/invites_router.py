"""
Aceptación de invitaciones por código (Fase 7, T-053).

`GET /invites/{code}`        → previsualiza la invitación (nombre de banda + rol + validez), para
                               que quien abre el enlace sepa a qué entra. No requiere ser miembro.
`POST /invites/{code}/accept`→ une al usuario autenticado a la banda (crea su `BandMembership`,
                               o reactiva la suya si estaba de baja) y consume un uso.

Validez de una invitación: la banda existe (no borrada), no está caducada (`expires_at`) ni agotada
(`used_count < max_uses`). Solo exige estar autenticado (te estás uniendo, aún no eres miembro).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.db import get_db
from ..services.models import (
    Band,
    BandInvite,
    BandMembership,
    Event,
    MusicianProfile,
    Song,
    _utcnow,
)
from ..services.ratelimit import check_rate
from ..services.schemas import BandMembershipResponse, InvitePreview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invites", tags=["invites"])


def _get_invite(db: Session, code: str) -> BandInvite:
    invite = db.query(BandInvite).filter(BandInvite.code == code).first()
    if invite is None:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")
    return invite


def _invalid_reason(db: Session, invite: BandInvite) -> str | None:
    """Devuelve el motivo por el que la invitación NO es válida, o None si es válida."""
    band = (
        db.query(Band)
        .filter(Band.id == invite.band_id, Band.deleted_at.is_(None))
        .first()
    )
    if band is None:
        return "banda no disponible"
    if getattr(invite, "revoked_at", None) is not None:
        return "revocada"
    if invite.expires_at is not None:
        now = _utcnow()
        exp = invite.expires_at
        if exp.tzinfo is None:  # las fechas de SQLite vuelven naive → comparar en el mismo modo
            now = now.replace(tzinfo=None)
        if exp <= now:
            return "expirada"
    if invite.max_uses is not None and invite.used_count >= invite.max_uses:
        return "agotada"
    return None


@router.get("/{code}", response_model=InvitePreview)
def preview_invite(code: str, request: Request, db: Session = Depends(get_db)):
    """Previsualiza una invitación por su código (no consume usos)."""
    # T-V6-74: límite por IP (la ruta es pública: evita barrer códigos a fuerza bruta)
    check_rate(f"invite-preview:{request.client.host if request.client else '-'}", 60, 60)
    invite = _get_invite(db, code)
    band = db.query(Band).filter(Band.id == invite.band_id).first()
    reason = _invalid_reason(db, invite)
    extra = {}
    if reason is None and band is not None:
        # T-V6-80: escaparate (solo si la invitación es válida; nada sensible).
        members = (db.query(BandMembership.user_id)
                   .filter(BandMembership.band_id == band.id, BandMembership.status == "active")
                   .all())
        ids = [m for (m,) in members]
        names = [n for (n,) in db.query(MusicianProfile.display_name)
                 .filter(MusicianProfile.id.in_(ids or [""])).all() if n][:6]
        now = _utcnow().replace(tzinfo=None)
        ev = (db.query(Event)
              .filter(Event.band_id == band.id, Event.deleted_at.is_(None),
                      Event.visibility.in_(("public", "unlisted")), Event.starts_at >= now,
                      Event.status != "cancelled")
              .order_by(Event.starts_at).first())
        extra = dict(
            avatar_url=band.avatar_url, cover_url=band.cover_url, member_count=len(ids),
            member_names=names,
            song_count=db.query(Song).filter(Song.band_id == band.id,
                                             Song.deleted_at.is_(None)).count(),
            next_public_event={"id": ev.id, "title": ev.title, "starts_at": ev.starts_at.isoformat(),
                               "type": ev.type} if ev else None,
        )
    return InvitePreview(
        band_id=invite.band_id,
        band_name=band.name if band else "(banda no disponible)",
        role_to_grant=invite.role_to_grant,
        valid=reason is None,
        reason=reason,
        **extra,
    )


@router.post("/{code}/accept", response_model=BandMembershipResponse,
             status_code=status.HTTP_201_CREATED)
def accept_invite(
    code: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Acepta la invitación: une al usuario a la banda con el rol indicado y consume un uso.

    - Si ya eres miembro **activo** → 409 (no se consume uso).
    - Si fuiste miembro y estás de **baja** → te reactiva con el rol de la invitación.
    """
    invite = _get_invite(db, code)
    reason = _invalid_reason(db, invite)
    if reason is not None:
        raise HTTPException(status_code=400, detail=f"Invitación {reason}")

    existing = (
        db.query(BandMembership)
        .filter(BandMembership.band_id == invite.band_id, BandMembership.user_id == user_id)
        .first()
    )
    if existing is not None and existing.status == "active":
        raise HTTPException(status_code=409, detail="Ya eres miembro de esta banda")

    # T-V6-08 (B-16): consumir el uso de forma ATÓMICA. Con `used_count += 1` dos aceptaciones
    # simultáneas podían superar `max_uses`; el UPDATE condicional solo afecta si queda cupo.
    cond = BandInvite.id == invite.id
    if invite.max_uses is not None:
        cond = cond & (BandInvite.used_count < invite.max_uses)
    res = db.execute(update(BandInvite).where(cond).values(used_count=BandInvite.used_count + 1))
    if res.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=410, detail="Invitación agotada")

    if existing is not None:  # estaba de baja → reactivar con el rol de la invitación
        existing.status = "active"
        existing.left_at = None
        existing.role = invite.role_to_grant
        membership = existing
    else:
        membership = BandMembership(
            band_id=invite.band_id,
            user_id=user_id,
            role=invite.role_to_grant,
            status="active",
        )
        db.add(membership)

    db.commit()
    db.refresh(membership)
    return membership
