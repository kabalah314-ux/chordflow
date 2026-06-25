"""
E2E T-140 — Reordenar el setlist arrastrando (pointer events, sin librerías).

En el editor de setlist, arrastrar por el asa (⠿) reordena las canciones; al guardar, el nuevo orden
persiste (el PATCH/POST ya acepta el orden). Funciona con ratón y táctil (touch-action:none en el asa).
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_reordenar_setlist_arrastrando(page, live_server, api):
    a = api.post("/songs/", json=sample_song_payload(title="DnD Uno")).json()["id"]
    b = api.post("/songs/", json=sample_song_payload(title="DnD Dos")).json()["id"]

    page.goto(live_server + "/static/setlists.html", wait_until="networkidle")
    page.click("#btn-new-setlist")
    page.wait_for_selector("#sl-name", timeout=8000)
    page.fill("#sl-name", "DnD Setlist")
    page.click(f'#sl-available button[data-id="{a}"]')
    page.click(f'#sl-available button[data-id="{b}"]')
    page.wait_for_function(
        "document.querySelectorAll('#sl-selected .sl-sel-row').length === 2", timeout=5000)

    order0 = page.evaluate(
        "[...document.querySelectorAll('#sl-selected .sl-sel-row')].map(r => r.dataset.sid)")
    assert order0 == [a, b]

    # Arrastrar la 2ª fila (b) sobre la mitad superior de la 1ª (a) usando el asa.
    h = page.locator(f'#sl-selected .sl-sel-row[data-sid="{b}"] .sl-drag').bounding_box()
    t = page.locator(f'#sl-selected .sl-sel-row[data-sid="{a}"]').bounding_box()
    page.mouse.move(h["x"] + h["width"] / 2, h["y"] + h["height"] / 2)
    page.mouse.down()
    page.mouse.move(t["x"] + t["width"] / 2, t["y"] + t["height"] - 2, steps=3)
    page.mouse.move(t["x"] + t["width"] / 2, t["y"] + 2, steps=3)
    page.mouse.up()

    page.wait_for_function(
        f"[...document.querySelectorAll('#sl-selected .sl-sel-row')].map(r => r.dataset.sid)[0] === '{b}'",
        timeout=5000)

    # Guardar y comprobar que el orden persistió (b, a) vía API.
    page.click("#sl-save")
    page.wait_for_selector('.song-card:has-text("DnD Setlist")', timeout=8000)
    sid = next(s["id"] for s in api.get("/setlists/").json() if s["name"] == "DnD Setlist")
    order_saved = [it["song_id"] for it in api.get(f"/setlists/{sid}").json()["items"]]
    assert order_saved == [b, a], f"el orden no persistió: {order_saved}"
