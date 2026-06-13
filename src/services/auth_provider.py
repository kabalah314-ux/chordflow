"""Proveedores de autenticación enchufables (T-043).

`auth.py` —la caché TTL, el lock de concurrencia y la degradación elegante (T-005/T-028)—
es **agnóstico al proveedor**: solo sabe pedir "valida este token y dame el usuario". Quién
habla con el backend de identidad concreto (Supabase hoy; otro mañana en el molde) es un
`AuthProvider`. Esto es lo que hace el núcleo de auth reutilizable fuera de ChordFlow.
"""

import json
import logging
import urllib.request
from typing import Protocol

logger = logging.getLogger(__name__)


class AuthProvider(Protocol):
    """Contrato mínimo de un proveedor de identidad."""

    def validate(self, token: str) -> dict | None:
        """Devuelve el dict del usuario (con al menos `id`) o None si el token no es válido."""
        ...


class SupabaseAuthProvider:
    """Valida tokens contra `GET /auth/v1/user` de Supabase (no requiere el JWT secret:
    usa la anon key y deja que el propio Supabase valide el bearer)."""

    def __init__(self, url: str | None, anon_key: str | None, timeout: float = 10.0):
        self._url = url
        self._anon_key = anon_key
        self._timeout = timeout

    def validate(self, token: str) -> dict | None:
        if not self._url or not self._anon_key:
            logger.error("Faltan SUPABASE_URL o SUPABASE_ANON_KEY en el entorno")
            return None
        try:
            req = urllib.request.Request(
                f"{self._url}/auth/v1/user",
                headers={
                    "apikey": self._anon_key,
                    "Authorization": f"Bearer {token}",
                },
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                if resp.status == 200:
                    return json.loads(resp.read())
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Token inválido o error validando con el proveedor: {e}")
        return None


def build_auth_provider(settings) -> AuthProvider:
    """Factoría: elige el proveedor según `settings.chordflow_auth_provider` (default supabase).
    Lanza `ValueError` ante un nombre desconocido (fail-fast al arrancar)."""
    name = (settings.chordflow_auth_provider or "supabase").lower()
    if name == "supabase":
        return SupabaseAuthProvider(settings.supabase_url, settings.supabase_anon_key)
    raise ValueError(f"Proveedor de auth desconocido: {name!r}")
