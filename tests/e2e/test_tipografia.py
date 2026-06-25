"""
E2E T-149 — Cifras tabulares en los displays numéricos del reproductor.

Refinamiento tipográfico: los números (beat, BPM, tono) usan `font-variant-numeric: tabular-nums`
para que no "bailen" al cambiar de cifra.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_cifras_tabulares_en_el_reproductor(page, live_server, api):
    sid = api.post("/songs/", json=sample_song_payload(title="Tab Nums")).json()["id"]
    page.goto(live_server + f"/static/index.html?songId={sid}", wait_until="networkidle")
    page.wait_for_selector(".chord-container, .chord-pill", timeout=8000)
    fv = page.evaluate(
        "() => getComputedStyle(document.getElementById('current-beat-display')).fontVariantNumeric")
    assert "tabular-nums" in fv, f"el display de beat no usa cifras tabulares: {fv}"
