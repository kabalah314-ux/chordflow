"""
Tests de aislamiento multi-tenant (T-050, giro V2) — la "regla de oro".

Verifican la matriz de las dependencias `require_band_member` / `require_band_admin`:
- miembro activo            → 200
- usuario ajeno             → 404 (no se revela la existencia de la banda)
- miembro no-admin en ruta admin → 403
- admin en ruta admin       → 200
- miembro dado de baja (`left`)  → 404 (pierde acceso, pero sigue en el histórico)
- banda con soft-delete     → 404

Monta una mini-app con dos rutas guardadas y controla el usuario actuante vía
`dependency_overrides` de `get_current_user`.
"""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.services import models
from src.services.auth import get_current_user
from src.services.band_auth import require_band_admin, require_band_member
from src.services.db import Base, SessionLocal, engine

pytestmark = pytest.mark.unit

ADMIN = "11111111-1111-1111-1111-111111111111"
MEMBER = "22222222-2222-2222-2222-222222222222"
LEFT = "33333333-3333-3333-3333-333333333333"
STRANGER = "99999999-9999-9999-9999-999999999999"

BAND_ID = "band-aaaa"
DELETED_BAND_ID = "band-deleted"


@pytest.fixture()
def app_and_user():
    """Mini-app con rutas guardadas + holder del usuario actuante (override de auth)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        db.add(models.Band(id=BAND_ID, name="Los Tres", created_by=ADMIN))
        db.add(models.Band(id=DELETED_BAND_ID, name="Difunta", created_by=ADMIN,
                           deleted_at=models._utcnow()))
        db.add_all([
            models.BandMembership(band_id=BAND_ID, user_id=ADMIN, role="admin", status="active"),
            models.BandMembership(band_id=BAND_ID, user_id=MEMBER, role="member", status="active"),
            models.BandMembership(band_id=BAND_ID, user_id=LEFT, role="member", status="left"),
            # miembro (activo) de la banda difunta → debe seguir dando 404 por el soft-delete
            models.BandMembership(band_id=DELETED_BAND_ID, user_id=MEMBER, role="admin",
                                  status="active"),
        ])
        db.commit()
    finally:
        db.close()

    app = FastAPI()
    holder = {"uid": STRANGER}

    @app.get("/bands/{band_id}/_member")
    def _member_route(m=Depends(require_band_member)):
        return {"role": m.role}

    @app.get("/bands/{band_id}/_admin")
    def _admin_route(m=Depends(require_band_admin)):
        return {"role": m.role}

    app.dependency_overrides[get_current_user] = lambda: holder["uid"]
    return TestClient(app), holder


def test_miembro_activo_accede(app_and_user):
    client, holder = app_and_user
    holder["uid"] = MEMBER
    r = client.get(f"/bands/{BAND_ID}/_member")
    assert r.status_code == 200
    assert r.json()["role"] == "member"


def test_ajeno_recibe_404(app_and_user):
    client, holder = app_and_user
    holder["uid"] = STRANGER
    assert client.get(f"/bands/{BAND_ID}/_member").status_code == 404


def test_no_admin_en_ruta_admin_recibe_403(app_and_user):
    client, holder = app_and_user
    holder["uid"] = MEMBER
    assert client.get(f"/bands/{BAND_ID}/_admin").status_code == 403


def test_admin_en_ruta_admin_accede(app_and_user):
    client, holder = app_and_user
    holder["uid"] = ADMIN
    r = client.get(f"/bands/{BAND_ID}/_admin")
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_ajeno_en_ruta_admin_recibe_404_no_403(app_and_user):
    """El ajeno no debe poder distinguir 'no eres admin' de 'no existe' → 404 antes que 403."""
    client, holder = app_and_user
    holder["uid"] = STRANGER
    assert client.get(f"/bands/{BAND_ID}/_admin").status_code == 404


def test_miembro_de_baja_pierde_acceso(app_and_user):
    client, holder = app_and_user
    holder["uid"] = LEFT
    assert client.get(f"/bands/{BAND_ID}/_member").status_code == 404


def test_banda_con_soft_delete_da_404(app_and_user):
    client, holder = app_and_user
    holder["uid"] = MEMBER  # es miembro activo de la banda difunta, pero está borrada
    assert client.get(f"/bands/{DELETED_BAND_ID}/_member").status_code == 404
