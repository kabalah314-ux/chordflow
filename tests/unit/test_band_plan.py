"""
Andamiaje de planes SaaS de la banda (V3-F3, T-097). Sin cobro: solo el campo `Band.plan`
('free' por defecto), que un admin puede cambiar a 'pro'. Prepara la monetización futura sin
hacer retrofit en cada fase.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership

pytestmark = pytest.mark.unit

MEMBER = "22222222-2222-2222-2222-222222222222"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_plan_default_free_y_admin_lo_cambia(client):
    bid = client.post("/bands/", json={"name": "Banda Plan"}).json()["id"]
    assert client.get(f"/bands/{bid}").json()["plan"] == "free"

    r = client.patch(f"/bands/{bid}", json={"plan": "pro"})
    assert r.status_code == 200 and r.json()["plan"] == "pro"

    # También se refleja en "mis bandas"
    assert any(b["id"] == bid and b["plan"] == "pro" for b in client.get("/bands/").json())

    # Valor inválido → 422 (lo valida el Literal BandPlan)
    assert client.patch(f"/bands/{bid}", json={"plan": "premium"}).status_code == 422


def test_plan_solo_lo_cambia_un_admin(client):
    bid = client.post("/bands/", json={"name": "Banda Plan 2"}).json()["id"]
    db = SessionLocal()
    try:
        db.add(BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"))
        db.commit()
    finally:
        db.close()
    with acting_as(MEMBER):
        assert client.patch(f"/bands/{bid}", json={"plan": "pro"}).status_code == 403
