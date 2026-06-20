"""
conftest.py — Fixtures compartidas del harness de tests de ChordFlow.

Claves:
- Activa el MODO TEST (CHORDFLOW_TEST_MODE=1) ANTES de importar la app, para que la
  autenticación use un usuario de prueba fijo sin llamar a Supabase.
- Usa bases de datos SQLite TEMPORALES y desechables (nunca toca chordflow.db).
- `client`      → TestClient en proceso para los tests de API (rápidos).
- `live_server` → servidor uvicorn real (subproceso) para los tests E2E con navegador.
- `api`         → cliente HTTP autenticado contra el live_server (para sembrar datos).
"""

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── Entorno de test: DEBE fijarse ANTES de importar la app ──────────────────
os.environ["CHORDFLOW_TEST_MODE"] = "1"
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_unit.db")

TEST_USER_ID = "00000000-0000-0000-0000-000000000000"

# Texto de ejemplo para sembrar canciones desde el editor/parser.
SAMPLE_RAW = """Verso 1:
Am        C        G
Hola mundo esto es una prueba
"""


# ─────────────────────────── Tests de API (en proceso) ─────────────────────
@pytest.fixture()
def client():
    """TestClient de FastAPI. Recrea el esquema en cada test para aislarlos."""
    from fastapi.testclient import TestClient

    from src.main import app
    from src.services import models  # noqa: F401 - registra los modelos en Base
    from src.services.db import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def sample_song_payload(title="Cancion de prueba", artist="Tester"):
    """Payload mínimo válido para POST /songs/."""
    return {
        "title": title,
        "artist": artist,
        "bpm": 100,
        "sections": [
            {
                "name": "Verso 1",
                "order": 1,
                "lines": [
                    {
                        "order": 1,
                        "type": "lyric",
                        "content": "Hola mundo",
                        "beat_start": 0,
                        "beat_duration": 4,
                        "chords": [
                            {"chord_name": "Am", "char_position": 0, "beat_offset": 0},
                            {"chord_name": "C", "char_position": 5, "beat_offset": 2},
                        ],
                    }
                ],
            }
        ],
    }


# ─────────────────────────── Tests E2E (subproceso) ────────────────────────
def _free_port(preferred=8765):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server():
    """Arranca uvicorn en modo test con una BD temporal; cede la URL base."""
    port = _free_port()
    base = f"http://127.0.0.1:{port}"

    e2e_db = ROOT / "test_e2e.db"
    if e2e_db.exists():
        e2e_db.unlink()

    env = os.environ.copy()
    env["CHORDFLOW_TEST_MODE"] = "1"
    env["DATABASE_URL"] = f"sqlite:///{e2e_db.as_posix()}"

    # IMPORTANTE: la salida del servidor va a un FICHERO, no a subprocess.PIPE.
    # Con PIPE y nadie leyéndolo, el buffer del pipe del SO (~64 KB en Windows) se
    # llena con los logs y uvicorn se BLOQUEA al escribir → el servidor cuelga a
    # mitad del suite y todo lo posterior da ReadTimeout. Además, --no-access-log
    # reduce el volumen de salida.
    log_path = ROOT / "test_e2e_server.log"
    log_fh = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app",
         "--host", "127.0.0.1", "--port", str(port), "--no-access-log"],
        cwd=str(ROOT), env=env,
        stdout=log_fh, stderr=subprocess.STDOUT,
    )

    # Esperar a que responda. 90s de margen: el arranque de uvicorn en frío (import de la app)
    # ronda los ~26s en máquinas lentas y se dispara bajo carga alta (varias suites seguidas / CI
    # / la máquina ocupada) → un deadline corto provocaba fallos en cascada de todos los e2e por no
    # llegar a arrancar (flakiness T-042; doctor usa el mismo criterio, 45s en un arranque aislado).
    deadline = time.time() + 90
    up = False
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base + "/config", timeout=2)
            up = True
            break
        except Exception:
            if proc.poll() is not None:
                break
            time.sleep(0.4)

    if not up:
        log_fh.flush()
        try:
            out = log_path.read_text(encoding="utf-8")[:1000]
        except OSError:
            out = ""
        proc.terminate()
        pytest.fail(f"El live_server no arrancó en {base}\n{out}")

    yield base

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    log_fh.close()
    for f in (e2e_db, log_path):
        if f.exists():
            try:
                f.unlink()
            except OSError:
                pass


@pytest.fixture()
def api(live_server):
    """Cliente HTTP autenticado (modo test) contra el live_server.

    Timeout explícito de 30s: el default de httpx (5s) provocaba `ReadTimeout`
    intermitentes cuando el primer request al subproceso uvicorn coincidía con el
    arranque/JIT del worker o con un pico de carga del CI (flakiness T-042)."""
    import httpx
    with httpx.Client(base_url=live_server,
                      headers={"Authorization": "Bearer test-token"},
                      timeout=30.0) as c:
        yield c


def wipe_songs(api):
    """Borra todas las canciones del usuario de prueba (para tests de estado vacío)."""
    songs = api.get("/songs/").json()
    for s in songs:
        api.delete(f"/songs/{s['id']}")
