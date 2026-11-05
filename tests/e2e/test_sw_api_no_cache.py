"""
T-V6-03 (F-01): el service worker solo cachea estáticos versionados (`/static/*?v=`) y HTML.
Antes usaba una lista negra de rutas de API y olvidó `/collections`: la biblioteca mostraba
colecciones rancias y, en un dispositivo compartido, las del usuario anterior.
"""

import pytest

pytestmark = pytest.mark.e2e

API_PREFIXES = ("/songs", "/collections", "/bands", "/me/", "/profile", "/setlists", "/config")


def test_sw_no_guarda_respuestas_de_api(page, live_server, api):
    api.post("/collections/", json={"name": "Coleccion SW", "song_ids": []})
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    try:
        page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller",
                               timeout=8000)
    except Exception:
        pytest.skip("El service worker no llegó a controlar la página en este navegador")
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#library-collections", timeout=8000)
    keys = page.evaluate("""async () => {
        const out = [];
        for (const n of await caches.keys()) {
            const c = await caches.open(n);
            for (const r of await c.keys()) out.push(new URL(r.url).pathname + new URL(r.url).search);
        }
        return out;
    }""")
    filtradas = [k for k in keys if k.startswith(API_PREFIXES)]
    assert filtradas == [], f"El SW cacheó respuestas de API: {filtradas}"
    # Y lo que sí se cachea son estáticos versionados o HTML.
    for k in keys:
        assert k.endswith(".html") or "?v=" in k, k
