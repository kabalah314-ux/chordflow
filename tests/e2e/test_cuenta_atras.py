"""
E2E T-V5-08 — Cuenta atrás (pre-roll) antes de reproducir.

- El botón cicla apagada (–) · 4 · 8 y persiste (localStorage). Por defecto está apagada: Play arranca
  directo (no cambia el comportamiento previo).
- Con la cuenta activa, Play desde el principio muestra el overlay 4-3-2-1 y, al terminar, el motor
  arranca (el beat avanza). El motor no avanza durante la cuenta.
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def _abrir(page, live_server, api, title="Cuenta Atras"):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title=title)).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    return sid


def test_boton_cuenta_atras_cicla_y_persiste(page, live_server, api):
    _abrir(page, live_server, api)
    b = "#btn-countin"
    assert page.inner_text(b) == "–"          # por defecto, apagada
    page.click(b)
    assert page.inner_text(b) == "4"
    page.click(b)
    assert page.inner_text(b) == "8"
    page.click(b)
    assert page.inner_text(b) == "–"
    # Persiste entre recargas: la dejamos en 4 y comprobamos tras recargar.
    page.click(b)                              # 4
    page.reload(wait_until="networkidle")
    page.wait_for_selector(b, timeout=8000)
    assert page.inner_text(b) == "4"


def test_play_con_cuenta_muestra_overlay_y_luego_arranca(page, live_server, api):
    _abrir(page, live_server, api)
    page.click("#btn-countin")                 # activar cuenta atrás (4)
    assert page.inner_text("#btn-countin") == "4"

    page.locator("#score-container").click()
    page.click("#btn-play-pause")
    # Aparece el overlay con un número de la cuenta.
    page.wait_for_selector("#countin-overlay:not([hidden])", timeout=2000)
    assert page.inner_text("#countin-num") in ("4", "3", "2", "1")
    # Durante la cuenta el motor NO avanza (sigue en el principio).
    assert float(page.get_attribute("#current-beat-display", "data-beat")) == 0.0

    # Al terminar (~2 s a 120 BPM) el overlay se oculta y el motor arranca.
    page.wait_for_function(
        "() => document.getElementById('countin-overlay').hidden", timeout=5000)
    page.wait_for_timeout(400)
    assert float(page.get_attribute("#current-beat-display", "data-beat")) > 0.0


def test_cuenta_apagada_arranca_directo_sin_overlay(page, live_server, api):
    _abrir(page, live_server, api)
    # Por defecto apagada: Play arranca ya, sin overlay.
    assert page.inner_text("#btn-countin") == "–"
    page.locator("#score-container").click()
    page.click("#btn-play-pause")
    page.wait_for_timeout(700)
    assert page.get_attribute("#countin-overlay", "hidden") is not None  # nunca se mostró
    assert float(page.get_attribute("#current-beat-display", "data-beat")) > 0.0
