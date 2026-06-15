import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from ..services.auth import get_current_user
from ..services.importer import ImportError_, import_from_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["import"])


class ImportRequest(BaseModel):
    url: HttpUrl  # valida que sea http/https (422 si no)


class ImportResponse(BaseModel):
    raw_text: str


@router.post("/", response_model=ImportResponse)
def import_song(req: ImportRequest, user_id: str = Depends(get_current_user)):
    """Importar una partitura desde una URL con IA (T-045). Requiere auth. Devuelve el texto
    en el formato del editor para que el usuario lo revise antes de guardar."""
    try:
        raw_text = import_from_url(str(req.url))
        return ImportResponse(raw_text=raw_text)
    except ImportError_ as e:
        # Mensaje apto para el usuario (no filtra internals). 502: dependencia externa.
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error inesperado importando {req.url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al importar")
