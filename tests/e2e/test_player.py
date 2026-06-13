"""
E2E del reproductor: carga la canción (P1), Play avanza el beat (P2),
transponer cambia los acordes (P3).
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def _crear_y_abrir(page, live_server, api, title="Cancion Player"):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title=title)).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    return sid


def test_carga_la_cancion(page, live_server, api):
    _crear_y_abrir(page, live_server, api, title="Cancion Cargada")
    assert page.inner_text("#song-title") == "Cancion Cargada"
    assert page.locator(".chord-container, .chord-pill").count() >= 1


def test_carga_por_defecto_sin_songId(page, live_server, api):
    """Abrir el reproductor SIN ?songId debe cargar la primera canción con sus
    acordes. Regresión T-010: el listado /songs/ se volvió ligero (SongSummary sin
    `sections`); app.js debe pedir el detalle de songs[0], no renderizar el resumen."""
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Primera Por Defecto"))
    page.goto(live_server + "/static/index.html", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    assert page.inner_text("#song-title") == "Primera Por Defecto"
    # Si app.js hubiera renderizado el SongSummary (sin sections), no habría acordes.
    assert page.locator(".chord-container, .chord-pill").count() >= 1


def test_play_avanza_el_beat(page, live_server, api):
    _crear_y_abrir(page, live_server, api)
    assert "0.0" in page.inner_text("#current-beat-display")
    page.click("#btn-play-pause")
    page.wait_for_timeout(900)  # dejar correr ~1s de reproducción
    page.click("#btn-play-pause")  # pausar
    beat_txt = page.inner_text("#current-beat-display")
    # El beat debe haber avanzado por encima de 0.0
    valor = float(beat_txt.split(":")[1].strip())
    assert valor > 0.0, f"el beat no avanzó: {beat_txt}"


def test_transponer_cambia_los_acordes(page, live_server, api):
    _crear_y_abrir(page, live_server, api)
    acorde = page.locator(".chord-container, .chord-pill").first
    original = acorde.inner_text().strip()
    page.click("#btn-key-up")  # +1 semitono
    page.wait_for_timeout(150)
    nuevo = acorde.inner_text().strip()
    assert nuevo != original, f"el acorde no cambió al transponer ({original})"
    assert page.inner_text("#key-value") in ("+1", "1")
