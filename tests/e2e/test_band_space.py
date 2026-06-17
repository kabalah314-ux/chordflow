"""
E2E del espacio de banda con pestañas (Fase 13, T-075 — contexto BANDA, incrementos 1-3).

`band.html` monta, dentro del shell BandFlow, el banner de banda + pestañas que REUSAN las
funciones de sección de `bands.js` (repertorio, setlists, agenda, finanzas, chat).
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_band_space_banner_y_pestanas(page, live_server, api):
    api.put("/profile/me", json={"display_name": "Oscar E2E"})
    bid = api.post("/bands/", json={"name": "Banda Pestañas"}).json()["id"]

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.wait_for_selector(".bf-band-banner", timeout=8000)
    banner = page.inner_text(".bf-band-banner")
    assert "Banda Pestañas" in banner
    assert "Admin" in banner                       # soy admin (creador), badge de rol

    # Las 6 pestañas reutilizadas están
    tabs = page.inner_text(".bf-tabs")
    for label in ("Miembros", "Repertorio", "Setlists", "Agenda", "Finanzas", "Chat"):
        assert label in tabs, f"falta la pestaña {label}"

    # Miembros muestra mi nombre real, no el UUID
    page.click('.bf-tab[data-tab="miembros"]')
    assert "Oscar E2E" in page.inner_text('.bs-panel[data-panel="miembros"]')


def test_band_space_pestana_reusa_repertorio(page, live_server, api):
    bid = api.post("/bands/", json={"name": "Banda Rep"}).json()["id"]
    api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Tema De Banda"))

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.wait_for_selector(".bf-tabs", timeout=8000)
    page.click('.bf-tab[data-tab="repertorio"]')
    # El loader reusado (loadRepertoire) pinta la canción en #b-repertoire
    page.wait_for_selector('#b-repertoire .setlist-song', timeout=8000)
    assert "Tema De Banda" in page.inner_text("#b-repertoire")
    assert page.locator("#b-add-song").count() == 1   # admin → botón copiar visible


def test_band_space_giras(page, live_server, api):
    """T-096 (V3-F5): la pestaña Giras lista/crea giras y abre su detalle (ruta + presupuesto)."""
    bid = api.post("/bands/", json={"name": "Banda Giras UI"}).json()["id"]
    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.wait_for_selector(".bf-tabs", timeout=8000)
    page.click('.bf-tab[data-tab="giras"]')
    page.wait_for_selector("#b-tours", timeout=8000)

    # Crear una gira con el botón + promptModal
    page.click("#b-new-tour")
    page.fill('.modal-overlay [data-act="input"]', "Gira Test UI")
    page.click('.modal-overlay [data-act="ok"]')

    # Aparece en la lista
    page.wait_for_selector("#b-tours .setlist-song", timeout=8000)
    assert "Gira Test UI" in page.inner_text("#b-tours")

    # Abrir el detalle: ruta + presupuesto, con el formulario de añadir parada (soy admin)
    page.click("#b-tours [data-tour]")
    page.wait_for_selector("#b-tour-detail #b-add-stop", timeout=8000)
    assert "Presupuesto" in page.inner_text("#b-tour-detail")


def test_band_space_id_invalido_muestra_error(page, live_server, api):
    # Una banda inexistente → la vista avisa con elegancia, no se rompe.
    page.goto(live_server + "/static/band.html?id=no-existe-1234", wait_until="networkidle")
    page.wait_for_selector("text=No se pudo abrir la banda", timeout=8000)
    assert page.locator('a[href="bands.html"]').count() >= 1   # salida a Mis bandas
