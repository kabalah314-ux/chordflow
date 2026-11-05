"""
V6-F9 — Funciones de banda (T-V6-81/82/83/86/88/92/94): semáforo del repertorio, vista por
miembro, pizarra, hoja del bolo (checklist + enlace público), votación de fechas (también sin
cuenta) y feedback. Cada bloque comprueba permisos por rol y aislamiento (ajeno → 404).
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership, MusicianProfile

pytestmark = pytest.mark.unit

ADMIN = "00000000-0000-0000-0000-000000000000"
MEMBER = "22222222-2222-2222-2222-222222222222"
GUEST = "33333333-3333-3333-3333-333333333333"
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _band(client, name="Banda Tools"):
    bid = client.post("/bands/", json={"name": name}).json()["id"]
    db = SessionLocal()
    try:
        db.add_all([
            BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"),
            BandMembership(band_id=bid, user_id=GUEST, role="guest", status="active"),
        ])
        if db.get(MusicianProfile, MEMBER) is None:
            db.add(MusicianProfile(id=MEMBER, display_name="Ana Bajo"))
        db.commit()
    finally:
        db.close()
    return bid


def _song(client, bid, title="Tema"):
    r = client.post(f"/bands/{bid}/songs/", json={"title": title, "duration_sec": 215})
    assert r.status_code == 201, r.text
    return r.json()


# ── Semáforo ──────────────────────────────────────────────────────────────────
def test_semaforo_privado_por_defecto_y_compartido_suma(client):
    bid = _band(client)
    s1, s2 = _song(client, bid, "Uno"), _song(client, bid, "Dos")
    assert s1["duration_sec"] == 215

    r = client.put(f"/bands/{bid}/songs/{s1['id']}/status", json={"status": "mastered"})
    assert r.status_code == 200 and r.json()["shared"] is False

    with acting_as(MEMBER):
        client.put(f"/bands/{bid}/songs/{s1['id']}/status",
                   json={"status": "improving", "shared": True})
        board = client.get(f"/bands/{bid}/song-status").json()
        # Ve lo suyo + lo compartido; el estado PRIVADO del admin no se cuenta.
        assert board["band"][s1["id"]] == {"pending": 0, "improving": 1, "mastered": 0}
        assert board["totals_mine"] == {"pending": 1, "improving": 1, "mastered": 0}
        assert board["songs_total"] == 2

    board = client.get(f"/bands/{bid}/song-status").json()
    assert board["band"][s1["id"]]["mastered"] == 1 and board["band"][s1["id"]]["improving"] == 1
    assert s2["id"] not in board["band"]

    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/song-status").status_code == 404
        assert client.put(f"/bands/{bid}/songs/{s1['id']}/status",
                          json={"status": "pending"}).status_code == 404


def test_semaforo_no_acepta_cancion_de_otra_banda(client):
    b1, b2 = _band(client, "B1"), _band(client, "B2")
    s = _song(client, b2)
    assert client.put(f"/bands/{b1}/songs/{s['id']}/status",
                      json={"status": "pending"}).status_code == 404


# ── Vista por miembro ─────────────────────────────────────────────────────────
def test_mis_preferencias_por_cancion(client):
    bid = _band(client)
    s = _song(client, bid)
    assert client.get(f"/songs/{s['id']}/my-prefs").json()["transpose"] == 0
    with acting_as(MEMBER):
        r = client.put(f"/songs/{s['id']}/my-prefs", json={"transpose": -2, "view_mode": "lyrics"})
        assert r.status_code == 200 and r.json()["transpose"] == -2
    # Lo de Ana no cambia lo mío
    assert client.get(f"/songs/{s['id']}/my-prefs").json()["transpose"] == 0
    with acting_as(STRANGER):
        assert client.get(f"/songs/{s['id']}/my-prefs").status_code == 404
    assert client.put(f"/songs/{s['id']}/my-prefs", json={"transpose": 40}).status_code == 422


# ── Pizarra ───────────────────────────────────────────────────────────────────
def test_pizarra_crud_y_roles(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/notes", json={"body": "Comprar cuerdas", "assignee_id": MEMBER,
                                                   "is_pinned": True})
    assert r.status_code == 201, r.text
    note = r.json()
    assert note["assignee_name"] == "Ana Bajo" and note["is_pinned"] is True

    with acting_as(GUEST):
        assert len(client.get(f"/bands/{bid}/notes").json()) == 1
        assert client.post(f"/bands/{bid}/notes", json={"body": "x"}).status_code == 403

    # Responsable ajeno a la banda → 400
    assert client.post(f"/bands/{bid}/notes",
                       json={"body": "y", "assignee_id": STRANGER}).status_code == 400

    with acting_as(MEMBER):
        r = client.patch(f"/bands/{bid}/notes/{note['id']}", json={"done": True})
        assert r.status_code == 200 and r.json()["done_at"]
        # Un miembro no borra la nota de otro
        assert client.delete(f"/bands/{bid}/notes/{note['id']}").status_code == 403

    assert client.get(f"/bands/{bid}/notes").json() == []
    assert len(client.get(f"/bands/{bid}/notes?include_done=true").json()) == 1
    assert client.delete(f"/bands/{bid}/notes/{note['id']}").status_code == 204

    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/notes").status_code == 404


# ── Hoja del bolo ─────────────────────────────────────────────────────────────
def test_hoja_del_bolo_checklist_y_enlace_publico(client):
    bid = _band(client)
    ev = client.post(f"/bands/{bid}/events/", json={
        "type": "concert", "title": "Bolo Sala X", "starts_at": "2099-05-01T21:00:00",
        "fee": "500.00", "contact_phone": "600111222",
        "load_in_at": "2099-05-01T17:00:00", "soundcheck_at": "2099-05-01T18:00:00",
        "address": "Calle Falsa 123", "backline_notes": "Batería de la sala"}).json()
    assert ev["load_in_at"].startswith("2099-05-01T17:00") and ev["address"] == "Calle Falsa 123"

    r = client.post(f"/bands/{bid}/events/{ev['id']}/checklist", json={"text": "Llevar DI"})
    assert r.status_code == 201
    item = r.json()
    with acting_as(MEMBER):
        assert client.patch(f"/bands/{bid}/events/{ev['id']}/checklist/{item['id']}",
                            json={"done": True}).json()["done_at"]
        # El enlace público lo crea un admin
        assert client.post(f"/bands/{bid}/events/{ev['id']}/sheet-token").status_code == 403

    tok = client.post(f"/bands/{bid}/events/{ev['id']}/sheet-token").json()["token"]
    with acting_as(STRANGER):
        pub = client.get(f"/public/gig-sheets/{tok}")
        assert pub.status_code == 200
        body = pub.text
        assert "Bolo Sala X" in body and "Llevar DI" in body and "Calle Falsa 123" in body
        # Proyección segura: ni caché ni teléfono
        assert "600111222" not in body and '"fee"' not in body and "contact" not in body
        assert client.get(f"/bands/{bid}/events/{ev['id']}/checklist").status_code == 404

    client.delete(f"/bands/{bid}/events/{ev['id']}/sheet-token")
    assert client.get(f"/public/gig-sheets/{tok}").status_code == 404


# ── Votación de fechas ────────────────────────────────────────────────────────
def test_votacion_de_fechas_flujo_completo(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/polls", json={
        "title": "Ensayo de diciembre", "type": "rehearsal", "location": "Local",
        "options": [{"starts_at": "2099-12-03T19:00:00"}, {"starts_at": "2099-12-01T19:00:00"}]})
    assert r.status_code == 201, r.text
    poll = r.json()
    assert [o["starts_at"][:10] for o in poll["options"]] == ["2099-12-01", "2099-12-03"]
    o1, o2 = poll["options"][0]["id"], poll["options"][1]["id"]
    assert set(poll["pending"]) >= {"Ana Bajo"}

    client.put(f"/bands/{bid}/polls/{poll['id']}/votes",
               json={"votes": [{"option_id": o1, "status": "yes"},
                               {"option_id": o2, "status": "no"}]})

    # Ana vota SIN sesión, por el enlace, eligiendo su nombre
    tok = poll["token"]
    with acting_as(STRANGER):
        pub = client.get(f"/public/polls/{tok}").json()
        assert pub["token"] is None and pub["band_id"] is None
        assert any(m["display_name"] == "Ana Bajo" for m in pub["members"])
        # Un id que no es miembro no puede votar
        assert client.put(f"/public/polls/{tok}/votes", json={
            "user_id": STRANGER, "votes": [{"option_id": o1, "status": "yes"}]}).status_code == 400
        r = client.put(f"/public/polls/{tok}/votes", json={
            "user_id": MEMBER, "votes": [{"option_id": o1, "status": "maybe"}]})
        assert r.status_code == 200 and r.json()["options"][0]["maybe"] == 1

    # Confirmar → evento con asistencias ya rellenas
    with acting_as(GUEST):
        assert client.post(f"/bands/{bid}/polls/{poll['id']}/confirm",
                           json={"option_id": o1}).status_code == 403
    r = client.post(f"/bands/{bid}/polls/{poll['id']}/confirm", json={"option_id": o1})
    assert r.status_code == 200 and r.json()["status"] == "closed"
    eid = r.json()["event_id"]
    ev = client.get(f"/bands/{bid}/events/{eid}").json()
    assert ev["title"] == "Ensayo de diciembre" and ev["starts_at"].startswith("2099-12-01")
    assert {a["user_id"]: a["status"] for a in ev["attendance"]} == {ADMIN: "yes", MEMBER: "maybe"}

    # Cerrada: ya no se vota
    assert client.put(f"/public/polls/{tok}/votes", json={
        "user_id": MEMBER, "votes": [{"option_id": o1, "status": "no"}]}).status_code == 409
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/polls").status_code == 404
    assert client.get("/public/polls/token-que-no-existe-xx").status_code == 404


# ── Feedback ──────────────────────────────────────────────────────────────────
def test_feedback_y_eventos_de_producto(client):
    assert client.post("/feedback", json={"body": "El metrónomo se adelanta", "page": "/app"}
                       ).status_code == 201
    assert client.post("/feedback", json={"body": ""}).status_code == 422
    assert client.post("/me/product-events", json={"kind": "player.open"}).status_code == 204
    assert client.post("/me/product-events", json={"kind": "MAL ESPACIO"}).status_code == 422


# ── Setlist inteligente (T-V6-88) ─────────────────────────────────────────────
def test_setlist_lleva_duracion_total_real_o_estimada(client):
    a = client.post("/songs/", json={"title": "Real", "bpm": 120, "duration_sec": 200,
                                     "key_root": "E", "sections": []}).json()
    b = client.post("/songs/", json={"title": "Estimada", "bpm": 120, "duration_beats": 400,
                                     "sections": []}).json()
    sl = client.post("/setlists/", json={"name": "Bolo", "song_ids": [a["id"], b["id"]]})
    assert sl.status_code == 201, sl.text
    det = sl.json()
    assert [i["duration_sec"] for i in det["items"]] == [200, 200]  # 400 pulsos a 120 = 200 s
    assert det["items"][0]["key_root"] == "E"
    summ = next(s for s in client.get("/setlists/").json() if s["id"] == det["id"])
    assert summ["duration_sec"] == 400
