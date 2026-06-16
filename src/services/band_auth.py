"""
Autorización multi-tenant del giro V2 (Fase 7, T-050).

Dos dependencias FastAPI que blindan el **aislamiento entre bandas** (la mayor superficie de
riesgo del giro, §5.2 / §C.4.3 — "regla de oro"):

- `require_band_member(band_id)` → exige ser **miembro activo** de la banda; si no, **404**
  (no se revela siquiera que la banda existe a un usuario ajeno).
- `require_band_admin(band_id)`  → exige además rol **admin**; si es miembro pero no admin, **403**.

Ambas reusan `get_current_user` (que respeta el modo test) y devuelven el `BandMembership`
(con su rol) para que el endpoint lo reutilice sin volver a consultarlo. **Cada ruta de banda
debe depender de una de las dos** y tener su test de aislamiento ("ajeno → 403/404").
"""

import logging

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .auth import get_current_user
from .db import get_db
from .models import Band, BandMembership

logger = logging.getLogger(__name__)


def require_band_member(
    band_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
) -> BandMembership:
    """Devuelve la pertenencia ACTIVA del usuario en la banda, o 404.

    404 (no 403) a propósito cuando no es miembro: a un usuario ajeno no se le confirma ni
    desmiente la existencia de la banda. Un miembro dado de baja (`status='left'`) tampoco
    pasa el filtro de `active` → pierde el acceso pero su fila permanece en el histórico.
    Una banda con soft-delete (`deleted_at`) se trata como inexistente."""
    membership = (
        db.query(BandMembership)
        .join(Band, Band.id == BandMembership.band_id)
        .filter(
            BandMembership.band_id == band_id,
            BandMembership.user_id == user_id,
            BandMembership.status == "active",
            Band.deleted_at.is_(None),
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Banda no encontrada")
    return membership


def require_band_admin(
    membership: BandMembership = Depends(require_band_member),
) -> BandMembership:
    """Como `require_band_member` pero exige rol admin (403 si es miembro no-admin).

    Compone sobre `require_band_member`: FastAPI resuelve `band_id` (de la ruta) para la
    dependencia anidada, así que un ajeno sigue obteniendo 404 antes de llegar al 403."""
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Requiere rol de administrador")
    return membership
