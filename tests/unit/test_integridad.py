"""
Tests de integridad a nivel de esquema (T-034/035/036).

- owner_id NOT NULL: ninguna canción puede quedar sin dueño (T-034).
- Line.type: validación de schema (Literal → 422) y CHECK en BD como defensa en profundidad (T-035).
- server_default: un INSERT por SQL directo (sin pasar por los defaults de Python) recibe igualmente
  los valores por defecto desde la propia BD (T-036).

El fixture `client` crea el esquema con `create_all` a partir de los modelos, así que estas
restricciones (NOT NULL, CHECK, server_default) están presentes en la BD de test.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.unit


def test_line_type_invalido_da_422(client):
    """Un `type` de línea fuera de la lista permitida → 422 (validación de schema, T-035)."""
    payload = sample_song_payload()
    payload["sections"][0]["lines"][0]["type"] = "BASURA"
    r = client.post("/songs/", json=payload)
    assert r.status_code == 422, r.text


def test_owner_id_not_null_en_bd(client):
    """Insertar una canción SIN owner_id por SQL directo → IntegrityError (NOT NULL, T-034)."""
    from sqlalchemy import text

    from src.services.db import SessionLocal

    db = SessionLocal()
    try:
        with pytest.raises(IntegrityError):
            db.execute(text("INSERT INTO songs (id, title) VALUES ('x1', 'Sin dueño')"))
            db.commit()
        db.rollback()
    finally:
        db.close()


def test_check_line_type_en_bd(client):
    """Insertar una línea con `type` inválido por SQL directo (saltándose el schema) →
    IntegrityError por el CHECK `ck_lines_type` (defensa en profundidad, T-035)."""
    from sqlalchemy import text

    from src.services.db import SessionLocal

    sid = client.post("/songs/", json=sample_song_payload()).json()["id"]
    db = SessionLocal()
    try:
        sec_id = db.execute(
            text("SELECT id FROM sections WHERE song_id = :s"), {"s": sid}
        ).scalar()
        with pytest.raises(IntegrityError):
            db.execute(text(
                'INSERT INTO lines (id, section_id, "order", type) '
                "VALUES ('lx', :sec, 1, 'BASURA')"
            ), {"sec": sec_id})
            db.commit()
        db.rollback()
    finally:
        db.close()


def test_server_default_en_bd(client):
    """Insertar una canción por SQL directo SIN bpm/is_public/capo: la BD aplica los
    server_default (no solo Python) → bpm=120, is_public=0, capo=0 (T-036)."""
    from sqlalchemy import text

    from src.services.db import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text(
            "INSERT INTO songs (id, title, owner_id) VALUES ('sd1', 'Defaults', 'u1')"
        ))
        db.commit()
        row = db.execute(text(
            "SELECT bpm, is_public, capo, format_version FROM songs WHERE id = 'sd1'"
        )).fetchone()
        assert row == (120, 0, 0, "1.0")
    finally:
        db.close()
