from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChordMarkerBase(BaseModel):
    chord_name: str
    char_position: Optional[int] = None
    beat_offset: Optional[float] = None
    duration_beats: Optional[float] = None
    finger_diagram: Optional[Dict[str, Any]] = None
    barre: Optional[Dict[str, Any]] = None
    muted_strings: Optional[List[int]] = None

class ChordMarkerCreate(ChordMarkerBase):
    pass

class ChordMarkerResponse(ChordMarkerBase):
    id: str
    line_id: str

    model_config = ConfigDict(from_attributes=True)

class TabLineBase(BaseModel):
    string_number: int
    fret_sequence: List[Dict[str, Any]]

class TabLineCreate(TabLineBase):
    pass

class TabLineResponse(TabLineBase):
    id: str
    line_id: str

    model_config = ConfigDict(from_attributes=True)

class LineBase(BaseModel):
    order: int
    # Validación de entrada (T-035): un type fuera de la lista → 422 (defensa de usuario);
    # el CHECK de BD (models.Line) es la defensa en profundidad.
    type: Literal["lyric", "tab", "chord_only", "comment", "spacer"]
    content: Optional[str] = None
    beat_start: Optional[float] = None
    beat_duration: Optional[float] = None
    display_hint: Optional[Dict[str, Any]] = None

class LineCreate(LineBase):
    chords: Optional[List[ChordMarkerCreate]] = []
    tab_strings: Optional[List[TabLineCreate]] = []

class LineResponse(LineBase):
    id: str
    section_id: str
    chords: List[ChordMarkerResponse] = []
    tab_strings: List[TabLineResponse] = []

    model_config = ConfigDict(from_attributes=True)

class SectionBase(BaseModel):
    name: Optional[str] = None
    order: int
    repeat_count: int = 1
    color_tag: Optional[str] = None

class SectionCreate(SectionBase):
    lines: Optional[List[LineCreate]] = []

class SectionResponse(SectionBase):
    id: str
    song_id: str
    lines: List[LineResponse] = []

    model_config = ConfigDict(from_attributes=True)

class SongBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = Field(None, ge=0, le=3000)
    bpm: int = Field(120, ge=20, le=400)
    time_signature_num: int = Field(4, ge=1, le=32)
    time_signature_den: int = Field(4, ge=1, le=32)
    key_root: Optional[str] = None
    key_mode: Optional[str] = None
    tuning: Optional[str] = None
    capo: int = Field(0, ge=0, le=24)
    instrument: Optional[str] = None
    format_version: str = "1.0"
    is_public: bool = False
    source_type: Optional[str] = None
    source_file_path: Optional[str] = None
    tags: Optional[List[str]] = None
    duration_beats: Optional[float] = None

class SongCreate(SongBase):
    sections: Optional[List[SectionCreate]] = []

# Actualización parcial de metadatos (no toca la estructura de secciones).
# Usado por PATCH para, p. ej., guardar el último tempo elegido.
class SongUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = Field(None, ge=0, le=3000)
    bpm: Optional[int] = Field(None, ge=20, le=400)
    key_root: Optional[str] = None
    key_mode: Optional[str] = None
    tuning: Optional[str] = None
    capo: Optional[int] = Field(None, ge=0, le=24)
    instrument: Optional[str] = None
    is_public: Optional[bool] = None

class SongResponse(SongBase):
    id: str
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    sections: List[SectionResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Listado ligero de `GET /songs/`: metadatos planos + número de secciones, SIN la
# estructura anidada (sections→lines→chords). Serializar `SongResponse` en el listado
# obligaba a lazy-load de toda la estructura por cada canción → N+1. `SongSummary` no
# declara `sections`, así que pydantic nunca toca esa relación. El `section_count` lo
# rellena el router con UNA sola query agregada para todas las canciones (T-010).
class SongSummary(SongBase):
    id: str
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    section_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ── Setlists / repertorios (Fase 5) ──────────────────────────────────────────
class SetlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    song_ids: List[str] = []  # canciones en el orden deseado


class SetlistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    song_ids: Optional[List[str]] = None  # si viene, reemplaza la lista/orden completo


class SetlistItemOut(BaseModel):
    song_id: str
    position: int
    title: str
    artist: Optional[str] = None
    bpm: Optional[int] = None


class SetlistResponse(BaseModel):
    id: str
    name: str
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[SetlistItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class SetlistSummary(BaseModel):
    id: str
    name: str
    song_count: int = 0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
