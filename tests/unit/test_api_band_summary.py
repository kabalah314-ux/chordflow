"""
Tests del Resumen de banda (V4-F2, T-129).

`GET /bands/{id}/summary` arma en UNA ida y vuelta el panel del espacio de banda: próximo evento
(con asistencia + mi estado), último mensaje del chat general, mi saldo y contadores. El AISLAMIENTO
multi-tenant (regla de oro) lo cubre el gate transversal `test_aislamiento_parametrizado.py`; aquí se
verifica la FORMA y que los contadores cuentan solo lo de esa banda.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.unit


def test_summary_forma_basica(client):
    bid = client.post("/bands/", json={"name": "Banda Resumen"}).json()["id"]
    # Sembrar: un evento futuro, un mensaje, una canción de banda, una colección y un setlist.
    client.post(f"/bands/{bid}/events/",
                json={"type": "concert", "title": "Bolo Resumen", "starts_at": "2099-05-05T20:00:00"})
    client.post(f"/bands/{bid}/messages/", json={"body": "nos vemos en el ensayo"})
    client.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Tema Resumen"))
    client.post(f"/bands/{bid}/collections/", json={"name": "Acústico", "song_ids": []})
    client.post(f"/bands/{bid}/setlists/", json={"name": "Set 1", "song_ids": []})

    r = client.get(f"/bands/{bid}/summary")
    assert r.status_code == 200
    d = r.json()

    # Próximo evento con su título y mi estado (aún sin marcar → None).
    assert d["next_event"] is not None
    assert d["next_event"]["title"] == "Bolo Resumen"
    assert "attendance" in d["next_event"]

    # Último mensaje del chat general, marcado como mío.
    assert d["last_message"] is not None
    assert d["last_message"]["body"] == "nos vemos en el ensayo"
    assert d["last_message"]["is_mine"] is True

    # Saldo numérico (sin movimientos → 0) y contadores correctos.
    assert float(d["my_balance"]) == 0.0
    assert d["counts"] == {"songs": 1, "setlists": 1, "collections": 1}


def test_summary_vacio_sin_datos(client):
    bid = client.post("/bands/", json={"name": "Banda Vacía"}).json()["id"]
    d = client.get(f"/bands/{bid}/summary").json()
    assert d["next_event"] is None
    assert d["last_message"] is None
    assert d["counts"] == {"songs": 0, "setlists": 0, "collections": 0}


def test_summary_excluye_evento_pasado(client):
    bid = client.post("/bands/", json={"name": "Banda Pasada"}).json()["id"]
    client.post(f"/bands/{bid}/events/",
                json={"type": "rehearsal", "title": "Ensayo Viejo", "starts_at": "2000-01-01T20:00:00"})
    d = client.get(f"/bands/{bid}/summary").json()
    assert d["next_event"] is None  # un evento pasado no es el "próximo"
