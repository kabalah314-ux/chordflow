"""
E2E T-V5-13 — Metrónomo standalone en la sección "Afinador / Metrónomo" (V5-F3, guía §4).

- La página tiene ambos paneles (afinador + metrónomo) y el nav refleja el nombre nuevo.
- BPM con +/− (persiste en el dispositivo) y compás seleccionable (persiste, redibuja los puntos).
- Tap-tempo actualiza el BPM (determinista vía clamps, como en test_js_logic).
- Iniciar/Parar arranca el bucle (AudioContext stubeado: sin audio real) y los puntos marcan el beat.
"""

import pytest

pytestmark = pytest.mark.e2e

# Sin audio real en el test: BfMetronome crea el AudioContext perezosamente en start().
AUDIO_STUB = """() => {
    window.AudioContext = function () {
        this.currentTime = 0; this.destination = {};
        this.createOscillator = () => ({ connect(){}, start(){}, stop(){}, frequency:{} });
        this.createGain = () => ({ connect(){}, gain:{ setValueAtTime(){},
                                   exponentialRampToValueAtTime(){} } });
    };
}"""


@pytest.fixture()
def metro(page, live_server):
    page.goto(live_server + "/static/afinador.html", wait_until="networkidle")
    page.evaluate(AUDIO_STUB)
    return page


def test_pagina_tiene_ambos_paneles_y_nav(metro):
    assert metro.is_visible("#tuner-panel")
    assert metro.is_visible("#metro-panel")
    assert "Metrónomo" in metro.inner_text("h1")
    # El item del menú pasa a "Afinador / Metrónomo" (guía §4).
    labels = metro.eval_on_selector_all(
        ".bf-sidebar a.bf-nav-item", "els => els.map(e => e.textContent)"
    )
    assert any("Metrónomo" in lbl for lbl in labels), f"nav sin 'Metrónomo': {labels}"


def test_bpm_sube_baja_y_persiste(metro):
    bpm0 = int(metro.inner_text("#metro-bpm"))
    metro.click("#metro-up")
    metro.click("#metro-up")
    metro.click("#metro-down")
    assert int(metro.inner_text("#metro-bpm")) == bpm0 + 1
    # Persiste al recargar (localStorage del dispositivo).
    metro.reload(wait_until="networkidle")
    assert int(metro.inner_text("#metro-bpm")) == bpm0 + 1


def test_compas_cambia_los_puntos_y_persiste(metro):
    assert metro.eval_on_selector_all(".metro-pip", "els => els.length") == 4  # 4/4 por defecto
    metro.select_option("#metro-meter", "6/8")
    assert metro.eval_on_selector_all(".metro-pip", "els => els.length") == 6
    metro.reload(wait_until="networkidle")
    assert metro.input_value("#metro-meter") == "6/8"
    assert metro.eval_on_selector_all(".metro-pip", "els => els.length") == 6


def test_tap_tempo_actualiza_el_bpm(metro):
    # Determinista vía clamp (como en test_js_logic): un intervalo de ~100 ms satura a 240.
    # Todo en UN evaluate para que no pase >2 s entre sembrar el tap y el clic (ventana del tap).
    metro.evaluate(
        """() => {
            bfMetro._taps = [performance.now() - 100];
            document.getElementById('metro-tap').click();
        }"""
    )
    assert int(metro.inner_text("#metro-bpm")) == 240


def test_iniciar_marca_el_beat_y_parar_detiene(metro):
    metro.click("#metro-start")
    assert metro.inner_text("#metro-start") == "Parar"
    metro.wait_for_selector(".metro-pip--on", timeout=3000)  # el bucle ilumina el beat activo
    assert metro.evaluate("bfMetro.running") is True
    metro.click("#metro-start")
    assert metro.inner_text("#metro-start") == "Iniciar"
    assert metro.evaluate("bfMetro.running") is False
    assert metro.eval_on_selector_all(".metro-pip--on", "els => els.length") == 0
