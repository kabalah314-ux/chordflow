"""
V6-F9b — Red profesional (T-V6-96..100): perfiles de sala/profesional, convocatorias y
candidaturas (I-20 completo: publicar → postular → elegir → concierto en la agenda), EPK y página
pública de banda, mensajes de contacto, valoraciones con relación previa y reportes.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership, MusicianProfile

pytestmark = pytest.mark.unit

MUSICO = "00000000-0000-0000-0000-000000000000"   # admin de la banda (usuario por defecto)
MIEMBRO = "22222222-2222-2222-2222-222222222222"
SALA = "55555555-5555-5555-5555-555555555555"     # dueño de la sala
FOTO = "66666666-6666-6666-6666-666666666666"     # fotógrafo
OTRO = "77777777-7777-7777-7777-777777777777"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _band(client, name="Los Pruebas"):
    bid = client.post("/bands/", json={"name": name}).json()["id"]
    db = SessionLocal()
    try:
        db.add(BandMembership(band_id=bid, user_id=MIEMBRO, role="member", status="active"))
        for uid, n in ((SALA, "Marta Sala"), (FOTO, "Pau Foto")):
            if db.get(MusicianProfile, uid) is None:
                db.add(MusicianProfile(id=uid, display_name=n))
        db.commit()
    finally:
        db.close()
    return bid


def _venue(client, name="Sala Luz"):
    with acting_as(SALA):
        r = client.post("/me/pro-profiles", json={
            "kind": "venue", "name": name, "zone": "Barcelona", "capacity": 150,
            "styles": ["rock", "versiones", "Rock"], "phone": "600999000", "show_phone": False,
            "address": "Carrer Major 1", "links": [{"label": "Web", "url": "https://sala.example"}]})
        assert r.status_code == 201, r.text
        return r.json()


def _call(client, pro_id, **extra):
    with acting_as(SALA):
        r = client.post(f"/me/pro-profiles/{pro_id}/gig-calls", json={
            "title": "Banda de versiones para el 20/12", "starts_at": "2099-12-20T22:00:00",
            "styles": ["versiones"], "format": "2 pases de 45 min", "deal_type": "fee",
            "fee": "300.00", "conditions": "Cena incluida", **extra})
        assert r.status_code == 201, r.text
        return r.json()


def test_perfil_de_sala_y_listado_publico_sin_telefono(client):
    v = _venue(client)
    assert v["styles"] == ["rock", "versiones"]  # sin duplicados
    assert v["phone"] == "600999000"  # el dueño lo ve
    lst = client.get("/public/pros?kind=venue&zone=barcel").json()
    assert any(p["id"] == v["id"] for p in lst)
    assert "600999000" not in str(lst) and "user_id" not in str(lst)
    pub = client.get(f"/public/pros/{v['id']}").json()
    assert pub["phone"] is None and pub["address"] == "Carrer Major 1"
    # Con sesión y show_phone=False → tampoco
    with acting_as(OTRO):
        assert client.get(f"/pros/{v['id']}").json()["phone"] is None
        # Un ajeno no edita el perfil
        assert client.patch(f"/me/pro-profiles/{v['id']}", json={"name": "X"}).status_code == 404
    with acting_as(SALA):
        client.patch(f"/me/pro-profiles/{v['id']}", json={"show_phone": True})
    with acting_as(OTRO):
        assert client.get(f"/pros/{v['id']}").json()["phone"] == "600999000"
    # Público sin sesión: nunca
    assert client.get(f"/public/pros/{v['id']}").json()["phone"] is None


def test_solo_salas_y_bookers_publican_convocatorias(client):
    with acting_as(FOTO):
        foto = client.post("/me/pro-profiles", json={"kind": "photographer", "name": "Pau Foto",
                                                      "zone": "Girona"}).json()
        assert client.post(f"/me/pro-profiles/{foto['id']}/gig-calls",
                           json={"title": "x"}).status_code == 400
    lst = client.get("/public/pros?kind=pros").json()
    assert any(p["id"] == foto["id"] for p in lst) and all(p["kind"] != "venue" for p in lst)


def test_flujo_convocatoria_completo(client):
    bid = _band(client)
    otra = _band(client, "Los Otros")
    v = _venue(client, "Sala Flujo")
    call = _call(client, v["id"])
    assert call["zone"] == "Barcelona"  # hereda la zona del perfil

    pub = client.get("/public/gig-calls?style=versiones").json()
    assert any(c["id"] == call["id"] for c in pub)

    # EPK de la banda (admin) → viaja en la candidatura
    client.put(f"/bands/{bid}/epk", json={"bio": "Versiones de los 80", "formation": "cuarteto",
                                          "styles": ["versiones"]})
    with acting_as(MIEMBRO):  # un miembro no postula (solo admin)
        assert client.post(f"/bands/{bid}/gig-applications",
                           json={"gig_call_id": call["id"]}).status_code == 403
    with acting_as(OTRO):  # ajeno → 404
        assert client.post(f"/bands/{bid}/gig-applications",
                           json={"gig_call_id": call["id"]}).status_code == 404

    r = client.post(f"/bands/{bid}/gig-applications",
                    json={"gig_call_id": call["id"], "message": "¡Nos encantaría!"})
    assert r.status_code == 201, r.text
    app_id = r.json()["id"]
    assert client.post(f"/bands/{bid}/gig-applications",
                       json={"gig_call_id": call["id"]}).status_code == 409
    a2 = client.post(f"/bands/{otra}/gig-applications", json={"gig_call_id": call["id"]}).json()

    # La sala ve las candidaturas (con EPK) y un mensaje en su bandeja
    with acting_as(SALA):
        apps = client.get(f"/me/gig-calls/{call['id']}/applications").json()
        mine = next(a for a in apps if a["id"] == app_id)
        assert mine["epk"]["bio"] == "Versiones de los 80" and mine["status"] == "seen"
        threads = client.get("/me/threads").json()
        assert any(t["title"] == "Los Pruebas" for t in threads)
        # Otro usuario no ve las candidaturas
    with acting_as(OTRO):
        assert client.get(f"/me/gig-calls/{call['id']}/applications").status_code == 404

    # Antes de la relación, no se puede valorar
    assert client.post(f"/pros/{v['id']}/reviews", json={"stars": 5}).status_code == 403

    with acting_as(SALA):
        r = client.post(f"/me/gig-calls/{call['id']}/applications/{app_id}/choose")
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "chosen"
        eid = r.json()["event_id"]
        assert client.post(f"/me/gig-calls/{call['id']}/applications/{a2['id']}/choose"
                           ).status_code == 409
        assert client.get(f"/me/pro-profiles/{v['id']}/calendar").json()[0]["kind"] == "gig"

    # El concierto está en la agenda de la banda, con la sala en sus Salas y el caché
    ev = client.get(f"/bands/{bid}/events/{eid}").json()
    assert ev["type"] == "concert" and ev["starts_at"].startswith("2099-12-20")
    assert ev["venue_name"] == "Sala Flujo" and float(ev["fee"]) == 300.0
    assert any(x["name"] == "Sala Flujo" for x in client.get(f"/bands/{bid}/venues/").json())
    # Las demás, declinadas; la convocatoria, cubierta y fuera del listado público
    other_apps = client.get(f"/bands/{otra}/gig-applications").json()
    assert other_apps[0]["status"] == "declined"
    assert all(c["id"] != call["id"] for c in client.get("/public/gig-calls").json())

    # Ahora sí se valoran mutuamente
    rv = client.post(f"/pros/{v['id']}/reviews", json={"stars": 5, "body": "Trato genial"})
    assert rv.status_code == 200, rv.text
    with acting_as(SALA):
        assert client.post(f"/network/bands/{bid}/reviews", json={"stars": 4}).status_code == 200
    assert client.get(f"/public/pros/{v['id']}").json()["rating_avg"] == 5.0
    with acting_as(OTRO):  # sin relación → 403
        assert client.post(f"/pros/{v['id']}/reviews", json={"stars": 1}).status_code == 403


def test_epk_publico_y_contacto_con_la_banda(client):
    bid = _band(client, "Banda EPK")
    assert client.get(f"/public/bands/{bid}").status_code == 404  # sin EPK público
    with acting_as(MIEMBRO):
        assert client.put(f"/bands/{bid}/epk", json={"is_public": True}).status_code == 403
    client.put(f"/bands/{bid}/epk", json={"is_public": True, "bio": "Rock", "rider_notes": "2 DI",
                                          "links": [{"label": "YouTube",
                                                     "url": "https://youtube.com/x"}]})
    pub = client.get(f"/public/bands/{bid}").json()
    assert pub["epk"]["bio"] == "Rock" and pub["epk"]["rider_notes"] is None
    assert client.put(f"/bands/{bid}/epk", json={
        "links": [{"label": "x", "url": "javascript:alert(1)"}]}).status_code == 422

    with acting_as(SALA):
        r = client.post(f"/network/bands/{bid}/contact", json={"body": "¿Tocáis en enero?"})
        assert r.status_code == 201
        tid = r.json()["id"]
    # Cualquier miembro de la banda ve y responde
    with acting_as(MIEMBRO):
        t = client.get(f"/me/threads/{tid}").json()
        assert t["messages"][0]["body"] == "¿Tocáis en enero?"
        assert client.post(f"/me/threads/{tid}/messages", json={"body": "¡Sí!"}).status_code == 200
    with acting_as(OTRO):
        assert client.get(f"/me/threads/{tid}").status_code == 404
    # La propia banda no se escribe a sí misma
    assert client.post(f"/network/bands/{bid}/contact", json={"body": "x"}).status_code == 400


def test_reportes_ocultan_tras_tres_personas(client):
    v = _venue(client, "Sala Dudosa")
    for uid in (OTRO, FOTO, MIEMBRO):
        with acting_as(uid):
            assert client.post("/reports", json={"target_kind": "pro", "target_id": v["id"],
                                                 "reason": "Perfil falso"}).status_code == 201
    assert client.get(f"/public/pros/{v['id']}").status_code == 404
    assert all(p["id"] != v["id"] for p in client.get("/public/pros").json())


def test_moderacion_del_catalogo(client):
    """T-V6-66: quien publica retira; comentarios los borra su autor o quien publicó; 3 reportes
    ocultan la partitura."""
    s = client.post("/songs/", json={"title": "Para el catálogo", "sections": []}).json()
    sc = client.post("/catalog/publish", json={"song_id": s["id"]})
    assert sc.status_code == 201, sc.text
    sid = sc.json()["id"]
    assert client.get(f"/catalog/scores/{sid}").json()["is_mine"] is True
    with acting_as(OTRO):
        c = client.post(f"/catalog/scores/{sid}/comments", json={"body": "Falta el puente"}).json()
        assert client.delete(f"/catalog/scores/{sid}").status_code == 404   # no es suya
    with acting_as(FOTO):
        assert client.delete(f"/catalog/scores/{sid}/comments/{c['id']}").status_code == 403
    assert client.delete(f"/catalog/scores/{sid}/comments/{c['id']}").status_code == 204
    for uid in (OTRO, FOTO, MIEMBRO):
        with acting_as(uid):
            client.post("/reports", json={"target_kind": "score", "target_id": sid,
                                          "reason": "Letra completa con derechos"})
    assert client.get(f"/catalog/scores/{sid}").status_code == 404   # oculta hasta revisión


def test_quien_publica_retira_su_partitura(client):
    s = client.post("/songs/", json={"title": "Me arrepiento", "sections": []}).json()
    sid = client.post("/catalog/publish", json={"song_id": s["id"]}).json()["id"]
    assert client.delete(f"/catalog/scores/{sid}").status_code == 204
    assert client.get(f"/catalog/scores/{sid}").status_code == 404
