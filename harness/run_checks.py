"""
run_checks.py — Orquesta toda la verificación de calidad en una sola pasada.

Ejecuta en cadena y reporta un resumen único:
    1. doctor.py          (salud del entorno + smoke)
    2. ruff               (lint)
    3. pytest tests/unit  (API + lógica, rápido)
    4. pytest tests/e2e   (navegador con Playwright)

Uso:
    python harness/run_checks.py            # todo
    python harness/run_checks.py --fast     # sin e2e (más rápido durante el desarrollo)

Código de salida 0 si todo pasa, 1 si algo falla. Es la definición de "terminado".
"""

import subprocess
import sys
from pathlib import Path

# UTF-8 en la salida: la consola de Windows (cp1252) revienta con los emojis del resumen.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
FAST = "--fast" in sys.argv

# (etiqueta, comando). Cada comando se ejecuta desde la raíz del proyecto.
steps = [
    ("doctor (entorno + smoke)", [PYTHON, "harness/doctor.py"]),
    ("ruff (lint)", [PYTHON, "-m", "ruff", "check", "."]),
    ("pytest unit (API + lógica)", [PYTHON, "-m", "pytest", "tests/unit", "-m", "unit"]),
]
if not FAST:
    steps.append(("pytest e2e (navegador)", [PYTHON, "-m", "pytest", "tests/e2e", "-m", "e2e"]))

print("\n🚦 ChordFlow — run_checks" + (" (modo rápido, sin e2e)" if FAST else "") + "\n" + "=" * 55)

resultados = []
for label, cmd in steps:
    print(f"\n▶ {label}\n" + "-" * 55)
    code = subprocess.call(cmd, cwd=str(ROOT))
    resultados.append((label, code == 0))

print("\n" + "=" * 55)
print("Resumen:")
for label, ok in resultados:
    print(f"  {'✅' if ok else '❌'} {label}")

todo_ok = all(ok for _, ok in resultados)
print("=" * 55)
print("✅ TODO VERDE — puedes cerrar la tarea." if todo_ok
      else "❌ Hay fallos — la tarea NO está terminada.")
sys.exit(0 if todo_ok else 1)
