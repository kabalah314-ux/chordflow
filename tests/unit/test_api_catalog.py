"""
Tests de la biblioteca global / catálogo público (V3-F9, D9).

El bucle: publicar ("ponla aquí") → buscar → ver → importar a mi banda → valorar → comentar.
Más controles de propiedad/pertenencia.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from tests.conftest import sample_song_payload

pytestmark = pytest.mark.unit

ADMIN = "00000000-0000-0000-0000-000000000000"
OTHER = "22222222-2222-2222-2222-222222222222"
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _publish_song(client, title="Wonderwall", artist="Oasis"):
    payload = sample_song_payload(title=title)
    payload["artist"] = artist
    sid = client.post("/songs/", json=payload).json()["id"]
    r = client.post("/catalog/publish", json={"song_id": sid})
    assert r.status_code == 201, r.text
    return sid, r.json()["id"]


def test_publicar_y_buscar(client):
    _sid, scid = _publish_song(client, title="Wonderwall", artist="Oasis")
    # Aparece al buscar por título o artista (insensible a mayúsculas/acentos)
    res = client.get("/catalog/search", params={"q": "wonder"}).json()
    assert any(s["id"] == scid and s["title"] == "Wonderwall" for s in res)
    assert client.get("/catalog/search", params={"q": "oasis"}).json()


def test_publicar_solo_lo_mio(client):
    # Una canción de OTRO usuario no la puedo publicar yo.
    with acting_as(STRANGER):
        sid = client.post("/songs/", json=sample_song_payload(title="Ajena")).json()["id"]
    assert client.post("/catalog/publish", json={"song_id": sid}).status_code == 403
    assert client.post("/catalog/publish", json={"song_id": "no-existe"}).status_code == 404


def test_detalle_trae_la_partitura(client):
    _sid, scid = _publish_song(client)
    d = client.get(f"/catalog/scores/{scid}").json()
    assert d["title"] == "Wonderwall"
    assert isinstance(d["sections"], list) and len(d["sections"]) >= 1  # el visor recibe el árbol
    assert client.get("/catalog/scores/no-existe").status_code == 404


def test_importar_a_banda_y_a_personal(client):
    _sid, scid = _publish_song(client)
    # A mi espacio personal
    r = client.post(f"/catalog/scores/{scid}/import", json={})
    assert r.status_code == 201 and r.json()["song_id"]

    # A una banda mía → aparece en su repertorio
    bid = client.post("/bands/", json={"name": "Mi Banda"}).json()["id"]
    r2 = client.post(f"/catalog/scores/{scid}/import", json={"band_id": bid})
    assert r2.status_code == 201
    rep = client.get(f"/bands/{bid}/songs/").json()
    assert any(s["title"] == "Wonderwall" for s in rep)

    # import_count subió
    assert client.get(f"/catalog/scores/{scid}").json()["import_count"] >= 2


def test_no_importar_a_banda_ajena(client):
    _sid, scid = _publish_song(client)
    with acting_as(STRANGER):
        bid = client.post("/bands/", json={"name": "Banda Ajena"}).json()["id"]
    assert client.post(f"/catalog/scores/{scid}/import", json={"band_id": bid}).status_code == 403


def test_valorar_recalcula_media(client):
    _sid, scid = _publish_song(client)
    r = client.put(f"/catalog/scores/{scid}/rating", json={"stars": 4})
    assert r.status_code == 200 and r.json()["rating_count"] == 1
    assert float(r.json()["rating_avg"]) == pytest.approx(4.0)
    # Otro usuario valora 2 → media 3 con 2 votos
    with acting_as(OTHER):
        client.put(f"/catalog/scores/{scid}/rating", json={"stars": 2})
    d = client.get(f"/catalog/scores/{scid}").json()
    assert d["rating_count"] == 2 and float(d["rating_avg"]) == pytest.approx(3.0)
    # Valor fuera de rango → 422
    assert client.put(f"/catalog/scores/{scid}/rating", json={"stars": 9}).status_code == 422


def test_letra_recortada_en_publico_completa_al_importar(client):
    """C1/D2: el catálogo público recorta la letra; al importar se obtiene la letra completa."""
    long_line = "Esta es una linea de letra muy larga que supera de sobra el umbral de recorte publico"
    payload = {"title": "Larga", "artist": "X", "bpm": 100, "sections": [
        {"name": "Verso", "order": 1, "lines": [
            {"order": 1, "type": "lyric", "content": long_line,
             "beat_start": 0, "beat_duration": 4, "chords": []}]}]}
    sid = client.post("/songs/", json=payload).json()["id"]
    scid = client.post("/catalog/publish", json={"song_id": sid}).json()["id"]

    pub = client.get(f"/catalog/scores/{scid}").json()
    pub_line = pub["sections"][0]["lines"][0]["content"]
    assert pub_line.endswith("…") and len(pub_line) < len(long_line), "la letra pública no se recortó"

    new_sid = client.post(f"/catalog/scores/{scid}/import", json={}).json()["song_id"]
    full = client.get(f"/songs/{new_sid}").json()
    assert full["sections"][0]["lines"][0]["content"] == long_line, "el import no trae la letra completa"


def test_no_republicar_la_misma_cancion(client):
    """D9: una canción → una publicación. Re-publicar la misma → 409 (no duplica)."""
    sid = client.post("/songs/", json=sample_song_payload(title="Una")).json()["id"]
    assert client.post("/catalog/publish", json={"song_id": sid}).status_code == 201
    assert client.post("/catalog/publish", json={"song_id": sid}).status_code == 409


def test_import_preserva_reference_url(client):
    """El enlace de referencia (YouTube) se conserva al publicar e importar (round-trip)."""
    payload = sample_song_payload(title="ConRef")
    payload["reference_url"] = "https://youtu.be/abc12345678"
    sid = client.post("/songs/", json=payload).json()["id"]
    scid = client.post("/catalog/publish", json={"song_id": sid}).json()["id"]
    new_sid = client.post(f"/catalog/scores/{scid}/import", json={}).json()["song_id"]
    assert client.get(f"/songs/{new_sid}").json()["reference_url"] == "https://youtu.be/abc12345678"


def test_comentar(client):
    _sid, scid = _publish_song(client)
    r = client.post(f"/catalog/scores/{scid}/comments", json={"body": "Falta el puente del solo"})
    assert r.status_code == 201 and r.json()["body"] == "Falta el puente del solo"
    d = client.get(f"/catalog/scores/{scid}").json()
    assert any(c["body"] == "Falta el puente del solo" for c in d["comments"])
