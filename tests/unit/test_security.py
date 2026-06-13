"""
Tests de seguridad transversal: CORS (T-004) y caché de validación de token (T-005).
Corren en proceso con TestClient (modo test).
"""

import pytest

pytestmark = pytest.mark.unit


def test_cors_restringe_origenes(client):
    """Solo los orígenes de CHORDFLOW_ALLOWED_ORIGINS reciben cabecera CORS (T-004).
    Default de test: http://127.0.0.1:8000 y http://localhost:8000."""
    # Origen permitido → la respuesta refleja ese origen
    r = client.get("/config", headers={"Origin": "http://127.0.0.1:8000"})
    assert r.headers.get("access-control-allow-origin") == "http://127.0.0.1:8000"

    # Origen NO permitido → no se emite cabecera CORS (un sitio de terceros no puede
    # usar credenciales contra la API)
    r = client.get("/config", headers={"Origin": "http://evil.example.com"})
    assert "access-control-allow-origin" not in r.headers


def test_validacion_de_token_se_cachea(monkeypatch):
    """Dos requests con el mismo token validan contra Supabase UNA sola vez (T-005)."""
    from src.services import auth

    monkeypatch.setattr(auth, "TEST_MODE", False)   # forzar validación real
    auth._token_cache.clear()

    calls = {"n": 0}

    def fake_validate(_token):
        calls["n"] += 1
        return {"id": "user-123"}

    monkeypatch.setattr(auth, "_validate_token_with_supabase", fake_validate)

    assert auth.get_current_user("Bearer abc") == "user-123"
    assert auth.get_current_user("Bearer abc") == "user-123"
    assert calls["n"] == 1   # solo se validó remotamente una vez


def test_token_en_cache_sobrevive_caida_de_supabase(monkeypatch):
    """Con una entrada en caché, si Supabase 'cae' la request sigue pasando (T-005)."""
    from src.services import auth

    monkeypatch.setattr(auth, "TEST_MODE", False)
    auth._token_cache.clear()

    # Primera validación OK → queda en caché
    monkeypatch.setattr(auth, "_validate_token_with_supabase", lambda _t: {"id": "u1"})
    assert auth.get_current_user("Bearer tok") == "u1"

    # Supabase cae (devuelve None) y forzamos caché caducada: degradación elegante
    auth._token_cache["tok"] = ("u1", 0.0)  # expirada
    monkeypatch.setattr(auth, "_validate_token_with_supabase", lambda _t: None)
    assert auth.get_current_user("Bearer tok") == "u1"

    # Sin caché y con Supabase caído → 401
    auth._token_cache.clear()
    with pytest.raises(Exception):
        auth.get_current_user("Bearer otro")


def test_token_cache_tiene_cota_de_tamano(monkeypatch):
    """La caché de tokens no crece sin límite (T-028)."""
    from src.services import auth

    monkeypatch.setattr(auth, "TEST_MODE", False)
    monkeypatch.setattr(auth, "TOKEN_CACHE_MAX", 5)
    auth._token_cache.clear()
    monkeypatch.setattr(auth, "_validate_token_with_supabase", lambda t: {"id": "u-" + t})

    for i in range(50):
        auth.get_current_user(f"Bearer tok{i}")

    assert len(auth._token_cache) <= 5
