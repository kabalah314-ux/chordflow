from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


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
    type: str # lyric | tab | chord_only | comment | spacer
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
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    bpm: int = 120
    time_signature_num: int = 4
    time_signature_den: int = 4
    key_root: Optional[str] = None
    key_mode: Optional[str] = None
    tuning: Optional[str] = None
    capo: int = 0
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
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    bpm: Optional[int] = None
    key_root: Optional[str] = None
    key_mode: Optional[str] = None
    tuning: Optional[str] = None
    capo: Optional[int] = None
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
