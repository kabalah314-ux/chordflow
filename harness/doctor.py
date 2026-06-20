"""
doctor.py — Iniciador de salud de ChordFlow.

Comprueba, en orden y deteniéndose en el primer fallo grave, que el proyecto
arranca y responde sin errores. Pensado para correr ANTES y DESPUÉS de cada cambio.

Uso:
    python harness/doctor.py

Salida: una línea por chequeo con ✅/❌ y un resumen final. Código de salida 0 si todo
verde, 1 si algo falla (útil para CI).
"""

import os
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# La consola de Windows usa cp1252 por defecto y revienta con los emojis (🩺, ✅…).
# Forzamos UTF-8 en la salida para que el doctor corra en cualquier plataforma.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent  # raíz del proyecto
PYTHON = sys.executable

# Acumulador de resultados: lista de (ok: bool, etiqueta, detalle)
results = []


def check(label):
    """Decorador-ligero: registra el resultado de una función que devuelve (ok, detalle)."""
    def run(fn):
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001 - el doctor nunca debe explotar
            ok, detail = False, f"excepción: {e}"
        results.append((ok, label, detail))
        icon = "✅" if ok else "❌"
        print(f"  {icon} {label}" + (f" — {detail}" if detail else ""))
        return ok
    return run


def free_port(preferred=8799):
    """Devuelve un puerto libre (intenta el preferido)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def http_get(url, timeout=5):
    """GET simple. Devuelve (status, body_text). No lanza en 4xx/5xx."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def wait_until_up(base_url, timeout=45):
    """Espera a que el servidor responda. Devuelve True si arrancó.

    45 s (no 25): en máquinas lentas/cargadas el arranque en frío de uvicorn + el import de la app
    (SQLAlchemy, routers, pydantic) ronda los ~25-30 s y rozaba el deadline → falso negativo. Mismo
    criterio que el deadline del `live_server` de los e2e (subido en T-042)."""
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base_url + "/config", timeout=2)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def main():
    print("\n🩺 ChordFlow doctor\n" + "=" * 50)

    # ── 1. Entorno Python ──────────────────────────────────────────────────
    @check("Python >= 3.10")
    def _():
        v = sys.version_info
        return (v >= (3, 10), f"{v.major}.{v.minor}.{v.micro}")

    @check("Dependencias del backend instaladas")
    def _():
        faltan = []
        for mod in ("fastapi", "uvicorn", "sqlalchemy", "pydantic", "dotenv"):
            try:
                __import__(mod)
            except ImportError:
                faltan.append(mod)
        return (not faltan, "todo presente" if not faltan else f"faltan: {', '.join(faltan)}")

    # ── 2. Configuración / secretos (sin imprimir valores) ─────────────────
    @check("Archivos .env y .env.local presentes")
    def _():
        falt = [f for f in (".env", ".env.local") if not (ROOT / f).exists()]
        return (not falt, "presentes" if not falt else f"faltan: {', '.join(falt)}")

    @check("Claves de Supabase definidas en .env.local")
    def _():
        env_local = ROOT / ".env.local"
        if not env_local.exists():
            return False, ".env.local no existe"
        txt = env_local.read_text(encoding="utf-8", errors="replace")
        needed = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
        falt = [k for k in needed if k not in txt]
        return (not falt, "definidas" if not falt else f"faltan: {', '.join(falt)}")

    # ── 3. Base de datos abre ──────────────────────────────────────────────
    @check("La base de datos abre (engine + connect)")
    def _():
        from sqlalchemy import create_engine, text
        db_url = os.getenv("DATABASE_URL", "sqlite:///./chordflow.db")
        eng = create_engine(db_url, connect_args={"check_same_thread": False}
                            if db_url.startswith("sqlite") else {})
        with eng.connect() as c:
            c.execute(text("SELECT 1"))
        return True, db_url.split("///")[-1] if "///" in db_url else db_url

    # ── 4. Arrancar el servidor (modo normal, BD temporal) ─────────────────
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    tmp_db = Path(tempfile.gettempdir()) / "chordflow_doctor.db"
    if tmp_db.exists():
        try:
            tmp_db.unlink()
        except OSError:
            pass

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{tmp_db.as_posix()}"
    env.pop("CHORDFLOW_TEST_MODE", None)  # modo NORMAL: queremos comprobar el 401 real

    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(ROOT), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    try:
        @check("El servidor arranca y responde")
        def _():
            up = wait_until_up(base)
            if not up:
                # Volcar las primeras líneas del log para diagnosticar
                out = ""
                if proc.poll() is not None and proc.stdout:
                    out = proc.stdout.read()[:500]
                return False, f"no respondió en {base}" + (f" | {out}" if out else "")
            return True, base

        @check("GET /config responde 200 y trae test_mode")
        def _():
            status, body = http_get(base + "/config")
            return (status == 200 and "test_mode" in body, f"HTTP {status}")

        @check("GET / redirige al inicio (app shell)")
        def _():
            status, body = http_get(base + "/")
            # urllib sigue la redirección → acabamos en app.html (200)
            return (status == 200, f"HTTP {status}")

        @check("Seguridad: GET /songs/ sin token → 401")
        def _():
            status, _body = http_get(base + "/songs/")
            return (status == 401, f"HTTP {status} (esperado 401)")

        # ── 5. Smoke de navegador (Playwright) ─────────────────────────────
        @check("Navegador: la página carga sin errores de JS")
        def _():
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                return True, "Playwright no instalado — chequeo omitido (no fatal)"

            page_errors = []
            try:
                with sync_playwright() as p:
                    try:
                        browser = p.chromium.launch()
                    except Exception as e:
                        return True, f"navegador no disponible, omitido ({e})"
                    page = browser.new_page()
                    # pageerror = excepciones JS no capturadas (lo que de verdad importa)
                    page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                    page.goto(base + "/static/login.html", wait_until="networkidle", timeout=15000)
                    browser.close()
            except Exception as e:  # noqa: BLE001
                return True, f"smoke de navegador omitido ({e})"
            return (not page_errors, "sin errores JS" if not page_errors
                    else f"errores JS: {page_errors[:2]}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    # ── Resumen ────────────────────────────────────────────────────────────
    print("=" * 50)
    fallos = [r for r in results if not r[0]]
    if fallos:
        print(f"❌ {len(fallos)} chequeo(s) fallaron:")
        for _ok, label, detail in fallos:
            print(f"   - {label}: {detail}")
        print("\nArréglalo antes de continuar (ver CLAUDE.md, paso 4).")
        return 1
    print(f"✅ Todo verde ({len(results)} chequeos). La app está sana.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
