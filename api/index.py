"""Entrypoint serverless para Vercel (@vercel/python).

Vercel sirve la app ASGI expuesta como `app`. Reutilizamos la misma app FastAPI de
`src.main` (no se duplica nada). El `vercel.json` enruta TODO el tráfico aquí.
"""

import sys
from pathlib import Path

# La raíz del repo (padre de api/) debe estar en sys.path para importar `src`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.main import app  # noqa: E402,F401  (lo usa Vercel como app ASGI)
