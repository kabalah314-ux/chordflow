"""
E2E T-137 — Microinteracciones (pop) con propósito y respetando reduced-motion.

`bfPop(el)` (util.js) aplica la clase `.bf-pop` (keyframes en design-system.css) para premiar una
acción. Con `prefers-reduced-motion: reduce` no anima.
"""

import pytest

pytestmark = pytest.mark.e2e

_PROBE = """() => {
    const d = document.createElement('div');
    d.className = 'bf-pop';
    document.body.appendChild(d);
    return getComputedStyle(d).animationName;
}"""


def test_microinteraccion_pop_y_reduced_motion(page, live_server):
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    assert page.evaluate("typeof bfPop") == "function"

    # Un nodo con .bf-pop anima con el keyframe 'bf-pop'.
    assert page.evaluate(_PROBE) == "bf-pop"

    # Con prefers-reduced-motion: reduce, no anima.
    page.emulate_media(reduced_motion="reduce")
    assert page.evaluate(_PROBE) == "none"
