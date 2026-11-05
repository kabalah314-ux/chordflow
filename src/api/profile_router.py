"""
Perfil del músico (Fase 7, T-054).

`GET /profile/me` → mi perfil (se crea vacío en el primer acceso: "autorelleno en primer login").
`PUT /profile/me` → crear/editar mi perfil (display_name, instruments, avatar_url).

`MusicianProfile.id` = user_id de Supabase: el perfil da el **nombre real** que se muestra en la
lista de miembros, finanzas, asistencia… en vez del UUID.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.db import get_db
from ..services.models import MusicianProfile
from ..services.schemas import MusicianProfileResponse, MusicianProfileUpsert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


def _get_or_create(db: Session, user_id: str) -> MusicianProfile:
    profile = db.query(MusicianProfile).filter(MusicianProfile.id == user_id).first()
    if profile is None:
        profile = MusicianProfile(id=user_id)
        db.add(profile)
        try:
            db.commit()
        except IntegrityError:
            # T-V6-19 (B-27): dos peticiones simultáneas en el primer login crean el mismo perfil;
            # la segunda pierde la carrera → se usa el que ya existe (antes: 500).
            db.rollback()
            return db.query(MusicianProfile).filter(MusicianProfile.id == user_id).first()
        db.refresh(profile)
    return profile


@router.get("/me", response_model=MusicianProfileResponse)
def get_my_profile(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """Mi perfil; lo crea vacío la primera vez (autorelleno en primer login)."""
    return _get_or_create(db, user_id)


@router.put("/me", response_model=MusicianProfileResponse)
def upsert_my_profile(
    payload: MusicianProfileUpsert,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Crear/editar mi perfil. Solo toca los campos enviados (parche parcial)."""
    profile = _get_or_create(db, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
