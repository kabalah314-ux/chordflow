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


def test_health_es_liveness(client):
    """/health responde 200 con {status: ok} y NO expone config sensible (T-025).
    Es un liveness barato, separado de /config (que sí trae datos del frontend)."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    # No debe filtrar nada de la config pública/Supabase.
    assert "supabase_url" not in r.json()


def test_delete_es_soft(client):
    """DELETE marca `deleted_at` en vez de borrar la fila (T-013): la canción
    desaparece de las lecturas pero su fila se conserva en la BD. Un segundo DELETE
    sobre la misma canción → 404 (ya no es visible)."""
    from src.services.db import SessionLocal
    from src.services.models import Song

    sid = client.post("/songs/", json=sample_song_payload()).json()["id"]

    assert client.delete(f"/songs/{sid}").status_code == 204
    # Invisible para la app...
    assert client.get(f"/songs/{sid}").status_code == 404
    assert client.get("/songs/").json() == []
    # ...pero la fila sigue en la BD, con deleted_at puesto.
    db = SessionLocal()
    try:
        row = db.query(Song).filter(Song.id == sid).first()
        assert row is not None, "el soft delete no debe borrar la fila"
        assert row.deleted_at is not None, "deleted_at debe quedar marcado"
    finally:
        db.close()
    # Segundo DELETE: ya no es visible → 404 (no 204).
    assert client.delete(f"/songs/{sid}").status_code == 404


def test_patch_solo_metadatos(client):
    sid = client.post("/songs/", json=sample_song_payload()).json()["id"]
    r = client.patch(f"/songs/{sid}", json={"bpm": 88})
    assert r.status_code == 200
    assert r.json()["bpm"] == 88
    # La estructura sigue intacta tras el PATCH
    assert len(r.json()["sections"]) == 1


def test_paginacion_acotada(client):
    """skip/limit fuera de rango → 422 (T-037)."""
    assert client.get("/songs/?skip=-1").status_code == 422
    assert client.get("/songs/?limit=0").status_code == 422
    assert client.get("/songs/?limit=99999").status_code == 422
    # valores válidos siguen funcionando
    assert client.get("/songs/?skip=0&limit=10").status_code == 200


def test_listado_es_ligero_sin_estructura(client):
    """El listado GET /songs/ no debe traer la estructura anidada `sections`
    (evita el N+1), sino un `section_count` plano (T-010)."""
    client.post("/songs/", json=sample_song_payload(title="Una"))

    listado = client.get("/songs/").json()
    assert len(listado) == 1
    item = listado[0]
    # Ligero: ni rastro de la jerarquía sections→lines→chords
    assert "sections" not in item
    # Pero sí el contador (el payload de ejemplo tiene 1 sección)
    assert item["section_count"] == 1
    # El detalle SÍ sigue trayendo la estructura completa
    detalle = client.get(f"/songs/{item['id']}").json()
    assert len(detalle["sections"]) == 1


def test_put_inexistente_devuelve_404(client):
    """PUT sobre un id que no existe debe devolver 404 (regresión: el except
    Exception ancho lo convertía en 400). T-027."""
    r = client.put("/songs/no-existe-123", json=sample_song_payload())
    assert r.status_code == 404


def test_validacion_de_rangos(client):
    """La API rechaza metadatos fuera de rango con 422 (T-024)."""
    bad_bpm = sample_song_payload()
    bad_bpm["bpm"] = 9999
    assert client.post("/songs/", json=bad_bpm).status_code == 422

    bad_year = sample_song_payload()
    bad_year["year"] = 99999
    assert client.post("/songs/", json=bad_year).status_code == 422

    # El PATCH también valida
    sid = client.post("/songs/", json=sample_song_payload()).json()["id"]
    assert client.patch(f"/songs/{sid}", json={"bpm": -5}).status_code == 422


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


def test_cascade_a_nivel_db(client):
    """Borrar una canción con SQL DIRECTO (sin pasar por el cascade ORM) tampoco debe
    dejar huérfanos: las FKs llevan ON DELETE CASCADE y SQLite fuerza FKs por conexión
    (PRAGMA). Defensa en profundidad sobre T-003. (T-033)."""
    from sqlalchemy import func, text

    from src.services.db import SessionLocal
    from src.services.models import ChordMarker, Line, Section, TabLine

    sid = client.post("/songs/", json=sample_song_payload()).json()["id"]

    db = SessionLocal()
    try:
        # Borrado crudo de la fila padre: NO dispara el cascade del ORM, solo el de la BD.
        db.execute(text("DELETE FROM songs WHERE id = :id"), {"id": sid})
        db.commit()
        # Sin cascade de BD, estas hijas quedarían huérfanas.
        assert db.query(func.count(Section.id)).scalar() == 0
        assert db.query(func.count(Line.id)).scalar() == 0
        assert db.query(func.count(ChordMarker.id)).scalar() == 0
        assert db.query(func.count(TabLine.id)).scalar() == 0
    finally:
        db.close()


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
