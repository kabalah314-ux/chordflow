"""
Tests de la API de canciones (en proceso, con TestClient).
Cubre: CRUD completo (A1) y aislamiento por dueño (A2).
Corre en modo test → el usuario autenticado es siempre TEST_USER_ID.
"""

import pytest

from tests.conftest import TEST_USER_ID, sample_song_payload

pytestmark = pytest.mark.unit


def test_crud_completo(client):
    # Lista vacía al empezar
    assert client.get("/songs/").json() == []

    # Crear
    r = client.post("/songs/", json=sample_song_payload(title="Mi Cancion"))
    assert r.status_code == 201, r.text
    song = r.json()
    sid = song["id"]
    assert song["title"] == "Mi Cancion"
    assert song["owner_id"] == TEST_USER_ID
    assert len(song["sections"]) == 1
    assert song["sections"][0]["lines"][0]["chords"][0]["chord_name"] == "Am"

    # Leer detalle
    r = client.get(f"/songs/{sid}")
    assert r.status_code == 200
    assert r.json()["id"] == sid

    # Listar (ahora hay 1)
    assert len(client.get("/songs/").json()) == 1

    # Borrar
    assert client.delete(f"/songs/{sid}").status_code == 204

    # Ya no está
    assert client.get(f"/songs/{sid}").status_code == 404
    assert client.get("/songs/").json() == []


def test_patch_solo_metadatos(client):
    sid = client.post("/songs/", json=sample_song_payload()).json()["id"]
    r = client.patch(f"/songs/{sid}", json={"bpm": 88})
    assert r.status_code == 200
    assert r.json()["bpm"] == 88
    # La estructura sigue intacta tras el PATCH
    assert len(r.json()["sections"]) == 1


def test_put_no_deja_filas_huerfanas(client):
    """Editar (PUT) no debe dejar lines/chord_markers/tab_lines huérfanos (T-003).
    El bug original: bulk delete de secciones que no disparaba el cascade ORM."""
    from sqlalchemy import func

    from src.services.db import SessionLocal
    from src.services.models import ChordMarker, Line, Section

    def contar():
        db = SessionLocal()
        try:
            return {
                "sections": db.query(func.count(Section.id)).scalar(),
                "lines": db.query(func.count(Line.id)).scalar(),
                "chords": db.query(func.count(ChordMarker.id)).scalar(),
            }
        finally:
            db.close()

    # Crear: el payload de ejemplo tiene 1 sección, 1 línea, 2 acordes
    sid = client.post("/songs/", json=sample_song_payload()).json()["id"]
    assert contar() == {"sections": 1, "lines": 1, "chords": 2}

    # Editar dos veces con el mismo payload. Si hubiera fuga, los contadores crecerían.
    for _ in range(2):
        r = client.put(f"/songs/{sid}", json=sample_song_payload(title="Editada"))
        assert r.status_code == 200, r.text

    # Tras editar, sigue habiendo exactamente la estructura de UNA canción.
    assert contar() == {"sections": 1, "lines": 1, "chords": 2}


def test_aislamiento_por_dueno(client):
    """Una canción de otro usuario no aparece para el usuario de prueba (A2)."""
    from src.services.db import SessionLocal
    from src.services.models import Song

    # Insertar directamente una canción de OTRO dueño
    db = SessionLocal()
    try:
        db.add(Song(title="Ajena", owner_id="otro-usuario-distinto"))
        db.commit()
    finally:
        db.close()

    # El usuario de prueba crea la suya
    client.post("/songs/", json=sample_song_payload(title="Mia"))

    titles = [s["title"] for s in client.get("/songs/").json()]
    assert "Mia" in titles
    assert "Ajena" not in titles  # el filtro por owner_id funciona
