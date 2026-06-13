"""Tests del proveedor de autenticación enchufable (T-043).

Verifican que:
- la factoría devuelve Supabase por defecto y falla (fail-fast) ante un nombre desconocido;
- `SupabaseAuthProvider` sin credenciales degrada a None (no revienta);
- el núcleo de `auth.py` es agnóstico: cambiar `_provider` cambia a quién valida, sin tocar
  la caché/TTL/degradación.
"""

import pytest

from src.services.auth_provider import (
    SupabaseAuthProvider,
    build_auth_provider,
)
from src.services.config import Settings

pytestmark = pytest.mark.unit


def test_factoria_supabase_por_defecto():
    provider = build_auth_provider(Settings())
    assert isinstance(provider, SupabaseAuthProvider)


def test_factoria_proveedor_desconocido_falla(monkeypatch):
    monkeypatch.setenv("CHORDFLOW_AUTH_PROVIDER", "no-existe")
    with pytest.raises(ValueError):
        build_auth_provider(Settings())


def test_supabase_sin_credenciales_devuelve_none():
    """Sin URL/anon key no se intenta la red: degrada a None (lo gestiona get_current_user)."""
    assert SupabaseAuthProvider(None, None).validate("tok") is None


def test_auth_es_agnostico_al_provider(monkeypatch):
    """`get_current_user` delega en `_provider.validate` vía `_validate_token`: inyectar otro
    proveedor cambia el user_id sin tocar la lógica de caché (T-043)."""
    from src.services import auth

    monkeypatch.setattr(auth, "TEST_MODE", False)
    auth._token_cache.clear()

    class FakeProvider:
        def validate(self, token):
            return {"id": "fake-user-from-otro-provider"}

    monkeypatch.setattr(auth, "_provider", FakeProvider())
    assert auth.get_current_user("Bearer cualquiera") == "fake-user-from-otro-provider"
    auth._token_cache.clear()
