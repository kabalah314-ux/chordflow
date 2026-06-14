"""
Test del cache-busting automático (T-022).

Garantiza que los `?v=<hash>` de los `static/*.html` coinciden con el contenido real de los
assets. Si alguien edita un `.js`/`.css` y no reejecuta `python harness/cachebust.py`, este test
falla → se acabó la clase de error de "olvidé subir el número de versión".
"""

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parent.parent.parent


def _load_cachebust():
    spec = importlib.util.spec_from_file_location("cachebust", ROOT / "harness" / "cachebust.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cache_busting_al_dia():
    cb = _load_cachebust()
    stale = cb.check()
    assert stale == [], (
        "Hay ?v= desactualizados (corre `python harness/cachebust.py`): " + ", ".join(stale))
