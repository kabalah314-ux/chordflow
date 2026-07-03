"""
E2E T-V5-06 — Identidad con imágenes (fotos de perfil, logo y fondo de banda).

La SUBIDA real a Supabase Storage no se prueba (client-side, y en modo test no hay Supabase);
se siembra la URL por API (el contrato que guarda upload.js) y se verifica que la app la PINTA:
foto en el perfil y en el lateral, logo+fondo en el banner de banda y cara en los miembros.
"""

import pytest

from tests.conftest import wipe_bands

pytestmark = pytest.mark.e2e

# 1×1 px transparente servido por la propia app (sin red externa en los tests): cualquier
# https:// vale para el contrato; aquí basta con que el DOM lo referencie.
IMG = "https://example.com/media/uid/avatar-1.jpg"
COVER = "https://example.com/media/uid/band-cover-1.jpg"


def test_perfil_y_lateral_muestran_la_foto(page, live_server, api):
    wipe_bands(api)
    api.put("/profile/me", json={"display_name": "Ana Músico", "avatar_url": IMG})
    try:
        page.goto(live_server + "/static/profile.html", wait_until="networkidle")
        page.wait_for_selector(".pf-identity", timeout=8000)

        # Identidad del perfil: la foto sustituye a las iniciales.
        src = page.get_attribute(".pf-identity .bf-avatar--lg img.bf-avatar__img", "src")
        assert src == IMG
        # Botón de cambiar foto presente (la subida real necesita Supabase, fuera del modo test).
        assert page.is_visible("#pf-photo")
        # Lateral (shell): la tarjeta de perfil también pinta la foto.
        assert page.get_attribute("#bf-prof-initials img.bf-avatar__img", "src") == IMG
    finally:
        # El perfil PERSISTE entre tests: quitar la foto para no contaminar a quien asierte iniciales.
        api.put("/profile/me", json={"avatar_url": ""})


def test_banner_de_banda_con_logo_y_fondo(page, live_server, api):
    wipe_bands(api)
    bid = api.post("/bands/", json={"name": "Con Imagen"}).json()["id"]
    api.patch(f"/bands/{bid}", json={"avatar_url": IMG, "cover_url": COVER})

    page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
    page.wait_for_selector(".bf-band-banner", timeout=8000)

    # Logo dentro del círculo del banner.
    assert page.get_attribute(".bf-band-banner .bf-avatar--lg img.bf-avatar__img", "src") == IMG
    # Fondo aplicado como background-image con el velo (--cover).
    banner_cls = page.get_attribute(".bf-band-banner", "class")
    assert "bf-band-banner--cover" in banner_cls
    bg = page.evaluate("getComputedStyle(document.querySelector('.bf-band-banner')).backgroundImage")
    assert COVER in bg
    # Ajustes (admin): botones de logo y fondo presentes.
    page.click('.bf-tab[data-tab="ajustes"]')
    assert page.is_visible("#set-logo") and page.is_visible("#set-cover")


def test_miembros_con_avatar(page, live_server, api):
    wipe_bands(api)
    api.put("/profile/me", json={"display_name": "Ana Músico", "avatar_url": IMG})
    try:
        bid = api.post("/bands/", json={"name": "Con Caras"}).json()["id"]

        page.goto(live_server + f"/static/band.html?id={bid}", wait_until="networkidle")
        page.wait_for_selector(".bf-band-banner", timeout=8000)
        page.click('.bf-tab[data-tab="miembros"]')
        page.wait_for_selector("#b-members .bf-avatar", timeout=8000)
        assert page.get_attribute("#b-members .bf-avatar img.bf-avatar__img", "src") == IMG
    finally:
        api.put("/profile/me", json={"avatar_url": ""})


def test_iniciales_sin_parentesis(page, live_server, api):
    """Fix del repaso 2026-07-02: 'Oscar (tú)' → 'O', no 'O('."""
    page.goto(live_server + "/static/app.html", wait_until="networkidle")
    page.wait_for_selector(".bf-sidebar", timeout=8000)
    got = page.evaluate("initialsFrom('Oscar (tú)')")
    assert got == "O", got
    assert page.evaluate("initialsFrom('María José')") == "MJ"
