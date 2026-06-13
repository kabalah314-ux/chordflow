import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .db import Base


def _utcnow():
    """Hora actual en UTC con zona (reemplaza datetime.utcnow(), deprecado en 3.12)."""
    return datetime.now(timezone.utc)


# Utilidad para usar UUID
def generate_uuid():
    return str(uuid.uuid4())

class Song(Base):
    __tablename__ = "songs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    artist = Column(String(255))
    album = Column(String(255))
    year = Column(Integer)
    bpm = Column(Integer, default=120)
    time_signature_num = Column(Integer, default=4)
    time_signature_den = Column(Integer, default=4)
    key_root = Column(String(4))
    key_mode = Column(String(32))
    tuning = Column(String(32))
    capo = Column(Integer, default=0)
    instrument = Column(String(32))
    format_version = Column(String(8), default="1.0")
    owner_id = Column(String(36), index=True) # FK a Users (Fase futura)
    is_public = Column(Boolean, default=False)
    source_type = Column(String(32))
    source_file_path = Column(Text)
    tags = Column(JSON)
    duration_beats = Column(Float)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)

    sections = relationship("Section", back_populates="song", cascade="all, delete-orphan", order_by="Section.order")

class Section(Base):
    __tablename__ = "sections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    song_id = Column(String(36), ForeignKey("songs.id"), nullable=False, index=True)
    name = Column(String(64))
    order = Column(Integer, nullable=False)
    repeat_count = Column(Integer, default=1)
    color_tag = Column(String(7))

    song = relationship("Song", back_populates="sections")
    lines = relationship("Line", back_populates="section", cascade="all, delete-orphan", order_by="Line.order")

class Line(Base):
    __tablename__ = "lines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    section_id = Column(String(36), ForeignKey("sections.id"), nullable=False, index=True)
    order = Column(Integer, nullable=False)
    type = Column(String(32), nullable=False) # lyric | tab | chord_only | comment | spacer
    content = Column(Text)
    beat_start = Column(Float)
    beat_duration = Column(Float)
    display_hint = Column(JSON)

    section = relationship("Section", back_populates="lines")
    chords = relationship("ChordMarker", back_populates="line", cascade="all, delete-orphan")
    tab_strings = relationship("TabLine", back_populates="line", cascade="all, delete-orphan")

class ChordMarker(Base):
    __tablename__ = "chord_markers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_id = Column(String(36), ForeignKey("lines.id"), nullable=False, index=True)
    chord_name = Column(String(16), nullable=False)
    char_position = Column(Integer)
    beat_offset = Column(Float)
    duration_beats = Column(Float)
    finger_diagram = Column(JSON)
    barre = Column(JSON)
    muted_strings = Column(JSON)

    line = relationship("Line", back_populates="chords")

class TabLine(Base):
    __tablename__ = "tab_lines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    line_id = Column(String(36), ForeignKey("lines.id"), nullable=False, index=True)
    string_number = Column(Integer, nullable=False)
    fret_sequence = Column(JSON) # Array of objects: beat, fret, technique, duration

    line = relationship("Line", back_populates="tab_strings")
