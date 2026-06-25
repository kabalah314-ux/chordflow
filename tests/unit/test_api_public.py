"""
V3-F7 — Plano público: GET /public/events/{id} (sin auth).

Regla de oro pública (distinta del aislamiento de banda): una fila **privada jamás aparece** en
`/public`, y la proyección **nunca** incluye datos sensibles (caché/contacto/notas/setlist/band_id).
"""

import pytest

pytestmark = pytest.mark.unit

SENSITIVE = ("fee", "contact_name", "contact_phone", "notes", "setlist_id",
             "attendance", "band_id", "visibility", "status")


def _concert(client, bid, **over):
    payload = {
        "type": "concert", "title": "Bolo Público", "starts_at": "2099-09-09T21:00:00",
        "fee": "500.00", "contact_name": "Promotor Secreto", "contact_phone": "600123123",
        "notes": "nota interna privada",
    }
    payload.update(over)
    r = client.post(f"/bands/{bid}/events/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_evento_unlisted_se_sirve_con_proyeccion_segura(client):
    bid = client.post("/bands/", json={"name": "Banda Pública"}).json()["id"]
    eid = _concert(client, bid)
    # Por defecto es privado → 404 en público.
    assert client.get(f"/public/events/{eid}").status_code == 404

    # El admin lo comparte (unlisted).
    assert client.patch(f"/bands/{bid}/events/{eid}", json={"visibility": "unlisted"}).status_code == 200

    r = client.get(f"/public/events/{eid}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["title"] == "Bolo Público"
    assert data["band_name"] == "Banda Pública"
    assert data["type"] == "concert"
    # NINGÚN dato sensible se filtra.
    for k in SENSITIVE:
        assert k not in data, f"el plano público filtró '{k}'"
    # Y los valores sensibles no aparecen por ningún lado del JSON serializado.
    blob = r.text
    assert "500.00" not in blob and "Promotor Secreto" not in blob and "nota interna" not in blob


def test_evento_privado_no_aparece_en_publico(client):
    bid = client.post("/bands/", json={"name": "Banda Privada"}).json()["id"]
    eid = _concert(client, bid)  # private por defecto
    assert client.get(f"/public/events/{eid}").status_code == 404


def test_evento_publico_tambien_se_sirve(client):
    bid = client.post("/bands/", json={"name": "Banda Visible"}).json()["id"]
    eid = _concert(client, bid)
    client.patch(f"/bands/{bid}/events/{eid}", json={"visibility": "public"})
    assert client.get(f"/public/events/{eid}").status_code == 200


def test_evento_borrado_o_inexistente_da_404(client):
    bid = client.post("/bands/", json={"name": "Banda Efímera"}).json()["id"]
    eid = _concert(client, bid)
    client.patch(f"/bands/{bid}/events/{eid}", json={"visibility": "unlisted"})
    assert client.get(f"/public/events/{eid}").status_code == 200
    client.delete(f"/bands/{bid}/events/{eid}")
    assert client.get(f"/public/events/{eid}").status_code == 404
    assert client.get("/public/events/no-existe-12345").status_code == 404
