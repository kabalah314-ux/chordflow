"""
Cuenta (T-V6-65, T-V6-42e): exportar mis datos, salir de una banda (con traspaso de admin) y
borrar mi cuenta en BandFlow.

- `GET  /me/export`             → JSON con mi perfil, mis canciones/setlists personales, mis bandas
                                   y mis perfiles de la red (derecho de acceso/portabilidad).
- `POST /bands/{id}/leave`      → salgo de la banda (baja blanda). Si soy el último admin y quedan
                                   miembros, hay que indicar a quién paso el admin (`transfer_to`).
- `POST /me/delete-account`     → borra mis datos personales y me saca de mis bandas (traspasando
                                   el admin al miembro más antiguo; si estaba solo, la banda se
                                   borra). La cuenta de acceso (Supabase Auth) la elimina Oscar
                                   desde el panel: la API no tiene (ni debe tener) la service key.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.band_auth import require_band_member
from ..services.db import get_db
from ..services.models import (
    Band,
    BandMembership,
    GigCall,
    MusicianProfile,
    Notification,
    ProProfile,
    Setlist,
    Song,
    _utcnow,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["account"])


class LeaveIn(BaseModel):
    transfer_to: Optional[str] = Field(None, max_length=36)


class DeleteAccountIn(BaseModel):
    confirm: str = Field(max_length=20)


def _song_dict(s: Song) -> dict:
    return {
        "title": s.title, "artist": s.artist, "bpm": s.bpm, "key": s.key_root, "capo": s.capo,
        "reference_url": s.reference_url, "created_at": s.created_at.isoformat() if s.created_at else None,
        "sections": [{"name": sec.name, "lines": [
            {"type": ln.type, "content": ln.content,
             "chords": [{"chord": c.chord_name, "position": c.char_position} for c in ln.chords]}
            for ln in sec.lines]} for sec in s.sections],
    }


@router.get("/me/export")
def export_my_data(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    p = db.get(MusicianProfile, user_id)
    songs = db.query(Song).filter(Song.owner_id == user_id, Song.band_id.is_(None),
                                  Song.deleted_at.is_(None)).all()
    sls = db.query(Setlist).filter(Setlist.owner_id == user_id, Setlist.band_id.is_(None),
                                   Setlist.deleted_at.is_(None)).all()
    bands = (db.query(Band.name, BandMembership.role, BandMembership.joined_at)
             .join(BandMembership, BandMembership.band_id == Band.id)
             .filter(BandMembership.user_id == user_id).all())
    pros = db.query(ProProfile).filter(ProProfile.user_id == user_id,
                                       ProProfile.deleted_at.is_(None)).all()
    return {
        "exported_at": _utcnow().isoformat(),
        "profile": {"display_name": p.display_name if p else None,
                    "instruments": p.instruments if p else None},
        "songs": [_song_dict(s) for s in songs],
        "setlists": [{"name": sl.name, "songs": [it.song.title for it in sl.items if it.song]}
                     for sl in sls],
        "bands": [{"name": n, "role": r, "joined_at": j.isoformat() if j else None}
                  for n, r, j in bands],
        "network_profiles": [{"kind": x.kind, "name": x.name, "zone": x.zone, "bio": x.bio}
                             for x in pros],
    }


def _others(db: Session, band_id: str, user_id: str):
    return (db.query(BandMembership)
            .filter(BandMembership.band_id == band_id, BandMembership.status == "active",
                    BandMembership.user_id != user_id)
            .order_by(BandMembership.joined_at).all())


def _leave(db: Session, m: BandMembership, transfer_to: Optional[str], auto: bool) -> None:
    others = _others(db, m.band_id, m.user_id)
    if m.role == "admin" and not any(o.role == "admin" for o in others):
        if not others:
            band = db.get(Band, m.band_id)
            if band is not None and band.deleted_at is None:
                band.deleted_at = _utcnow()   # me quedaba solo: la banda se archiva
        else:
            heir = next((o for o in others if o.user_id == transfer_to), None)
            if heir is None and auto:
                heir = others[0]   # el miembro más antiguo
            if heir is None:
                raise HTTPException(status_code=400,
                                    detail="Eres el único admin: elige a quién pasar el admin")
            heir.role = "admin"
    m.status = "left"
    m.left_at = _utcnow()


@router.post("/bands/{band_id}/leave")
def leave_band(band_id: str, payload: LeaveIn, db: Session = Depends(get_db),
               membership: BandMembership = Depends(require_band_member)):
    _leave(db, membership, payload.transfer_to, auto=False)
    db.commit()
    return {"ok": True}


@router.post("/me/delete-account")
def delete_account(payload: DeleteAccountIn, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    if payload.confirm.strip().upper() != "BORRAR":
        raise HTTPException(status_code=400, detail="Escribe BORRAR para confirmar")
    now = _utcnow()
    for m in db.query(BandMembership).filter(BandMembership.user_id == user_id,
                                             BandMembership.status == "active").all():
        _leave(db, m, None, auto=True)
    for s in db.query(Song).filter(Song.owner_id == user_id, Song.band_id.is_(None),
                                   Song.deleted_at.is_(None)):
        s.deleted_at = now
    for sl in db.query(Setlist).filter(Setlist.owner_id == user_id, Setlist.band_id.is_(None),
                                       Setlist.deleted_at.is_(None)):
        sl.deleted_at = now
    for p in db.query(ProProfile).filter(ProProfile.user_id == user_id,
                                         ProProfile.deleted_at.is_(None)):
        p.deleted_at = now
        p.phone = None
        for c in db.query(GigCall).filter(GigCall.pro_profile_id == p.id):
            c.status = "closed"
    prof = db.get(MusicianProfile, user_id)
    if prof is not None:
        prof.display_name = "Usuario eliminado"
        prof.avatar_url = None
        prof.instruments = None
        prof.calendar_token = None
    db.query(Notification).filter(Notification.user_id == user_id).delete(
        synchronize_session=False)
    db.commit()
    logger.warning("Cuenta %s: datos borrados a petición del usuario (falta borrar en Auth)",
                   user_id)
    return {"ok": True}
