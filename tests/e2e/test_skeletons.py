"""
E2E T-135 — Skeletons de carga en todas las listas.

`bfSkeletonList(n)` (util.js) genera n filas `.bf-skeleton--card`; las vistas de lista (biblioteca y
las agregadas agenda/finanzas/chat) lo pintan antes del fetch para dar sensación de respuesta inmediata.
"""

import pytest

pytestmark = pytest.mark.e2e


def test_bf_skeleton_list_helper(page, live_server):
    page.goto(live_server + "/static/agenda.html", wait_until="networkidle")
    assert page.evaluate("typeof bfSkeletonList") == "function"
    # n filas → n elementos .bf-skeleton--card (cada fila lleva además la clase base .bf-skeleton).
    n = page.evaluate("(bfSkeletonList(3).match(/bf-skeleton--card/g) || []).length")
    assert n == 3
    # Las filas son skeletons de verdad (clase base + tamaño de card).
    assert "bf-skeleton" in page.evaluate("bfSkeletonList(1)")
