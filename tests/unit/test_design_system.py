"""
Test del sistema de diseño (Fase 13, T-073).

La fundación visual del giro V2 (`static/design-system.css`) se sirve correctamente y declara
los tokens y componentes base de los que dependerán el app shell (T-074) y el espacio de banda
(T-075). Es la "fuente única" de aspecto: si este archivo desaparece o pierde sus tokens, el
reskin se queda sin base.
"""

import pytest

pytestmark = pytest.mark.unit


def test_design_system_se_sirve(client):
    r = client.get("/static/design-system.css")
    assert r.status_code == 200
    assert "text/css" in r.headers["content-type"]


def test_design_system_declara_tokens_y_componentes(client):
    css = client.get("/static/design-system.css").text
    # Tokens clave (paleta, acento como perilla única, tema claro)
    for token in ("--bf-bg", "--bf-surface", "--bf-text", "--bf-primary"):
        assert token in css, f"falta el token {token}"
    assert '[data-theme="light"]' in css, "falta el tema claro"
    # Componentes base que usarán el shell y el espacio de banda
    for cls in (".bf-btn", ".bf-card", ".bf-nav-item", ".bf-tab", ".bf-band-banner", ".bf-badge"):
        assert cls in css, f"falta el componente {cls}"


def test_design_system_adopta_paleta_bandflow(client):
    """Fase A: los tokens están reescritos al look BandFlow (acento coral naranja,
    tokens translúcidos -weak/hover nuevos y tipografía IBM Plex). Si alguien revierte
    el acento a azul o quita los tokens nuevos, este test lo caza."""
    css = client.get("/static/design-system.css").text
    # Acento coral BandFlow (ya no el azul #6c8cff)
    assert "#ff6b4a" in css, "el acento no es el coral BandFlow"
    assert "#6c8cff" not in css, "quedó el azul antiguo en el acento"
    # Tokens nuevos introducidos en la Fase A
    for token in ("--bf-accent-weak", "--bf-hover", "--bf-success-weak",
                  "--bf-danger-weak", "--bf-warning-weak"):
        assert token in css, f"falta el token nuevo {token}"
    # Identidad tipográfica IBM Plex (UI + mono)
    assert "IBM Plex Sans" in css and "IBM Plex Mono" in css, "faltan las fuentes IBM Plex"


def test_design_system_tiene_estados_de_ui(client):
    """V3-F1 (T-084): el sistema de diseño cubre los estados que separan un demo de un
    producto — deshabilitado, cargando (spinner), skeleton, vista vacía y foco accesible.
    Si alguien los borra, las páginas pierden estos estados de golpe y este test lo caza."""
    css = client.get("/static/design-system.css").text
    # Deshabilitado en botones e inputs
    assert ".bf-btn:disabled" in css, "falta el estado deshabilitado de botón"
    assert ".bf-input:disabled" in css, "falta el estado deshabilitado de input"
    # Cargando: spinner + botón con [data-loading]
    assert ".bf-spinner" in css and "@keyframes bf-spin" in css, "falta el spinner de carga"
    assert '[data-loading="true"]' in css, "falta el estado de carga del botón"
    # Skeleton y empty state
    assert ".bf-skeleton" in css, "falta el skeleton de carga"
    assert ".bf-empty" in css, "falta la vista vacía (empty state)"
    # Foco accesible y datos numéricos en mono
    assert ":focus-visible" in css, "falta el foco accesible"
    assert ".bf-num" in css, "falta la utilidad de números en mono"
