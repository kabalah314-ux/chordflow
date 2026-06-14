import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.db import get_db
from ..services.models import ChordMarker, Line, Section, Song, TabLine, _utcnow
from ..services.schemas import SongCreate, SongResponse, SongSummary, SongUpdate

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/songs",
    tags=["songs"]
)


def _append_sections(db_song: Song, sections) -> None:
    """Construye la estructura anidada (secciones→líneas→acordes/tabs) sobre `db_song`,
    apoyándose en los cascades del ORM. Extraído de create/update_song, que armaban
    exactamente lo mismo (T-038). No hace commit: el endpoint controla la transacción."""
    for sec_data in sections:
        db_sec = Section(**sec_data.model_dump(exclude={"lines"}))
        db_song.sections.append(db_sec)

        for line_data in sec_data.lines:
            db_line = Line(**line_data.model_dump(exclude={"chords", "tab_strings"}))
            db_sec.lines.append(db_line)

            for chord_data in line_data.chords:
                db_line.chords.append(ChordMarker(**chord_data.model_dump()))

            for tab_data in line_data.tab_strings:
                db_line.tab_strings.append(TabLine(**tab_data.model_dump()))

@router.get("/", response_model=List[SongSummary])
def get_songs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
              db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """Lista (ligera) de las canciones del usuario, paginada. Devuelve `SongSummary`
    (metadatos + section_count, SIN la estructura anidada) para evitar el N+1 de
    serializar toda la jerarquía por canción (T-010). T-037: skip/limit acotados."""
    try:
        songs = (db.query(Song)
                 .filter(Song.deleted_at.is_(None), Song.owner_id == user_id)
                 .offset(skip).limit(limit).all())
        if not songs:
            return []
        # UNA sola query agregada para el nº de secciones de TODAS las canciones de la
        # página (en vez de un lazy-load por canción → N+1).
        song_ids = [s.id for s in songs]
        counts = dict(
            db.query(Section.song_id, func.count(Section.id))
            .filter(Section.song_id.in_(song_ids))
            .group_by(Section.song_id)
            .all()
        )
        for s in songs:
            # Atributo no mapeado, solo para la serialización (no se persiste).
            s.section_count = counts.get(s.id, 0)
        return songs
    except SQLAlchemyError as e:
        logger.error(f"Error recuperando canciones: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")

@router.get("/{song_id}", response_model=SongResponse)
def get_song(song_id: str, db: Session = Depends(get_db),
             user_id: str = Depends(get_current_user)):
    """Obtiene el detalle completo de una canción del usuario."""
    try:
        song = db.query(Song).filter(Song.id == song_id, Song.owner_id == user_id,
                                      Song.deleted_at.is_(None)).first()
        if not song:
            raise HTTPException(status_code=404, detail="Canción no encontrada")
        return song
    except SQLAlchemyError as e:
        logger.error(f"Error recuperando canción {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")

@router.post("/", response_model=SongResponse, status_code=status.HTTP_201_CREATED)
def create_song(song: SongCreate, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    """Crea una canción completa con sus secciones, líneas y acordes."""
    try:
        # Crear la estructura anidada de SQLAlchemy, asignando el dueño
        db_song = Song(**song.model_dump(exclude={"sections"}), owner_id=user_id)
        _append_sections(db_song, song.sections)

        db.add(db_song)
        db.commit()
        db.refresh(db_song)
        logger.info(f"Canción creada exitosamente con ID: {db_song.id}")
        return db_song
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creando canción: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")
    except HTTPException:
        db.rollback()
        raise  # no convertir 404/403/etc. en 400
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado creando canción: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/{song_id}", response_model=SongResponse)
def update_song(song_id: str, song_update: SongCreate, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    """Actualiza una canción existente recreando su estructura (Fase 1 simplificada)."""
    try:
        db_song = db.query(Song).filter(Song.id == song_id, Song.owner_id == user_id,
                                        Song.deleted_at.is_(None)).first()
        if not db_song:
            raise HTTPException(status_code=404, detail="Canción no encontrada")

        # Eliminar las secciones existentes vía ORM para que el cascade
        # `delete-orphan` borre también sus lines/chords/tab_lines. (Un bulk
        # `query(...).delete()` NO dispara el cascade ORM y, como SQLite no fuerza
        # FKs por defecto, dejaba filas huérfanas en cada edición. Ver T-003.)
        for sec in list(db_song.sections):
            db.delete(sec)
        db.flush()

        # Actualizar campos base de la canción
        update_data = song_update.model_dump(exclude={"sections"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_song, key, value)

        # Re-crear secciones (mismo armado que en create_song, ver _append_sections)
        _append_sections(db_song, song_update.sections)

        db.commit()
        db.refresh(db_song)
        logger.info(f"Canción actualizada exitosamente: {song_id}")
        return db_song
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error actualizando canción {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")
    except HTTPException:
        db.rollback()
        raise  # no convertir el 404 (canción no encontrada) en 400
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado actualizando canción {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.patch("/{song_id}", response_model=SongResponse)
def patch_song(song_id: str, song_update: SongUpdate, db: Session = Depends(get_db),
               user_id: str = Depends(get_current_user)):
    """Actualiza parcialmente los metadatos de una canción (p. ej. el tempo) sin
    recrear su estructura. Ligero: solo aplica los campos enviados."""
    try:
        db_song = db.query(Song).filter(Song.id == song_id, Song.owner_id == user_id,
                                        Song.deleted_at.is_(None)).first()
        if not db_song:
            raise HTTPException(status_code=404, detail="Canción no encontrada")

        update_data = song_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_song, key, value)

        db.commit()
        db.refresh(db_song)
        logger.info(f"Canción actualizada (PATCH) {song_id}: {list(update_data.keys())}")
        return db_song
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en PATCH de canción {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")


@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song(song_id: str, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    """Soft delete (T-013): marca `deleted_at` en vez de borrar la fila. Todas las
    lecturas (list/get/put/patch) ya filtran `deleted_at IS NULL`, así que la canción
    desaparece de la app pero la fila (y su estructura) se conserva en la BD —
    recuperable y auditable. Un segundo DELETE sobre una canción ya borrada → 404."""
    try:
        db_song = db.query(Song).filter(Song.id == song_id, Song.owner_id == user_id,
                                         Song.deleted_at.is_(None)).first()
        if not db_song:
            raise HTTPException(status_code=404, detail="Canción no encontrada")

        db_song.deleted_at = _utcnow()
        db.commit()
        logger.info(f"Canción soft-deleted: {song_id}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error eliminando canción {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")
    except HTTPException:
        db.rollback()
        raise  # no convertir el 404 en 500
