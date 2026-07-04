"""
E2E T-V5-09 — Tempo ágil: mantener pulsado +/− acelera el cambio de BPM.

- Un toque corto sigue cambiando el BPM en 1 (comportamiento previo).
- Mantener pulsado repite acelerando → sube/baja bastante más que un solo toque, sin pasarse del rango.
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def _abrir(page, live_server, api):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title="Tempo")).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    return sid


def test_tap_simple_cambia_bpm_en_1(page, live_server, api):
    _abrir(page, live_server, api)
    inicial = int(page.inner_text("#bpm-value"))
    page.click("#btn-bpm-up")
    assert int(page.inner_text("#bpm-value")) == inicial + 1
    page.click("#btn-bpm-down")
    assert int(page.inner_text("#bpm-value")) == inicial


def test_mantener_pulsado_acelera_el_bpm(page, live_server, api):
    _abrir(page, live_server, api)
    inicial = int(page.inner_text("#bpm-value"))

    box = page.locator("#btn-bpm-up").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(1500)   # mantener pulsado ~1.5 s
    page.mouse.up()

    bpm = int(page.inner_text("#bpm-value"))
    # Mantener sube MUCHO más que un solo toque (+1): la repetición acelerada dispara varios pasos.
    assert bpm >= inicial + 3, f"el mantener pulsado no repitió/aceleró el BPM ({inicial} → {bpm})"
    # …y el motor acota: nunca por encima del máximo.
    assert bpm <= 240, f"el BPM se pasó del máximo (bpm={bpm})"
