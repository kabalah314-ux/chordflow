"""
E2E de la biblioteca: estado vacío (L1), aparición de canción (L2), búsqueda (L3).
"""

import pytest

from tests.conftest import sample_song_payload, wipe_songs

pytestmark = pytest.mark.e2e


def test_estado_vacio(page, live_server, api):
    # La biblioteca es unificada (T-077): pueden quedar canciones de banda de otros tests.
    # El estado vacío de "Personales" muestra el onboarding cuando no tengo partituras propias.
    wipe_songs(api)
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector('.lib-filter[data-filter="personal"]', timeout=8000)
    page.click('.lib-filter[data-filter="personal"]')
    page.wait_for_selector(".empty-state", timeout=8000)
    assert "Aún no tienes partituras" in page.inner_text(".empty-state")


def test_cancion_aparece_como_tarjeta(page, live_server, api):
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Cancion Visible"))
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    assert "Cancion Visible" in page.inner_text("#song-grid")


def test_borrar_usa_modal_y_elimina(page, live_server, api):
    """Borrar abre un modal de confirmación propio (no `confirm()` nativo, T-017); al aceptar,
    la tarjeta desaparece."""
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Para Borrar"))
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)

    page.click('.card-action-btn[data-act="delete"]')
    # Aparece nuestro modal glassmorphism (no el confirm() del navegador).
    page.wait_for_selector(".modal-overlay .modal-card", timeout=4000)
    assert "Para Borrar" in page.inner_text(".modal-card")
    page.click('.modal-card [data-act="ok"]')

    # Tras borrar, la tarjeta desaparece (puede haber otras canciones de banda en el grid).
    page.wait_for_function(
        "!document.querySelector('#song-grid').innerText.includes('Para Borrar')", timeout=8000)
    assert "Para Borrar" not in page.inner_text("#song-grid")


def test_busqueda_filtra(page, live_server, api):
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Wonderwall"))
    api.post("/songs/", json=sample_song_payload(title="Creep"))
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)

    page.fill("#search-input", "wonder")
    page.wait_for_timeout(300)  # la búsqueda es en vivo (input event)
    grid = page.inner_text("#song-grid")
    assert "Wonderwall" in grid
    assert "Creep" not in grid


def test_biblioteca_unificada_filtra_por_banda(page, live_server, api):
    """La biblioteca une personales + repertorio de banda y filtra (T-077)."""
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Tema Personal Uni"))
    bid = api.post("/bands/", json={"name": "Banda Biblio"}).json()["id"]
    api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Tema De Banda Uni"))

    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector('.lib-filter[data-filter="personal"]', timeout=8000)

    # Todas: aparecen ambas, con la etiqueta de banda
    page.click('.lib-filter[data-filter="all"]')
    page.wait_for_selector('.song-card', timeout=8000)
    grid = page.inner_text("#song-grid")
    assert "Tema Personal Uni" in grid and "Tema De Banda Uni" in grid
    assert "Banda Biblio" in grid          # badge de fuente

    # Filtro por banda: solo el repertorio de esa banda
    page.click(f'.lib-filter[data-filter="{bid}"]')
    page.wait_for_function(
        "!document.querySelector('#song-grid').innerText.includes('Tema Personal Uni')", timeout=8000)
    assert "Tema De Banda Uni" in page.inner_text("#song-grid")

    # Filtro Personales: solo mis partituras
    page.click('.lib-filter[data-filter="personal"]')
    page.wait_for_function(
        "!document.querySelector('#song-grid').innerText.includes('Tema De Banda Uni')", timeout=8000)
    assert "Tema Personal Uni" in page.inner_text("#song-grid")


def test_coleccion_personal_en_la_biblioteca(page, live_server, api):
    """Crear una colección personal desde la Biblioteca, verla como chip y filtrar el grid por ella."""
    wipe_songs(api)
    api.post("/songs/", json=sample_song_payload(title="Tema Acustico Col"))
    api.post("/songs/", json=sample_song_payload(title="Tema Fuera Col"))

    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector('#library-collections [data-act="new-col"]', timeout=8000)

    # Crear la colección con SOLO una de las dos canciones
    page.click('#library-collections [data-act="new-col"]')
    page.wait_for_selector("#col-name", timeout=8000)
    page.fill("#col-name", "Acustico E2E")
    page.check('#col-picker label:has-text("Tema Acustico Col") input')
    page.click('.modal-overlay [data-act="ok"]')

    # Aparece el chip de la colección
    chip = '#library-collections [data-collection]:has-text("Acustico E2E")'
    page.wait_for_selector(chip, timeout=8000)

    # Al activarla, el grid muestra solo su canción (no la que quedó fuera)
    page.click(chip)
    page.wait_for_function(
        "!document.querySelector('#song-grid').innerText.includes('Tema Fuera Col')", timeout=8000)
    grid = page.inner_text("#song-grid")
    assert "Tema Acustico Col" in grid and "Tema Fuera Col" not in grid


def test_setlists_accesible_desde_la_biblioteca(page, live_server, api):
    """Los Setlists personales se alcanzan desde la Biblioteca (antes la página estaba huérfana) y la
    página ya se llama 'Setlists', no 'Repertorios'."""
    page.goto(live_server + "/static/library.html", wait_until="networkidle")
    page.wait_for_selector('a[href="setlists.html"]', timeout=8000)
    page.click('a[href="setlists.html"]')
    page.wait_for_url("**/setlists.html", timeout=8000)
    page.wait_for_selector("h1", timeout=8000)
    h1 = page.inner_text("h1")
    assert "Setlists" in h1 and "Repertorios" not in h1
