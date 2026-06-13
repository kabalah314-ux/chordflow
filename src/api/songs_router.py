import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.db import get_db
from ..services.models import ChordMarker, Line, Section, Song, TabLine
from ..services.schemas import SongCreate, SongResponse, SongUpdate

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/songs",
    tags=["songs"]
)

@router.get("/", response_model=List[SongResponse])
def get_songs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
              db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    """Obtiene las canciones del usuario autenticado (paginadas). T-037: skip/limit acotados."""
    try:
        songs = (db.query(Song)
                 .filter(Song.deleted_at.is_(None), Song.owner_id == user_id)
                 .offset(skip).limit(limit).all())
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

        for sec_data in song.sections:
            db_sec = Section(**sec_data.model_dump(exclude={"lines"}))
            db_song.sections.append(db_sec)

            for line_data in sec_data.lines:
                db_line = Line(**line_data.model_dump(exclude={"chords", "tab_strings"}))
                db_sec.lines.append(db_line)

                for chord_data in line_data.chords:
                    db_chord = ChordMarker(**chord_data.model_dump())
                    db_line.chords.append(db_chord)

                for tab_data in line_data.tab_strings:
                    db_tab = TabLine(**tab_data.model_dump())
                    db_line.tab_strings.append(db_tab)

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

        # Re-crear secciones
        for sec_data in song_update.sections:
            db_sec = Section(**sec_data.model_dump(exclude={"lines"}))
            db_song.sections.append(db_sec)

            for line_data in sec_data.lines:
                db_line = Line(**line_data.model_dump(exclude={"chords", "tab_strings"}))
                db_sec.lines.append(db_line)

                for chord_data in line_data.chords:
                    db_chord = ChordMarker(**chord_data.model_dump())
                    db_line.chords.append(db_chord)

                for tab_data in line_data.tab_strings:
                    db_tab = TabLine(**tab_data.model_dump())
                    db_line.tab_strings.append(db_tab)

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
    """Elimina una canción del usuario (hard delete en Fase 1)."""
    try:
        db_song = db.query(Song).filter(Song.id == song_id, Song.owner_id == user_id).first()
        if not db_song:
            raise HTTPException(status_code=404, detail="Canción no encontrada")

        db.delete(db_song)
        db.commit()
        logger.info(f"Canción eliminada: {song_id}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error eliminando canción {song_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno de base de datos")
