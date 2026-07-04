import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl

from ..services.auth import get_current_user
from ..services.importer import (
    ImportError_,
    extract_chords_from_image,
    import_from_url,
    search_song,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["import"])


class ImportRequest(BaseModel):
    url: HttpUrl  # valida que sea http/https (422 si no)


class ImportResponse(BaseModel):
    raw_text: str


class PhotoRequest(BaseModel):
    image: str  # data URL: data:image/...;base64,... (ya redimensionada en el cliente)


class SearchResult(BaseModel):
    title: str
    artist: str = ""
    url: str
    source: str = ""


class SearchResponse(BaseModel):
    results: list[SearchResult]


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


@router.post("/photo", response_model=ImportResponse)
def import_photo(req: PhotoRequest, user_id: str = Depends(get_current_user)):
    """Foto de una hoja → partitura (T-V5-11, beta). Un modelo de visión gratuito transcribe la
    imagen al formato del editor para revisarla antes de guardar. Requiere auth."""
    try:
        raw_text = extract_chords_from_image(req.image)
        return ImportResponse(raw_text=raw_text)
    except ImportError_ as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error inesperado en foto→partitura: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al procesar la foto")


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, max_length=200), user_id: str = Depends(get_current_user)
):
    """Buscar una canción por nombre en CifraClub/LaCuerda (T-162). Requiere auth. Devuelve una
    preselección de candidatos (título/artista/url/origen) para elegir antes de importar."""
    try:
        results = search_song(q)
        return SearchResponse(results=results)
    except ImportError_ as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error inesperado buscando «{q}»: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al buscar")
