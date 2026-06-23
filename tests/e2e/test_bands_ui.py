"""
E2E del núcleo de banda (Fase 7, T-055): crear banda, verme como Admin con mi nombre de perfil,
generar enlace de invitación y previsualizarlo; y editar el perfil.
"""

import pytest

from tests.conftest import sample_song_payload

pytestmark = pytest.mark.e2e


def test_crear_banda_ver_miembro_y_generar_invitacion(page, live_server, api):
    # Mi perfil con nombre real → debe verse en la lista de miembros (no el UUID)
    api.put("/profile/me", json={"display_name": "Oscar E2E"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")

    # Crear banda vía promptModal
    page.click("#btn-new-band")
    page.wait_for_selector('.modal-overlay input[data-act="input"]', timeout=8000)
    page.fill('.modal-overlay input[data-act="input"]', "Banda E2E")
    page.click('.modal-overlay button[data-act="ok"]')

    # Crear banda lleva al espacio de banda (band.html) con su banner
    page.wait_for_url("**/band.html**", timeout=8000)
    page.wait_for_selector(".bf-band-banner", timeout=8000)
    banner = page.inner_text(".bf-band-banner")
    assert "Banda E2E" in banner
    assert "Admin" in banner                # soy admin (creador)

    # Miembros: mi nombre real, no el UUID
    page.click('.bf-tab[data-tab="miembros"]')
    assert "Oscar E2E" in page.inner_text('.bs-panel[data-panel="miembros"]')

    # Generar invitación → modal con el enlace join.html?code=
    page.click("#bs-invite")
    page.wait_for_selector(".modal-overlay input.search-box", timeout=8000)
    link = page.input_value(".modal-overlay input.search-box")
    assert "join.html?code=" in link
    page.click('.modal-overlay button[data-act="ok"]')

    # Previsualizar el enlace de invitación: muestra el nombre de la banda y es válida
    code = link.split("code=", 1)[1]
    page.goto(live_server + f"/static/join.html?code={code}", wait_until="networkidle")
    page.wait_for_selector("#join-accept", timeout=8000)
    assert "Banda E2E" in page.inner_text("#join-box")


def test_join_sin_codigo_ofrece_salida(page, live_server, api):
    # Abrir join.html sin ?code= no debe dejar al usuario atrapado: muestra el aviso
    # y un enlace explícito de salida hacia "Mis bandas" (coherencia de navegación).
    page.goto(live_server + "/static/join.html", wait_until="networkidle")
    page.wait_for_selector('#join-box a[href="bands.html"]', timeout=8000)
    assert "Enlace inválido" in page.inner_text("#join-box")
    assert "Ir a mis bandas" in page.inner_text("#join-box")


def test_volver_a_la_lista_muestra_la_banda(page, live_server, api):
    # Crea una banda por API y comprueba que aparece en la rejilla "Mis bandas"
    api.post("/bands/", json={"name": "Banda Listada"})
    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    assert "Banda Listada" in page.inner_text("#bands-grid")


def test_copiar_cancion_personal_al_repertorio_de_banda(page, live_server, api):
    # Una canción personal y una banda (vía API, como TEST_USER admin)
    api.post("/songs/", json=sample_song_payload(title="Tema Personal"))
    api.post("/bands/", json={"name": "Banda Repertorio"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    # Abrir la banda "Banda Repertorio" → band.html, pestaña Repertorio
    page.click('.song-card:has-text("Banda Repertorio") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="repertorio"]')
    page.wait_for_selector("#b-add-song", timeout=8000)

    # Copiar del repertorio personal
    page.click("#b-add-song")
    page.wait_for_selector("#copy-list button[data-id]", timeout=8000)
    page.click('#copy-list button:has-text("Tema Personal")')

    # La canción aparece en el repertorio de la banda
    page.wait_for_selector('#b-repertoire .setlist-song', timeout=8000)
    assert "Tema Personal" in page.inner_text("#b-repertoire")


def test_crear_setlist_de_banda_desde_la_ui(page, live_server, api):
    # Banda con una canción en el repertorio (vía API como admin)
    bid = api.post("/bands/", json={"name": "Banda Con Setlist"}).json()["id"]
    api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Cancion Repertorio"))

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Con Setlist") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="setlists"]')
    page.wait_for_selector("#b-new-setlist", timeout=8000)

    # Crear setlist desde el repertorio
    page.click("#b-new-setlist")
    page.wait_for_selector("#sl-name", timeout=8000)
    page.fill("#sl-name", "Bolo UI")
    page.click('#sl-available button[data-id]')          # añadir la canción
    page.wait_for_function("document.querySelectorAll('#sl-selected li button[data-rm]').length === 1",
                           timeout=5000)
    page.click("#sl-save")

    # Vuelve a la ficha y el setlist aparece
    page.wait_for_selector("#b-setlists .setlist-song", timeout=8000)
    assert "Bolo UI" in page.inner_text("#b-setlists")


def test_crear_repertorio_coleccion_y_anadir_cancion(page, live_server, api):
    """Repertorios (colecciones temáticas, T-114): crear un repertorio nombrado y añadirle una canción
    del repertorio de la banda; diferenciado de los setlists (pestaña 'Repertorios')."""
    bid = api.post("/bands/", json={"name": "Banda Repertorios"}).json()["id"]
    api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Cancion Col"))

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Repertorios") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="repertorio"]')
    page.wait_for_selector("#b-new-collection", timeout=8000)

    # Crear un repertorio (colección) por nombre vía el modal
    page.click("#b-new-collection")
    page.wait_for_selector(".modal-overlay input", timeout=8000)
    page.fill(".modal-overlay input", "Acústico")
    page.click('.modal-overlay button[data-act="ok"]')

    # Aparece en la lista de repertorios; lo abrimos y le añadimos la canción del repertorio
    page.wait_for_selector('#b-collections .setlist-song:has-text("Acústico")', timeout=8000)
    page.click('#b-collections .setlist-song:has-text("Acústico") button[data-act="open"]')
    page.wait_for_selector("#col-available button[data-add]", timeout=8000)
    page.click("#col-available button[data-add]")

    # La canción queda DENTRO de la colección
    page.wait_for_selector("#col-songs .setlist-song", timeout=8000)
    assert "Cancion Col" in page.inner_text("#col-songs")


def test_crear_setlist_desde_una_coleccion(page, live_server, api):
    """Pulido T-114: desde una colección se genera un setlist (orden de bolo) con sus canciones →
    cierra el bucle Repertorio→Setlist."""
    bid = api.post("/bands/", json={"name": "Banda Col2SL"}).json()["id"]
    s1 = api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="C2SL-A")).json()["id"]
    s2 = api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="C2SL-B")).json()["id"]
    api.post(f"/bands/{bid}/collections/", json={"name": "Acustico", "song_ids": [s1, s2]})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Col2SL") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="repertorio"]')
    page.wait_for_selector('#b-collections .setlist-song:has-text("Acustico")', timeout=8000)
    page.click('#b-collections .setlist-song:has-text("Acustico") button[data-act="open"]')

    # Generar un setlist desde la colección (acepta el nombre prerrelleno)
    page.wait_for_selector("#col-to-setlist", timeout=8000)
    page.click("#col-to-setlist")
    page.wait_for_selector(".modal-overlay input", timeout=4000)
    page.click('.modal-overlay button[data-act="ok"]')

    # El setlist aparece en la pestaña Setlists
    page.click('.bf-tab[data-tab="setlists"]')
    page.wait_for_selector('#b-setlists .setlist-song:has-text("Acustico")', timeout=8000)
    assert "Acustico" in page.inner_text("#b-setlists")


def test_concierto_con_booking_contacto_y_cache(page, live_server, api):
    """Booking (T-115): al crear un CONCIERTO aparecen los campos de booking; el caché + contacto se
    guardan y se muestran discretamente en la agenda (no en ensayos)."""
    api.post("/bands/", json={"name": "Banda Booking"})
    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Booking") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector("#b-new-event", timeout=8000)

    page.click("#b-new-event")
    page.wait_for_selector("#ev-title", timeout=8000)
    # Los campos de booking solo aparecen al elegir "Concierto"
    page.select_option("#ev-type", "concert")
    page.wait_for_selector("#ev-fee", state="visible", timeout=4000)
    page.fill("#ev-title", "Bolo con cache")
    page.fill("#ev-date", "2027-05-01T22:00")
    page.fill("#ev-contact", "Promotor Test")
    page.fill("#ev-fee", "300")
    page.click('.modal-overlay button[data-act="ok"]')

    # En la agenda el concierto muestra la línea de booking con el caché y el contacto
    booking_sel = '#b-agenda .setlist-song:has-text("Bolo con cache") .ev-booking'
    page.wait_for_selector(booking_sel, timeout=8000)
    booking = page.inner_text(booking_sel)
    assert "300" in booking and "Promotor Test" in booking


def test_sala_venue_reutilizable_en_concierto(page, live_server, api):
    """Salas reutilizables (T-116): una sala de la banda se enlaza a un concierto y se ve en la agenda
    (📍) y en la sección Salas."""
    bid = api.post("/bands/", json={"name": "Banda Venue"}).json()["id"]
    vid = api.post(f"/bands/{bid}/venues/",
                   json={"name": "Sala Apolo", "city": "Barcelona", "capacity": 600}).json()["id"]

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Venue") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="agenda"]')
    # La sala aparece en la sección "Salas"
    page.wait_for_selector('#b-venues .setlist-song:has-text("Sala Apolo")', timeout=8000)

    # Crear un concierto con esa sala
    page.click("#b-new-event")
    page.wait_for_selector("#ev-title", timeout=8000)
    page.select_option("#ev-type", "concert")
    page.wait_for_selector("#ev-venue", state="visible", timeout=4000)
    page.fill("#ev-title", "Bolo con sala")
    page.select_option("#ev-venue", value=vid)
    page.click('.modal-overlay button[data-act="ok"]')

    # El concierto muestra la sala (📍) en la agenda
    sel = '#b-agenda .setlist-song:has-text("Bolo con sala") .ev-booking'
    page.wait_for_selector(sel, timeout=8000)
    assert "Sala Apolo" in page.inner_text(sel)


def test_editar_sala_desde_la_ui(page, live_server, api):
    """Editar una sala desde la UI (Fase 14, completa T-116): el botón ✏️ abre el modal con los datos
    prerrellenados y al guardar hace PATCH → la sala se renombra y actualiza en la sección Salas."""
    bid = api.post("/bands/", json={"name": "Banda EditSala"}).json()["id"]
    api.post(f"/bands/{bid}/venues/",
             json={"name": "Sala Vieja", "city": "Madrid", "capacity": 200})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda EditSala") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector('#b-venues .setlist-song:has-text("Sala Vieja")', timeout=8000)

    # Abrir el editor de la sala → el modal viene prerrellenado
    page.click('#b-venues .setlist-song:has-text("Sala Vieja") button[data-act="edit"]')
    page.wait_for_selector("#v-name", timeout=4000)
    assert page.input_value("#v-name") == "Sala Vieja"
    page.fill("#v-name", "Sala Nueva")
    page.fill("#v-city", "Barcelona")
    page.click('.modal-overlay button[data-act="ok"]')

    # PATCH aplicado y lista recargada: nuevo nombre/ciudad, el viejo ya no está
    page.wait_for_selector('#b-venues .setlist-song:has-text("Sala Nueva")', timeout=8000)
    assert "Sala Vieja" not in page.inner_text("#b-venues")
    assert "Barcelona" in page.inner_text('#b-venues .setlist-song:has-text("Sala Nueva")')


def test_setlist_de_banda_con_apunte_por_cancion(page, live_server, api):
    """End-to-end del apunte por canción (T-110): el editor de setlist permite una nota por canción,
    se guarda y el reproductor la muestra en la barra del setlist."""
    bid = api.post("/bands/", json={"name": "Banda Apunte UI"}).json()["id"]
    api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Cancion Apunte"))

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Apunte UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="setlists"]')
    page.wait_for_selector("#b-new-setlist", timeout=8000)

    page.click("#b-new-setlist")
    page.wait_for_selector("#sl-name", timeout=8000)
    page.fill("#sl-name", "Bolo con apuntes")
    page.click('#sl-available button[data-id]')                 # añadir la canción
    page.wait_for_selector('#sl-selected .sl-note', timeout=5000)
    page.fill('#sl-selected .sl-note', "Capo 2 acustica")       # apunte por canción
    page.click("#sl-save")
    page.wait_for_selector("#b-setlists .setlist-song", timeout=8000)

    # La nota se persistió (verificado vía API)
    sid = next(s["id"] for s in api.get(f"/bands/{bid}/setlists/").json() if s["name"] == "Bolo con apuntes")
    detail = api.get(f"/bands/{bid}/setlists/{sid}").json()
    assert detail["items"][0]["note"] == "Capo 2 acustica"

    # El reproductor muestra el apunte en la barra del setlist
    song_id = detail["items"][0]["song_id"]
    page.goto(f"{live_server}/static/index.html?songId={song_id}&setlist={sid}&pos=0",
              wait_until="networkidle")
    page.wait_for_selector("#setlist-nav .sl-nav-note", timeout=8000)
    assert "Capo 2" in page.inner_text("#setlist-nav .sl-nav-note")


def test_editar_setlist_de_banda(page, live_server, api):
    """Editar un setlist existente desde la UI: el botón ✏️ abre el editor PRERRELLENADO (nombre +
    canciones + notas) y al guardar hace PATCH → cambia el nombre y la nota."""
    bid = api.post("/bands/", json={"name": "Banda EditSL"}).json()["id"]
    song = api.post(f"/bands/{bid}/songs/", json=sample_song_payload(title="Cancion SL")).json()
    sid = api.post(f"/bands/{bid}/setlists/",
                   json={"name": "Setlist Original",
                         "items": [{"song_id": song["id"], "note": "nota vieja"}]}).json()["id"]

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda EditSL") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="setlists"]')
    page.wait_for_selector('#b-setlists .setlist-song:has-text("Setlist Original")', timeout=8000)

    # Abrir el editor del setlist → viene prerrellenado (nombre + canción + nota)
    page.click('#b-setlists .setlist-song:has-text("Setlist Original") button[data-act="edit"]')
    page.wait_for_selector("#sl-name", timeout=8000)
    assert page.input_value("#sl-name") == "Setlist Original"
    page.wait_for_selector('#sl-selected .sl-note', timeout=5000)
    assert page.input_value('#sl-selected .sl-note') == "nota vieja"

    # Cambiar nombre y nota, guardar (PATCH)
    page.fill("#sl-name", "Setlist Editado")
    page.fill('#sl-selected .sl-note', "nota nueva")
    page.click("#sl-save")
    page.wait_for_selector('#b-setlists .setlist-song:has-text("Setlist Editado")', timeout=8000)

    # Persistió vía PATCH (nombre + nota), sin duplicar el setlist
    detail = api.get(f"/bands/{bid}/setlists/{sid}").json()
    assert detail["name"] == "Setlist Editado"
    assert detail["items"][0]["note"] == "nota nueva"
    assert len(api.get(f"/bands/{bid}/setlists/").json()) == 1


def test_crear_evento_y_marcar_asistencia_en_la_ui(page, live_server, api):
    api.post("/bands/", json={"name": "Banda Agenda UI"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Agenda UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector("#b-new-event", timeout=8000)

    # Crear un ensayo con fecha futura
    page.click("#b-new-event")
    page.wait_for_selector("#ev-title", timeout=8000)
    page.fill("#ev-title", "Ensayo UI")
    page.fill("#ev-date", "2027-01-15T20:00")
    page.click('.modal-overlay button[data-act="ok"]')

    # Aparece en la agenda y puedo marcar "Voy"
    page.wait_for_selector('#b-agenda .setlist-song', timeout=8000)
    assert "Ensayo UI" in page.inner_text("#b-agenda")
    page.click('#b-agenda .setlist-song:has-text("Ensayo UI") button[data-att="yes"]')
    page.wait_for_selector('#b-agenda .setlist-song button[data-att="yes"].active', timeout=8000)


def test_agenda_muestra_quien_ha_confirmado(page, live_server, api):
    """Cada evento muestra de forma discreta quién ha confirmado asistencia (#4): al marcar 'Voy'
    aparece una línea `.ev-attendees` con el ✅ y mi nombre. El backend la surte en la lista de
    eventos (no solo en el detalle)."""
    api.post("/bands/", json={"name": "Banda Confirmados"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Confirmados") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector("#b-new-event", timeout=8000)

    # Crear un evento y, antes de responder, NO debe haber línea de confirmados (sin ruido).
    page.click("#b-new-event")
    page.wait_for_selector("#ev-title", timeout=8000)
    page.fill("#ev-title", "Bolo confirmados")
    page.fill("#ev-date", "2027-03-10T21:00")
    page.click('.modal-overlay button[data-act="ok"]')
    song = '#b-agenda .setlist-song:has-text("Bolo confirmados")'
    page.wait_for_selector(song, timeout=8000)
    assert page.locator(song + " .ev-attendees").count() == 0

    # Al marcar "Voy", aparece la línea discreta con el ✅.
    page.click(song + ' button[data-att="yes"]')
    page.wait_for_selector(song + " .ev-attendees", timeout=8000)
    assert "✅" in page.inner_text(song + " .ev-attendees")


def test_registrar_movimiento_y_ver_saldos_en_la_ui(page, live_server, api):
    api.post("/bands/", json={"name": "Banda Finanzas UI"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Finanzas UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="finanzas"]')
    page.wait_for_selector("#b-new-tx", timeout=8000)

    # Registrar un gasto de 100 € pagado por mí (único miembro → me lo debo a mí, saldo 0)
    page.click("#b-new-tx")
    page.wait_for_selector("#tx-amount", timeout=8000)
    page.fill("#tx-desc", "Local de ensayo")
    page.fill("#tx-amount", "100")
    page.click('.modal-overlay button[data-act="ok"]')

    # El movimiento aparece en la lista de finanzas
    page.wait_for_selector('#b-tx-list .setlist-song', timeout=8000)
    assert "Local de ensayo" in page.inner_text("#b-finance")


def test_reparto_personalizado_en_movimiento(page, live_server, api):
    """El modal de movimiento permite reparto PERSONALIZADO: al elegirlo aparece una fila por
    miembro, se prerrellena al total y la suma se valida (✓); al registrar se envían `splits` que
    el backend acepta. (El backend ya soportaba splits; faltaba exponerlo en la UI — T-106.)"""
    api.post("/bands/", json={"name": "Banda Split UI"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Split UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="finanzas"]')
    page.wait_for_selector("#b-new-tx", timeout=8000)

    page.click("#b-new-tx")
    page.wait_for_selector("#tx-amount", timeout=8000)
    page.fill("#tx-desc", "Furgoneta")
    page.fill("#tx-amount", "90")
    # Pasar a reparto personalizado → aparece una fila por miembro (aquí 1: yo), prerrellenada al total
    page.select_option("#tx-split-mode", "custom")
    page.wait_for_selector("#tx-splits .split-amount", timeout=4000)
    assert page.input_value("#tx-splits .split-amount") == "90.00"  # prerrelleno al total
    assert "✓" in page.inner_text("#tx-split-sum")                   # la suma cuadra

    page.click('.modal-overlay button[data-act="ok"]')
    page.wait_for_selector('#b-tx-list .setlist-song', timeout=8000)
    assert "Furgoneta" in page.inner_text("#b-finance")             # el movimiento con splits se registró


def test_hilo_de_discusion_por_evento(page, live_server, api):
    """Cada evento de la agenda abre su HILO de discusión (mensajes con event_id): se publica en el
    hilo y aparece allí. El backend ya soportaba `?event_id=`; faltaba exponerlo en la UI (T-107)."""
    r = api.post("/bands/", json={"name": "Banda Hilo UI"})
    bid = r.json()["id"]
    api.post(f"/bands/{bid}/events/", json={"type": "rehearsal", "title": "Ensayo del jueves"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Hilo UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector('#b-agenda .setlist-song', timeout=8000)

    # Abrir el hilo del evento y publicar un mensaje
    page.click('#b-agenda .setlist-song:has-text("Ensayo del jueves") button[data-act="thread"]')
    page.wait_for_selector("#thread-input", timeout=8000)
    page.fill("#thread-input", "¿Llevamos el ampli grande?")
    page.click('.modal-overlay button[data-act="send"]')
    page.wait_for_selector('#thread-list .setlist-song', timeout=8000)
    assert "ampli grande" in page.inner_text("#thread-list")


def test_ligar_movimiento_a_evento(page, live_server, api):
    """El modal de movimiento permite ligar el gasto/ingreso a un evento de la banda; queda asociado
    (event_id) y la etiqueta del evento se muestra en el movimiento. El backend ya validaba event_id
    (Fase 11); faltaba exponerlo en la UI (T-108)."""
    r = api.post("/bands/", json={"name": "Banda Evento UI"})
    bid = r.json()["id"]
    api.post(f"/bands/{bid}/events/", json={"type": "concert", "title": "Bolo del sabado"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Evento UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="finanzas"]')
    page.wait_for_selector("#b-new-tx", timeout=8000)

    page.click("#b-new-tx")
    page.wait_for_selector("#tx-event", timeout=8000)   # selector de evento (tras cargar eventos)
    page.fill("#tx-desc", "Gasolina furgoneta")
    page.fill("#tx-amount", "60")
    page.select_option("#tx-event", label="Bolo del sabado")
    page.click('.modal-overlay button[data-act="ok"]')

    page.wait_for_selector('#b-tx-list .setlist-song', timeout=8000)
    fin = page.inner_text("#b-finance")
    assert "Gasolina furgoneta" in fin
    assert "Bolo del sabado" in fin   # la etiqueta del evento ligado se muestra


def test_exportar_finanzas_csv(page, live_server, api):
    """Las finanzas se exportan a CSV en el cliente: el botón descarga un CSV con cabecera y los
    movimientos (T-109; export client-side, sin backend)."""
    r = api.post("/bands/", json={"name": "Banda CSV UI"})
    bid = r.json()["id"]
    api.post(f"/bands/{bid}/transactions",
             json={"type": "expense", "description": "Cuerdas nuevas", "amount": "12.00", "paid_by_fund": True})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda CSV UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="finanzas"]')
    page.wait_for_selector('#b-export-csv', timeout=8000)

    with page.expect_download() as dl_info:
        page.click("#b-export-csv")
    download = dl_info.value
    assert download.suggested_filename.endswith(".csv")
    with open(download.path(), encoding="utf-8-sig") as f:
        content = f.read()
    assert "Importe" in content          # fila de cabecera
    assert "Cuerdas nuevas" in content   # el movimiento exportado


def test_booking_pipeline_cambiar_estado_de_evento(page, live_server, api):
    """Pipeline de booking (Fase 14, T-111): un evento se crea con estado del funnel (lead) y el admin
    lo mueve por el pipeline (Event.status) desde la agenda; el badge refleja el nuevo estado."""
    bid = api.post("/bands/", json={"name": "Banda Booking UI"}).json()["id"]
    api.post(f"/bands/{bid}/events/", json={"type": "concert", "title": "Sala Apolo", "status": "lead"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Booking UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector('#b-agenda .setlist-song', timeout=8000)

    fila = '#b-agenda .setlist-song:has-text("Sala Apolo")'
    assert "Lead" in page.inner_text(fila)                       # badge inicial del funnel
    page.select_option(f'{fila} .ev-status-sel', "confirmed")    # mover por el pipeline (admin)
    page.wait_for_selector(f'{fila} .ev-status--confirmed', timeout=8000)
    assert "Confirmado" in page.inner_text(fila)


def test_recordatorios_agenda_pronto_y_booking(page, live_server, api):
    """Recordatorios in-app (T-112): un evento en los próximos 7 días muestra '⏰ Pronto' y la agenda
    resume cuántos eventos siguen en el funnel de booking sin confirmar. Todo cliente, sin email."""
    from datetime import datetime, timedelta, timezone
    bid = api.post("/bands/", json={"name": "Banda Recordatorios UI"}).json()["id"]
    manana = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    api.post(f"/bands/{bid}/events/",
             json={"type": "concert", "title": "Concierto Pronto", "starts_at": manana, "status": "confirmed"})
    api.post(f"/bands/{bid}/events/", json={"type": "concert", "title": "Posible Bolo", "status": "lead"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Recordatorios UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="agenda"]')
    page.wait_for_selector('#b-agenda .setlist-song', timeout=8000)

    agenda = page.inner_text("#b-agenda")
    assert "Pronto" in agenda                       # recordatorio de evento próximo (≤7 días)
    assert "en booking sin confirmar" in agenda     # resumen del funnel de booking


def test_enviar_mensaje_en_el_chat_de_banda(page, live_server, api):
    api.post("/bands/", json={"name": "Banda Chat UI"})

    page.goto(live_server + "/static/bands.html", wait_until="networkidle")
    page.wait_for_selector(".song-card", timeout=8000)
    page.click('.song-card:has-text("Banda Chat UI") .card-main[data-act="open"]')
    page.wait_for_url("**/band.html**", timeout=8000)
    page.click('.bf-tab[data-tab="chat"]')
    page.wait_for_selector("#chat-input", timeout=8000)

    page.fill("#chat-input", "Hola equipo desde la UI")
    page.click("#chat-send")

    page.wait_for_selector('#b-chat .setlist-song', timeout=8000)
    assert "Hola equipo desde la UI" in page.inner_text("#b-chat")


def test_editar_perfil_persiste(page, live_server, api):
    page.goto(live_server + "/static/profile.html", wait_until="networkidle")
    page.wait_for_selector("#pf-name", timeout=8000)
    page.fill("#pf-name", "Nombre Guardado")
    page.fill("#pf-inst", "guitarra, voz")
    page.click("#pf-save")
    # Recargar y comprobar persistencia
    page.goto(live_server + "/static/profile.html", wait_until="networkidle")
    page.wait_for_selector("#pf-name", timeout=8000)
    assert page.input_value("#pf-name") == "Nombre Guardado"
