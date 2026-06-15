import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from .db import Base

# Valores permitidos para Line.type. Fuente única para el CHECK de BD (T-035) y la validación
# de schema (Literal en schemas.py).
LINE_TYPES = ("lyric", "tab", "chord_only", "comment", "spacer")


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
    bpm = Column(Integer, default=120, server_default=text("120"))
    time_signature_num = Column(Integer, default=4, server_default=text("4"))
    time_signature_den = Column(Integer, default=4, server_default=text("4"))
    key_root = Column(String(4))
    key_mode = Column(String(32))
    tuning = Column(String(32))
    capo = Column(Integer, default=0, server_default=text("0"))
    instrument = Column(String(32))
    format_version = Column(String(8), default="1.0", server_default=text("'1.0'"))
    # owner_id NOT NULL (T-034): la auth es obligatoria y el router siempre lo asigna; lo
    # blindamos a nivel de esquema para que ninguna fila pueda quedar sin dueño.
    owner_id = Column(String(36), nullable=False, index=True)
    # server_default agnóstico: 'false' es válido en Postgres y SQLite (3.23+). Un '0' literal
    # lo rechaza Postgres en una columna boolean (DatatypeMismatch). Visto al migrar a Postgres.
    is_public = Column(Boolean, default=False, server_default=text("false"))
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
    song_id = Column(String(36), ForeignKey("songs.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(64))
    order = Column(Integer, nullable=False)
    repeat_count = Column(Integer, default=1, server_default=text("1"))
    color_tag = Column(String(7))

    song = relationship("Song", back_populates="sections")
    lines = relationship("Line", back_populates="section", cascade="all, delete-orphan", order_by="Line.order")

class Line(Base):
    __tablename__ = "lines"
    # CHECK a nivel de BD: Line.type solo admite los valores conocidos (T-035). Defensa en
    # profundidad sobre la validación de schema (Literal en LineBase).
    __table_args__ = (
        CheckConstraint(
            "type IN (" + ", ".join(f"'{t}'" for t in LINE_TYPES) + ")",
            name="ck_lines_type",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    section_id = Column(String(36), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
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
    line_id = Column(String(36), ForeignKey("lines.id", ondelete="CASCADE"), nullable=False, index=True)
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
    line_id = Column(String(36), ForeignKey("lines.id", ondelete="CASCADE"), nullable=False, index=True)
    string_number = Column(Integer, nullable=False)
    fret_sequence = Column(JSON) # Array of objects: beat, fret, technique, duration

    line = relationship("Line", back_populates="tab_strings")


class Setlist(Base):
    """Repertorio: lista ordenada de canciones del usuario para tocar en directo (Fase 5)."""

    __tablename__ = "setlists"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete (como Song)

    items = relationship("SetlistItem", back_populates="setlist",
                         cascade="all, delete-orphan", order_by="SetlistItem.position")


class SetlistItem(Base):
    """Una entrada (canción en una posición) dentro de un repertorio."""

    __tablename__ = "setlist_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    setlist_id = Column(String(36), ForeignKey("setlists.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    song_id = Column(String(36), ForeignKey("songs.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    position = Column(Integer, nullable=False)  # orden dentro del repertorio (0,1,2…)

    setlist = relationship("Setlist", back_populates="items")
    song = relationship("Song")
