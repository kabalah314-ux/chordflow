"""
E2E T-V5-14 — Afinador 2.0 en la sección (V5-F3, guía §4).

- `bfFreqToNote` acepta la referencia A4 (435–445) y los cents cambian con ella (pura, sin micro).
- `bfTuneStatus` clasifica el desvío (ok/low/high) para el indicador grande.
- El selector "La4 =" persiste en el dispositivo y el indicador grande pinta el estado
  (vía el hook `bfTunerReadout`, sin micrófono — mismo espíritu que T-091).
"""

import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture()
def afinador(page, live_server):
    page.goto(live_server + "/static/afinador.html", wait_until="networkidle")
    return page


def test_freqtonote_con_referencia_a4(afinador):
    # Con la referencia por defecto (440), 440 Hz es La4 clavado.
    note = afinador.evaluate("() => bfFreqToNote(440)")
    assert note["name"] == "La" and note["octave"] == 4 and note["cents"] == 0
    # Con A4=442, 442 Hz es el nuevo La4 clavado…
    note442 = afinador.evaluate("() => bfFreqToNote(442, 442)")
    assert note442["name"] == "La" and note442["cents"] == 0
    # …y 440 Hz queda BAJO respecto a 442 (cents negativos).
    low = afinador.evaluate("() => bfFreqToNote(440, 442)")
    assert low["name"] == "La" and low["cents"] < 0


def test_tunestatus_clasifica(afinador):
    assert afinador.evaluate("bfTuneStatus(0)") == "ok"
    assert afinador.evaluate("bfTuneStatus(5)") == "ok"       # tolerancia ±5 cents
    assert afinador.evaluate("bfTuneStatus(-5)") == "ok"
    assert afinador.evaluate("bfTuneStatus(-6)") == "low"
    assert afinador.evaluate("bfTuneStatus(6)") == "high"


def test_selector_a4_persiste(afinador):
    assert afinador.input_value("#tuner-a4") == "440"
    afinador.select_option("#tuner-a4", "442")
    afinador.reload(wait_until="networkidle")
    assert afinador.input_value("#tuner-a4") == "442"


def test_indicador_grande_pinta_estado(afinador):
    # Sin micro: se pinta una lectura directa con el hook (como haría el bucle de detección).
    afinador.evaluate("bfTunerReadout(bfFreqToNote(440))")   # La4 clavado
    assert "Afinado" in afinador.inner_text("#tuner-status")
    assert "ok" in afinador.get_attribute("#tuner-status", "class")

    afinador.evaluate("bfTunerReadout(bfFreqToNote(430))")   # bajo respecto a La4
    assert "Bajo" in afinador.inner_text("#tuner-status")
    assert "low" in afinador.get_attribute("#tuner-status", "class")

    # La nota grande sigue mostrándose (y más grande en la sección: 3.8rem).
    assert afinador.inner_text("#tuner-note") != "—"
    size = afinador.evaluate(
        "() => getComputedStyle(document.getElementById('tuner-note')).fontSize"
    )
    assert float(size.replace("px", "")) > 50, f"nota pequeña en la sección: {size}"
