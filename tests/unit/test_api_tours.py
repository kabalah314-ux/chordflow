"""
Tests de las giras (V3-F5).

Crear (solo admin), listar/ver (miembros), paradas ligadas a conciertos de la banda, presupuesto
estimado con total, editar/borrar (admin) y **aislamiento** (ajeno→404 en cada ruta).
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership

pytestmark = pytest.mark.unit

ADMIN = "00000000-0000-0000-0000-000000000000"
MEMBER = "22222222-2222-2222-2222-222222222222"
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _band(client, name="Banda Giras"):
    bid = client.post("/bands/", json={"name": name}).json()["id"]
    db = SessionLocal()
    try:
        db.add(BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"))
        db.commit()
    finally:
        db.close()
    return bid


def test_admin_crea_gira_miembro_no(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/tours/", json={"name": "Gira Verano 2026"})
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Gira Verano 2026" and r.json()["status"] == "planning"
    assert float(r.json()["total_budget"]) == 0.0

    with acting_as(MEMBER):  # miembro no crea (solo admin)
        assert client.post(f"/bands/{bid}/tours/", json={"name": "X"}).status_code == 403


def test_paradas_ligan_conciertos_de_la_banda(client):
    bid = _band(client)
    tid = client.post(f"/bands/{bid}/tours/", json={"name": "Gira"}).json()["id"]
    eid = client.post(f"/bands/{bid}/events/",
                      json={"type": "concert", "title": "Bolo Madrid"}).json()["id"]

    # Parada ligada al concierto de la banda → OK, enriquecida con el título del evento
    r = client.post(f"/bands/{bid}/tours/{tid}/stops",
                    json={"event_id": eid, "city": "Madrid"})
    assert r.status_code == 201, r.text
    stops = r.json()["stops"]
    assert len(stops) == 1 and stops[0]["city"] == "Madrid"
    assert stops[0]["position"] == 0 and stops[0]["event_title"] == "Bolo Madrid"

    # Parada con un evento de OTRA banda → 400
    otra = client.post("/bands/", json={"name": "Otra"}).json()["id"]
    e2 = client.post(f"/bands/{otra}/events/", json={"type": "concert", "title": "Ajeno"}).json()["id"]
    assert client.post(f"/bands/{bid}/tours/{tid}/stops",
                       json={"event_id": e2}).status_code == 400

    # Segunda parada sin evento → posición 1
    r2 = client.post(f"/bands/{bid}/tours/{tid}/stops", json={"city": "Bilbao"})
    assert r2.status_code == 201
    assert [s["position"] for s in r2.json()["stops"]] == [0, 1]


def test_presupuesto_suma_total(client):
    bid = _band(client)
    tid = client.post(f"/bands/{bid}/tours/", json={"name": "Gira"}).json()["id"]
    client.post(f"/bands/{bid}/tours/{tid}/budget",
                json={"concept": "Furgoneta", "estimated_amount": "300.00"})
    r = client.post(f"/bands/{bid}/tours/{tid}/budget",
                    json={"concept": "Hotel", "category": "alojamiento", "estimated_amount": "150.50"})
    assert r.status_code == 201
    assert float(r.json()["total_budget"]) == pytest.approx(450.50)
    # El resumen también trae el total y el nº de paradas
    summ = next(t for t in client.get(f"/bands/{bid}/tours/").json() if t["id"] == tid)
    assert float(summ["total_budget"]) == pytest.approx(450.50) and summ["stop_count"] == 0


def test_listar_ver_editar_borrar(client):
    bid = _band(client)
    tid = client.post(f"/bands/{bid}/tours/", json={"name": "Gira"}).json()["id"]

    with acting_as(MEMBER):  # un miembro lista y ve
        assert len(client.get(f"/bands/{bid}/tours/").json()) == 1
        assert client.get(f"/bands/{bid}/tours/{tid}").status_code == 200

    r = client.patch(f"/bands/{bid}/tours/{tid}", json={"status": "active", "name": "Gira Otoño"})
    assert r.status_code == 200 and r.json()["status"] == "active" and r.json()["name"] == "Gira Otoño"

    with acting_as(MEMBER):  # miembro no edita ni borra
        assert client.patch(f"/bands/{bid}/tours/{tid}", json={"name": "X"}).status_code == 403
        assert client.delete(f"/bands/{bid}/tours/{tid}").status_code == 403

    assert client.delete(f"/bands/{bid}/tours/{tid}").status_code == 204
    assert client.get(f"/bands/{bid}/tours/{tid}").status_code == 404


def test_aislamiento_un_ajeno_no_ve_ni_toca_las_giras(client):
    bid = _band(client)
    tid = client.post(f"/bands/{bid}/tours/", json={"name": "Gira"}).json()["id"]
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/tours/").status_code == 404
        assert client.post(f"/bands/{bid}/tours/", json={"name": "X"}).status_code == 404
        assert client.get(f"/bands/{bid}/tours/{tid}").status_code == 404
        assert client.patch(f"/bands/{bid}/tours/{tid}", json={"name": "X"}).status_code == 404
        assert client.delete(f"/bands/{bid}/tours/{tid}").status_code == 404
        assert client.post(f"/bands/{bid}/tours/{tid}/stops", json={"city": "X"}).status_code == 404
        assert client.post(f"/bands/{bid}/tours/{tid}/budget",
                           json={"concept": "X", "estimated_amount": "1.00"}).status_code == 404
