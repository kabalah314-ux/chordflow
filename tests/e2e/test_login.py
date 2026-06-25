"""
E2E T-147 — Login pulido.

El claim refleja la propuesta de gestión de banda (no el teleprompter viejo) y el botón de Google
está presente. (La página de login REDIRIGE en modo test —el usuario siempre está autenticado—, así
que se verifica sobre el HTML servido; el OAuth real se prueba en producción.)
"""

import urllib.request

import pytest

pytestmark = pytest.mark.e2e


def test_login_claim_y_google_en_html(live_server):
    html = urllib.request.urlopen(live_server + "/static/login.html").read().decode("utf-8")
    assert "Gestiona tu banda" in html                                  # claim de banda
    assert "Tus partituras, en cualquier dispositivo" not in html       # claim viejo retirado
    assert 'id="btn-google"' in html                                    # botón Google
    assert "design-system.css" in html                                  # tokens → modo oscuro coherente (T-120)
