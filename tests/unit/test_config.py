"""Tests del objeto de configuración central `Settings` (T-016).

Verifican que pydantic-settings:
- lee el entorno con TIPOS (no strings sueltos): un int es int, un bool es bool;
- parsea `CHORDFLOW_ALLOWED_ORIGINS` (coma-separado) a lista limpia;
- VALIDA: un valor no convertible (TTL no numérico) revienta al arrancar, no en runtime.
"""

import pytest
from pydantic import ValidationError

from src.services.config import Settings, settings

pytestmark = pytest.mark.unit


def test_modo_test_activo_en_el_entorno_de_tests():
    """conftest fija CHORDFLOW_TEST_MODE=1 antes de importar la app → bool True."""
    assert settings.chordflow_test_mode is True


def test_origenes_cors_se_parsean_a_lista(monkeypatch):
    monkeypatch.setenv("CHORDFLOW_ALLOWED_ORIGINS", "http://a.com, http://b.com ,")
    s = Settings()
    assert s.allowed_origins_list == ["http://a.com", "http://b.com"]


def test_tipos_convertidos_desde_el_entorno(monkeypatch):
    monkeypatch.setenv("CHORDFLOW_TOKEN_TTL", "200")
    s = Settings()
    assert s.chordflow_token_ttl == 200
    assert isinstance(s.chordflow_token_ttl, int)


def test_valor_invalido_falla_al_arrancar(monkeypatch):
    """Un TTL no numérico debe fallar la validación al construir Settings (fail-fast),
    en vez de propagarse como un str a un `int(...)` en runtime."""
    monkeypatch.setenv("CHORDFLOW_TOKEN_TTL", "no-soy-un-numero")
    with pytest.raises(ValidationError):
        Settings()


def test_modo_test_rechaza_postgres_y_vercel(monkeypatch):
    """T-V6-02: el cerrojo impide activar el modo test fuera de SQLite/local."""
    monkeypatch.delenv("VERCEL", raising=False)
    with pytest.raises(ValidationError):
        Settings(chordflow_test_mode=True, database_url="postgresql://u:p@h:5432/db")
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(ValidationError):
        Settings(chordflow_test_mode=True, database_url="sqlite:///./x.db")
    monkeypatch.delenv("VERCEL", raising=False)
    assert Settings(chordflow_test_mode=True, database_url="sqlite:///./x.db").chordflow_test_mode


def test_produccion_sin_modo_test_arranca_con_postgres(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    s = Settings(chordflow_test_mode=False, database_url="postgresql://u:p@h:5432/db")
    assert s.chordflow_test_mode is False
