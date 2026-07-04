"""
E2E T-139 — Escenario más espectacular (solo CSS).

El Modo Directo (`.stage-mode`) gana realce: líneas inactivas más apagadas, acordes con más presencia
y la bolita de progreso pulsando. El motor (sync_engine/score_render) no se toca; respeta reduced-motion.
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def test_escenario_realce_y_bolita_pulsante(page, live_server, api):
    wipe_songs(api)
    sid = api.post("/songs/", json=sample_song_payload(title="Cancion Escena")).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)

    page.click("#btn-stage")
    assert "stage-mode" in (page.get_attribute("body", "class") or "")

    # La bolita de progreso pulsa en escenario (CSS determinista).
    dot_anim = page.evaluate(
        "() => getComputedStyle(document.getElementById('song-progress-dot')).animationName")
    assert dot_anim == "stage-dot-pulse"

    # Reproducir un poco para tener línea activa e inactivas, y comprobar el apagado fuerte.
    # Apagamos la cuenta atrás (default 4, T-V5-08) para que el motor arranque ya.
    for _ in range(3):
        if page.inner_text("#btn-countin") == "–":
            break
        page.click("#btn-countin")
    page.locator("#score-container").click()
    page.click("#btn-play-pause")
    page.wait_for_timeout(700)
    page.click("#btn-play-pause")
    op = page.evaluate("""() => {
        const inact = document.querySelector('.stage-mode .line-lyric.inactive');
        return inact ? parseFloat(getComputedStyle(inact).opacity) : null;
    }""")
    if op is not None:
        assert op < 0.3, f"las líneas inactivas no se apagan en escenario: {op}"
