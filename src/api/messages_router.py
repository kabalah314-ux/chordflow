"""
Comunicación de la banda — mensajes (Fase 12, Área 7).

`GET    /bands/{id}/messages?event_id=` → chat general (event_id null) o hilo de un evento (miembros).
`POST   /bands/{id}/messages`           → publicar (miembros, incl. guest; opcional event_id = hilo).
`PATCH  /bands/{id}/messages/{mid}`      → editar **el propio** mensaje (marca edited_at).
`DELETE /bands/{id}/messages/{mid}`      → borrar (autor el suyo; **admin** cualquiera). Soft delete.
`PATCH  /bands/{id}/messages/{mid}/pin`  → fijar/desfijar nota (**solo admin**).

Notas = mensajes con `is_pinned=true` (aparecen arriba). Empieza simple (lista que se refresca);
el tiempo real (Supabase Realtime) se añade después sin tocar el modelo. Aislamiento por
`require_band_member` + filtro `band_id`.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.band_auth import require_band_member
from ..services.db import get_db
from ..services.models import BandMembership, Event, Message, MusicianProfile, _utcnow
from ..services.schemas import MessageCreate, MessageEdit, MessageOut, MessagePin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands/{band_id}/messages", tags=["messages"])


def _get_message(db: Session, band_id: str, message_id: str) -> Message:
    msg = (db.query(Message)
           .filter(Message.id == message_id, Message.band_id == band_id,
                   Message.deleted_at.is_(None)).first())
    if msg is None:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    return msg


def _to_out(msg: Message, user_id: str, name: Optional[str]) -> MessageOut:
    out = MessageOut.model_validate(msg)
    out.author_name = name
    out.is_mine = msg.author_id == user_id
    return out


@router.get("/", response_model=List[MessageOut])
def list_messages(
    band_id: str,
    event_id: Optional[str] = None,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Chat general (event_id omitido) o hilo de un evento. Fijados primero, luego cronológico."""
    q = (db.query(Message, MusicianProfile.display_name)
         .outerjoin(MusicianProfile, MusicianProfile.id == Message.author_id)
         .filter(Message.band_id == band_id, Message.deleted_at.is_(None)))
    q = q.filter(Message.event_id == event_id) if event_id else q.filter(Message.event_id.is_(None))
    rows = q.order_by(Message.is_pinned.desc(), Message.created_at.asc()).all()
    return [_to_out(m, membership.user_id, name) for m, name in rows]


@router.post("/", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def post_message(
    band_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Publicar un mensaje (cualquier miembro activo, incl. guest). Si `event_id`, va al hilo."""
    if payload.event_id is not None:
        ok = (db.query(Event.id)
              .filter(Event.id == payload.event_id, Event.band_id == band_id,
                      Event.deleted_at.is_(None)).first())
        if not ok:
            raise HTTPException(status_code=400, detail="El evento no es de esta banda")
    msg = Message(band_id=band_id, event_id=payload.event_id,
                  author_id=membership.user_id, body=payload.body)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    name = (db.query(MusicianProfile.display_name)
            .filter(MusicianProfile.id == membership.user_id).scalar())
    return _to_out(msg, membership.user_id, name)


@router.patch("/{message_id}", response_model=MessageOut)
def edit_message(
    band_id: str,
    message_id: str,
    payload: MessageEdit,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Editar el PROPIO mensaje (solo el autor)."""
    msg = _get_message(db, band_id, message_id)
    if msg.author_id != membership.user_id:
        raise HTTPException(status_code=403, detail="Solo puedes editar tus propios mensajes")
    msg.body = payload.body
    msg.edited_at = _utcnow()
    db.commit()
    db.refresh(msg)
    name = (db.query(MusicianProfile.display_name)
            .filter(MusicianProfile.id == msg.author_id).scalar())
    return _to_out(msg, membership.user_id, name)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    band_id: str,
    message_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Borrar (soft delete) un mensaje: el autor el suyo; un admin cualquiera."""
    msg = _get_message(db, band_id, message_id)
    if msg.author_id != membership.user_id and membership.role != "admin":
        raise HTTPException(status_code=403, detail="No puedes borrar mensajes de otros")
    msg.deleted_at = _utcnow()
    db.commit()


@router.patch("/{message_id}/pin", response_model=MessageOut)
def pin_message(
    band_id: str,
    message_id: str,
    payload: MessagePin,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Fijar/desfijar un mensaje como nota (solo admin)."""
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Solo un admin fija notas")
    msg = _get_message(db, band_id, message_id)
    msg.is_pinned = payload.is_pinned
    db.commit()
    db.refresh(msg)
    name = (db.query(MusicianProfile.display_name)
            .filter(MusicianProfile.id == msg.author_id).scalar())
    return _to_out(msg, membership.user_id, name)
