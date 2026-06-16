"""
revision.py — Revisión de la app POR SECCIONES.

Para CADA sección/fase implementada, muestra qué **integraciones** existen ya en la app
(rutas de la API registradas + páginas del front) frente a lo que esa sección debería tener,
y opcionalmente **arranca la app** para revisarla a ojo en el navegador.

Pensado para correr **al cerrar cada sección** del giro a SaaS de gestión de bandas
(ver GUIA_MAESTRA_V2_FUNCIONAL.md). Responde a "¿qué se ha integrado de verdad en esta sección?".

Uso:
    python harness/revision.py                 # resumen de TODAS las secciones (qué hay / qué falta)
    python harness/revision.py fase7           # detalle de una sección + checklist de revisión manual
    python harness/revision.py fase7 --serve    # además arranca la app (modo test) para verla en el navegador

Nunca modifica nada ni explota: si algo falla, lo informa y sigue (estilo doctor.py).
Tras revisar a ojo, anota el resultado en harness/REVISIONES.md (plantilla en templates/REVISION_TEMPLATE.md).
"""

import os
import socket
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

# Windows usa cp1252 y revienta con emojis; forzamos UTF-8 como en doctor.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
PYTHON = sys.executable

# ─────────────────────────────────────────────────────────────────────────────
# Mapa de secciones: qué rutas API y qué páginas debería integrar cada sección.
# Las marcadas `planned=True` aún no existen (son objetivo del giro) → saldrán como
# PENDIENTES hasta que se implementen. Eso es justo lo que queremos ver.
# Al implementar una fase, ajusta aquí sus rutas/páginas reales si cambian.
# ─────────────────────────────────────────────────────────────────────────────
SECTIONS = {
    # ── Lo que YA existe en producción ──────────────────────────────────────
    "repertorio": {
        "title": "Repertorio (canciones) — base actual",
        "phase": "Base / Fase 8",
        "routes": ["/songs"],
        "pages": ["library.html", "editor.html", "index.html"],
        "checklist": [
            "La biblioteca lista canciones y la búsqueda filtra",
            "El editor importa/crea y guarda → reproductor",
            "El reproductor sincroniza acordes + auto-scroll",
        ],
    },
    "setlists": {
        "title": "Setlists / repertorios",
        "phase": "Base / Fase 9",
        "routes": ["/setlists"],
        "pages": ["setlists.html"],
        "checklist": [
            "Crear, ordenar y borrar un setlist",
            "Reproducir en orden con la barra ◀ ▶",
        ],
    },
    "import": {
        "title": "Importar desde URL con IA",
        "phase": "Base / Fase 8",
        "routes": ["/import"],
        "pages": ["editor.html"],
        "checklist": [
            "Pegar una URL extrae la partitura y precarga el editor",
        ],
    },
    # ── Giro a SaaS de banda (objetivo; ver GUIA_MAESTRA_V2_FUNCIONAL.md) ─────
    "fase7": {
        "title": "Fase 7 — Identidad + núcleo de banda (multi-tenant)",
        "phase": "Fase 7 (giro)",
        # Membresía e invitaciones-por-banda viven bajo /bands/{id}/...; aceptar invitación e
        # invitaciones son /invites; el perfil es /profile.
        "routes": ["/bands", "/invites", "/profile"],
        "pages": ["bands.html", "join.html", "profile.html"],
        "checklist": [
            "Crear una banda → entro como admin y aparece en 'Mis bandas'",
            "Invitar por código → otro usuario se une (member/guest)",
            "AISLAMIENTO: un usuario ajeno NO ve/edita la banda (403/404)",
            "Dar de baja (baja blanda): pierde acceso pero sigue en histórico",
            "El perfil muestra nombres reales, no UUIDs",
        ],
    },
    "fase8": {
        "title": "Fase 8 — Repertorio de banda",
        "phase": "Fase 8 (giro)",
        "routes": ["/bands/{band_id}/songs"],
        "pages": ["bands.html"],
        "checklist": [
            "La banda tiene repertorio compartido (Song.band_id)",
            "Copiar una canción personal a la banda no toca la personal",
            "El reproductor abre canciones de banda para sus miembros",
            "Un guest ve el repertorio pero no lo edita (403)",
            "AISLAMIENTO: el repertorio no se filtra entre bandas (ajeno→404)",
        ],
    },
    "fase9": {
        "title": "Fase 9 — Setlists de banda",
        "phase": "Fase 9 (giro)",
        "routes": ["/bands/{band_id}/setlists"],
        "pages": ["bands.html"],
        "checklist": [
            "Crear un setlist de banda desde su repertorio (orden)",
            "Solo admite canciones del repertorio de la banda",
            "El reproductor abre el setlist de banda a sus miembros (◀▶)",
            "Un guest ve los setlists pero no los edita (403)",
            "Los setlists personales se preservan (no se mezclan)",
            "AISLAMIENTO: los setlists no se filtran entre bandas (ajeno→404)",
        ],
    },
    "fase10": {
        "title": "Fase 10 — Agenda (ensayos + conciertos)",
        "phase": "Fase 10 (giro)",
        "routes": ["/bands/{band_id}/events"],
        "pages": ["bands.html"],
        "checklist": [
            "Crear ensayo/concierto/otro (solo admin); miembro no puede (403)",
            "Marcar asistencia voy/no voy/quizás (incl. guest)",
            "Concierto con setlist de la banda (setlist solo en conciertos)",
            "Próximos/pasados separados en la agenda",
            "AISLAMIENTO: la agenda no se filtra entre bandas (ajeno→404)",
        ],
    },
    "fase11": {
        "title": "Fase 11 — Finanzas con división (Splitwise)",
        "phase": "Fase 11 (giro)",
        "routes": ["/bands/{band_id}/transactions", "/bands/{band_id}/balances",
                   "/bands/{band_id}/settlements"],
        "pages": ["bands.html"],
        "checklist": [
            "Gasto/ingreso con reparto (por defecto a partes iguales)",
            "Saldo neto por miembro + fondo común cuadra a cero",
            "Liquidar saldos los acerca a cero",
            "Solo admin registra; cualquier miembro ve",
            "AISLAMIENTO: las finanzas no se filtran entre bandas (ajeno→404)",
        ],
    },
    "fase12": {
        "title": "Fase 12 — Comunicación (chat + notas)",
        "phase": "Fase 12 (giro)",
        "routes": ["/bands/{band_id}/messages"],
        "pages": ["bands.html"],
        "checklist": [
            "Chat general (publicar/listar) con refresco periódico",
            "Hilo por evento separado del chat general",
            "Notas fijadas (is_pinned) por un admin, aparecen arriba",
            "Editar/borrar el propio; admin borra cualquiera",
            "AISLAMIENTO: el chat no se filtra entre bandas (ajeno→404)",
        ],
    },
    "fase13": {
        "title": "Fase 13 — App shell + diseño + vistas agregadas + rebranding BandFlow",
        "phase": "Fase 13 (giro)",
        # Endpoints agregados del contexto TÚ (/me/dashboard, /me/events, /me/balances,
        # /me/conversations). Las páginas nuevas viven en el shell BandFlow.
        "routes": ["/me"],
        "pages": ["app.html", "agenda.html", "finanzas.html", "chat.html", "band.html"],
        "checklist": [
            "El lateral (shell) aparece y navega; marca el activo; tema claro/oscuro",
            "Inicio agrega próximos eventos + últimos mensajes de mis bandas",
            "Espacio de banda (band.html): banner + pestañas reusan las secciones",
            "Agenda/Finanzas/Chat agregadas con etiqueta de banda y filtro",
            "AISLAMIENTO: las vistas agregadas solo muestran MIS bandas (left/borrada fuera)",
            "Reskin: paleta coral BandFlow + IBM Plex; la joya (player) sigue funcionando",
            "Rebranding: la marca visible es BandFlow (sin 'ChordFlow' en títulos/manifest)",
        ],
    },
}


def free_port(preferred=8788):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def wait_until_up(base_url, timeout=30):
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base_url + "/config", timeout=2)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def registered_paths():
    """Importa la app (BD temporal, modo test) y devuelve el set de rutas registradas."""
    tmp_db = Path(tempfile.gettempdir()) / "chordflow_revision.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db.as_posix()}"
    os.environ["CHORDFLOW_TEST_MODE"] = "1"
    sys.path.insert(0, str(ROOT))
    try:
        from src.main import app  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️  No se pudo importar la app para introspección: {e}")
        return set()
    paths = set()
    for route in app.routes:
        p = getattr(route, "path", None)
        if p:
            paths.add(p)
    return paths


def route_present(prefix, paths):
    """True si hay alguna ruta registrada que empiece por el prefijo."""
    return any(p == prefix or p.startswith(prefix.rstrip("/") + "/") or p.startswith(prefix)
               for p in paths)


def section_status(key, sec, paths):
    """Calcula (rutas_ok, rutas_total, pags_ok, pags_total, estado)."""
    routes = sec.get("routes", [])
    pages = sec.get("pages", [])
    r_ok = sum(1 for r in routes if route_present(r, paths))
    p_ok = sum(1 for pg in pages if (STATIC / pg).exists())
    total = len(routes) + len(pages)
    done = r_ok + p_ok
    if total == 0:
        estado = "—"
    elif done == 0:
        estado = "⛔ pendiente"
    elif done < total:
        estado = "🟡 parcial"
    else:
        estado = "✅ completa"
    return r_ok, len(routes), p_ok, len(pages), estado


def print_summary(paths):
    print("\n🔎 Revisión de la app — resumen por secciones\n" + "=" * 60)
    print(f"  {'sección':<12} {'fase':<18} {'rutas':<7} {'páginas':<8} estado")
    print("  " + "-" * 56)
    for key, sec in SECTIONS.items():
        r_ok, r_tot, p_ok, p_tot, estado = section_status(key, sec, paths)
        marca = " (planificada)" if sec.get("planned") else ""
        print(f"  {key:<12} {sec['phase']:<18} {r_ok}/{r_tot:<5} {p_ok}/{p_tot:<6} {estado}{marca}")
    print("=" * 60)
    print("Detalle de una sección:  python harness/revision.py <sección>")
    print("Verla en el navegador:   python harness/revision.py <sección> --serve\n")


def print_detail(key, paths):
    sec = SECTIONS[key]
    print(f"\n🔎 Revisión — {sec['title']}\n" + "=" * 60)
    print(f"  Fase: {sec['phase']}" + ("  (aún planificada)" if sec.get("planned") else ""))

    print("\n  Rutas API integradas:")
    for r in sec.get("routes", []):
        icon = "✅" if route_present(r, paths) else "⛔"
        print(f"    {icon} {r}")

    print("\n  Páginas del front:")
    for pg in sec.get("pages", []):
        icon = "✅" if (STATIC / pg).exists() else "⛔"
        print(f"    {icon} static/{pg}")

    print("\n  ✋ Checklist de revisión manual (verifica a ojo en la app):")
    for item in sec.get("checklist", []):
        print(f"    [ ] {item}")

    r_ok, r_tot, p_ok, p_tot, estado = section_status(key, sec, paths)
    print("\n" + "=" * 60)
    print(f"  Estado de integración: {estado}  ({r_ok}/{r_tot} rutas · {p_ok}/{p_tot} páginas)")
    print("  Apunta el resultado en harness/REVISIONES.md "
          "(plantilla: templates/REVISION_TEMPLATE.md)\n")


def serve(key):
    """Arranca la app en modo test y deja las URLs listas para revisar en el navegador."""
    sec = SECTIONS[key]
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    tmp_db = Path(tempfile.gettempdir()) / "chordflow_revision_serve.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{tmp_db.as_posix()}"
    env["CHORDFLOW_TEST_MODE"] = "1"  # sesión de prueba sin Supabase → puedes navegar la app

    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(ROOT), env=env,
    )
    try:
        if not wait_until_up(base):
            print("  ❌ La app no arrancó; revisa el log de arriba.")
            return
        print("\n  ✅ App arrancada en MODO TEST para revisión visual.")
        print(f"     Base: {base}")
        print("     Abre en el navegador las páginas de esta sección:")
        for pg in sec.get("pages", []):
            existe = "" if (STATIC / pg).exists() else "  (⛔ aún no existe)"
            print(f"       - {base}/static/{pg}{existe}")
        print("\n     (Ctrl+C para parar el servidor)\n")
        proc.wait()
    except KeyboardInterrupt:
        print("\n  Parando el servidor…")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main():
    args = [a for a in sys.argv[1:]]
    serve_flag = "--serve" in args
    args = [a for a in args if a != "--serve"]
    key = args[0] if args else None

    if key and key not in SECTIONS:
        print(f"Sección desconocida: '{key}'. Disponibles: {', '.join(SECTIONS)}")
        return 1

    paths = registered_paths()

    if not key:
        print_summary(paths)
        return 0

    print_detail(key, paths)
    if serve_flag:
        serve(key)
    return 0


if __name__ == "__main__":
    sys.exit(main())
