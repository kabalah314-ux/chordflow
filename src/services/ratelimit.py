"""Limitador de peticiones sencillo en memoria (T-V6-06).

Ventana deslizante por clave (`import:<user_id>`, `invite:<ip>`…). Vive en la memoria de cada
instancia serverless: no es global, pero corta el abuso básico sin dependencias. T-V6-74 lo
sustituye por uno persistente.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def check_rate(key: str, limit: int, window_s: int) -> None:
    """Lanza 429 si `key` ya hizo `limit` peticiones en los últimos `window_s` segundos."""
    now = time.monotonic()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - window_s:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(status_code=429,
                                detail="Demasiadas peticiones seguidas. Espera un momento.")
        q.append(now)


def reset() -> None:
    """Vacía el limitador (para tests)."""
    with _lock:
        _hits.clear()
