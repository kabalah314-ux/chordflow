"""
Tests del dashboard agregado de Inicio (Fase 13, T-076).

`GET /me/dashboard` agrega próximos eventos + últimos mensajes de MIS bandas (con etiqueta de
banda). Incluye el test de AISLAMIENTO (regla de oro): una banda ajena nunca aparece.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership

pytestmark = pytest.mark.unit

ME = "00000000-0000-0000-0000-000000000000"   # usuario de prueba (modo test)
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_dashboard_vacio_sin_bandas(client):
    r = client.get("/me/dashboard")
    assert r.status_code == 200
    assert r.json() == {"upcoming_events": [], "recent_messages": []}


def test_dashboard_agrega_con_etiqueta_de_banda(client):
    bid = client.post("/bands/", json={"name": "Mi Banda"}).json()["id"]
    client.post(f"/bands/{bid}/events/",
                json={"type": "concert", "title": "Bolo Apolo", "starts_at": "2099-01-01T20:00:00"})
    client.post(f"/bands/{bid}/messages/", json={"body": "¿Ensayamos el finde?"})

    d = client.get("/me/dashboard").json()
    assert any(e["title"] == "Bolo Apolo" and e["band_name"] == "Mi Banda"
               for e in d["upcoming_events"])
    assert any(m["body"] == "¿Ensayamos el finde?" and m["band_name"] == "Mi Banda"
               for m in d["recent_messages"])


def test_dashboard_excluye_eventos_pasados(client):
    bid = client.post("/bands/", json={"name": "B"}).json()["id"]
    client.post(f"/bands/{bid}/events/",
                json={"type": "rehearsal", "title": "Ensayo Pasado", "starts_at": "2000-01-01T20:00:00"})
    d = client.get("/me/dashboard").json()
    assert not any(e["title"] == "Ensayo Pasado" for e in d["upcoming_events"])


def test_dashboard_aislamiento_excluye_banda_ajena(client):
    # Mi banda con un evento futuro y un mensaje
    bid = client.post("/bands/", json={"name": "Mía"}).json()["id"]
    client.post(f"/bands/{bid}/events/",
                json={"type": "concert", "title": "Evento Mío", "starts_at": "2099-02-02T20:00:00"})
    client.post(f"/bands/{bid}/messages/", json={"body": "mensaje mío"})

    # Banda AJENA (de STRANGER), donde yo NO soy miembro
    with acting_as(STRANGER):
        oid = client.post("/bands/", json={"name": "Ajena"}).json()["id"]
        client.post(f"/bands/{oid}/events/",
                    json={"type": "concert", "title": "Evento Ajeno", "starts_at": "2099-03-03T20:00:00"})
        client.post(f"/bands/{oid}/messages/", json={"body": "secreto ajeno"})

    d = client.get("/me/dashboard").json()
    titles = [e["title"] for e in d["upcoming_events"]]
    bodies = [m["body"] for m in d["recent_messages"]]
    assert "Evento Mío" in titles and "Evento Ajeno" not in titles
    assert "mensaje mío" in bodies and "secreto ajeno" not in bodies


def test_me_events_incluye_pasados_y_proximos_con_etiqueta(client):
    bid = client.post("/bands/", json={"name": "Banda Agenda"}).json()["id"]
    client.post(f"/bands/{bid}/events/",
                json={"type": "concert", "title": "Futuro", "starts_at": "2099-01-01T20:00:00"})
    client.post(f"/bands/{bid}/events/",
                json={"type": "rehearsal", "title": "Pasado", "starts_at": "2000-01-01T20:00:00"})
    evs = client.get("/me/events").json()
    titles = [e["title"] for e in evs]
    # La agenda agregada trae próximos Y pasados (a diferencia del dashboard), con etiqueta.
    assert "Futuro" in titles and "Pasado" in titles
    assert all(e["band_name"] == "Banda Agenda" for e in evs)


def test_me_events_aislamiento_excluye_banda_ajena(client):
    bid = client.post("/bands/", json={"name": "Mía"}).json()["id"]
    client.post(f"/bands/{bid}/events/",
                json={"type": "concert", "title": "Evento Propio", "starts_at": "2099-01-01T20:00:00"})
    with acting_as(STRANGER):
        oid = client.post("/bands/", json={"name": "Ajena"}).json()["id"]
        client.post(f"/bands/{oid}/events/",
                    json={"type": "concert", "title": "Evento Ajeno", "starts_at": "2099-01-01T20:00:00"})
    titles = [e["title"] for e in client.get("/me/events").json()]
    assert "Evento Propio" in titles and "Evento Ajeno" not in titles


def test_me_balances_lista_mis_bandas_aislado(client):
    bid = client.post("/bands/", json={"name": "Banda Pasta"}).json()["id"]
    client.post(f"/bands/{bid}/transactions",
                json={"type": "expense", "description": "Local", "amount": "100.00", "paid_by_fund": True})
    with acting_as(STRANGER):
        client.post("/bands/", json={"name": "Ajena Pasta"})
    bals = client.get("/me/balances").json()
    names = [b["band_name"] for b in bals]
    assert "Banda Pasta" in names and "Ajena Pasta" not in names
    mine = next(b for b in bals if b["band_name"] == "Banda Pasta")
    assert "balance" in mine and mine["band_id"] == bid


# ── Regresión del aislamiento (revisión T-078): las ramas status='left' y banda borrada ──
def test_dashboard_excluye_banda_si_me_doy_de_baja(client):
    bid = client.post("/bands/", json={"name": "Me Voy"}).json()["id"]
    client.post(f"/bands/{bid}/events/",
                json={"type": "concert", "title": "Evento Tras Baja", "starts_at": "2099-01-01T20:00:00"})
    client.post(f"/bands/{bid}/messages/", json={"body": "mensaje tras baja"})
    # Doy de baja MI membresía (status='left') directamente en BD.
    db = SessionLocal()
    try:
        m = db.query(BandMembership).filter_by(band_id=bid, user_id=ME).first()
        m.status = "left"
        db.commit()
    finally:
        db.close()
    d = client.get("/me/dashboard").json()
    evs = client.get("/me/events").json()
    assert all(e["title"] != "Evento Tras Baja" for e in d["upcoming_events"])
    assert all(m["body"] != "mensaje tras baja" for m in d["recent_messages"])
    assert all(e["title"] != "Evento Tras Baja" for e in evs)


def test_dashboard_excluye_banda_borrada(client):
    bid = client.post("/bands/", json={"name": "Borrada"}).json()["id"]
    client.post(f"/bands/{bid}/events/",
                json={"type": "concert", "title": "Evento De Borrada", "starts_at": "2099-01-01T20:00:00"})
    client.delete(f"/bands/{bid}")   # soft delete (admin)
    d = client.get("/me/dashboard").json()
    evs = client.get("/me/events").json()
    assert all(e["title"] != "Evento De Borrada" for e in d["upcoming_events"])
    assert all(e["title"] != "Evento De Borrada" for e in evs)


def test_dashboard_y_events_excluyen_cancelados(client):
    bid = client.post("/bands/", json={"name": "Con Cancelado"}).json()["id"]
    eid = client.post(f"/bands/{bid}/events/",
                      json={"type": "concert", "title": "Cancelado", "starts_at": "2099-01-01T20:00:00"}).json()["id"]
    client.patch(f"/bands/{bid}/events/{eid}", json={"status": "cancelled"})
    d = client.get("/me/dashboard").json()
    evs = client.get("/me/events").json()
    assert all(e["title"] != "Cancelado" for e in d["upcoming_events"])
    assert all(e["title"] != "Cancelado" for e in evs)


def test_dashboard_excluye_mensajes_de_hilo_de_evento(client):
    bid = client.post("/bands/", json={"name": "Con Hilo"}).json()["id"]
    eid = client.post(f"/bands/{bid}/events/",
                      json={"type": "rehearsal", "title": "Ensayo"}).json()["id"]
    client.post(f"/bands/{bid}/messages/", json={"body": "comentario de hilo", "event_id": eid})
    client.post(f"/bands/{bid}/messages/", json={"body": "mensaje general"})
    bodies = [m["body"] for m in client.get("/me/dashboard").json()["recent_messages"]]
    assert "mensaje general" in bodies and "comentario de hilo" not in bodies


def test_me_conversations_una_por_banda_aislado(client):
    bid = client.post("/bands/", json={"name": "Charla"}).json()["id"]
    client.post(f"/bands/{bid}/messages/", json={"body": "hola banda"})
    client.post("/bands/", json={"name": "Silenciosa"})   # sin mensajes
    with acting_as(STRANGER):
        client.post("/bands/", json={"name": "Ajena Chat"})

    convs = client.get("/me/conversations").json()
    names = [c["band_name"] for c in convs]
    assert "Charla" in names and "Silenciosa" in names and "Ajena Chat" not in names
    assert next(c for c in convs if c["band_name"] == "Charla")["last_body"] == "hola banda"
    assert next(c for c in convs if c["band_name"] == "Silenciosa")["last_body"] is None
    # las que tienen mensajes van primero
    assert names.index("Charla") < names.index("Silenciosa")
