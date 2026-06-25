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
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from .db import Base

# Valores permitidos para Line.type. Fuente única para el CHECK de BD (T-035) y la validación
# de schema (Literal en schemas.py).
LINE_TYPES = ("lyric", "tab", "chord_only", "comment", "spacer")

# Giro V2 (SaaS de banda) — fuentes únicas para los CHECK de BD y la validación de schema.
# Roles dentro de una banda (matriz de permisos §C.2 de la guía funcional).
BAND_ROLES = ("admin", "member", "guest")
# Estado de pertenencia: 'left' = baja blanda (la fila permanece para el histórico, §Área 8).
MEMBERSHIP_STATUSES = ("active", "left")
# Agenda (Fase 10). Tipo de evento; el setlist solo se adjunta a 'concert'.
EVENT_TYPES = ("rehearsal", "concert", "other")
# Estado/pipeline del evento (§C.4.1 #1): lead/contacted/negotiating = pipeline de booking (solo
# 'concert', se explota en Fase 14); rehearsal/other nacen en 'confirmed'.
EVENT_STATUSES = ("lead", "contacted", "negotiating", "confirmed", "done", "cancelled")
# Asistencia a un evento (§Área 2 #16).
ATTENDANCE_STATUSES = ("yes", "no", "maybe")
# Finanzas (Fase 11). Tipo de movimiento.
TRANSACTION_TYPES = ("expense", "income")
# Giras (V3-F5). Estado de una gira.
TOUR_STATUSES = ("planning", "active", "done", "cancelled")
# Plan SaaS de la banda (V3-F3, andamiaje; sin cobro aún). 'free' por defecto.
BAND_PLANS = ("free", "pro")
# Biblioteca global (V3-F9). Estado de una partitura del catálogo público.
PUBLIC_SCORE_STATUSES = ("published", "hidden", "removed")
# Eje de visibilidad (V3-F7, D1): private = solo la banda (default); unlisted = accesible por enlace
# (quien tenga el id), no listado/indexado; public = listado/indexable (F8). Las rutas privadas NO
# cambian; lo público se sirve por rutas /public separadas con proyección SEGURA (nunca datos sensibles).
VISIBILITY_LEVELS = ("private", "unlisted", "public")


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
    # band_id (giro V2, Fase 8): NULL = canción personal (espacio de `owner_id`); con valor =
    # está en el repertorio de esa banda (visible/editable por sus miembros). Las canciones de
    # banda son COPIAS (decisión §7), así cada banda tiene su versión sin afectar a la personal.
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # server_default agnóstico: 'false' es válido en Postgres y SQLite (3.23+). Un '0' literal
    # lo rechaza Postgres en una columna boolean (DatatypeMismatch). Visto al migrar a Postgres.
    is_public = Column(Boolean, default=False, server_default=text("false"))
    source_type = Column(String(32))
    source_file_path = Column(Text)
    # Enlace de referencia (YouTube/Spotify) para escuchar el tema original (V3-F4, T-090).
    reference_url = Column(String(512), nullable=True)
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
    # band_id (giro V2, Fase 9): NULL = setlist personal; con valor = setlist de esa banda
    # (sacado de su repertorio, reutilizable). Las personales no se tocan.
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=True, index=True
    )
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
    # note (giro V2, Fase 9): apunte por canción en el setlist ("aquí hablo al público",
    # "cambio de guitarra"). Área 3 #27. Visible en el modo concierto.
    note = Column(Text, nullable=True)

    setlist = relationship("Setlist", back_populates="items")
    song = relationship("Song")


# ── Repertorios de banda — colecciones temáticas (T-114) ──────────────────────
# Diferenciación Repertorio vs Setlist: una COLECCIÓN agrupa canciones del repertorio de la banda
# por tema ("acústico", "cañero", "bodas"), SIN orden de bolo. El Setlist sigue siendo el ORDEN
# concreto de un concierto (con notas por canción, T-110). Aditivo: no toca songs/setlists.


class SongCollection(Base):
    """Colección temática de canciones (T-114). Como `Setlist`: `band_id` con valor = colección de esa
    banda (canciones del repertorio); `band_id` NULL + `owner_id` = colección PERSONAL del usuario
    (sus propias canciones). Soft-delete (como Setlist)."""

    __tablename__ = "song_collections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # owner_id: dueño de la colección PERSONAL (band_id NULL). En las de banda queda NULL.
    owner_id = Column(String(36), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete (como Setlist)

    items = relationship("SongCollectionItem", back_populates="collection",
                         cascade="all, delete-orphan", order_by="SongCollectionItem.position")


class SongCollectionItem(Base):
    """Pertenencia de una canción a una colección. Único (collection_id, song_id): una canción no
    se repite dentro de la misma colección (pero sí puede estar en varias colecciones)."""

    __tablename__ = "song_collection_items"
    __table_args__ = (
        UniqueConstraint("collection_id", "song_id", name="uq_collection_song"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    collection_id = Column(String(36), ForeignKey("song_collections.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    song_id = Column(String(36), ForeignKey("songs.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    position = Column(Integer, nullable=False, default=0)  # orden estable de visualización

    collection = relationship("SongCollection", back_populates="items")
    song = relationship("Song")


# ── Giro V2 — Núcleo de identidad de banda (Fase 7, T-048) ────────────────────
# Todo aditivo: tablas nuevas, no toca lo existente. Convenciones §C.4.3 de
# GUIA_MAESTRA_V2_FUNCIONAL.md (índice band_id, timestamps UTC, soft-delete donde hay
# histórico, CHECK como en Line.type). Song.band_id/Setlist.band_id NO entran aquí (Fases 8/9).


class MusicianProfile(Base):
    """Perfil del músico. `id` = user_id de Supabase (no se genera): permite mostrar
    nombres reales en vez de UUIDs en miembros, finanzas, asistencia, etc. (§4.1)."""

    __tablename__ = "musician_profiles"

    id = Column(String(36), primary_key=True)  # = user_id de Supabase
    display_name = Column(String(255))
    instruments = Column(JSON)  # ["guitarra", "voz", ...]
    avatar_url = Column(String(512))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Band(Base):
    """Banda (tenant). De ella cuelga todo el giro multi-tenant. Soft-delete (tiene
    histórico/valor, §C.4.3)."""

    __tablename__ = "bands"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    avatar_url = Column(String(512))
    created_by = Column(String(36), nullable=False, index=True)  # user_id del creador (→ admin)
    # Una sola divisa por banda (§C.4.3). Sin multi-divisa en v1. Default EUR.
    currency = Column(String(3), nullable=False, default="EUR", server_default=text("'EUR'"))
    # Plan SaaS (V3-F3, andamiaje; sin cobro aún). 'free' | 'pro'. Lo cambia un admin. La validación
    # de valores vive en la capa API (Literal BandPlan); sin CHECK de BD para no recrear `bands`.
    plan = Column(String(16), nullable=False, default="free", server_default=text("'free'"))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete (como Song)

    memberships = relationship(
        "BandMembership", back_populates="band", cascade="all, delete-orphan"
    )
    invites = relationship(
        "BandInvite", back_populates="band", cascade="all, delete-orphan"
    )


class BandMembership(Base):
    """Pertenencia músico↔banda con rol. Único (band_id, user_id). Baja blanda:
    status='left' + left_at (la fila permanece para el histórico, §Área 8)."""

    __tablename__ = "band_memberships"
    __table_args__ = (
        UniqueConstraint("band_id", "user_id", name="uq_membership_band_user"),
        CheckConstraint(
            "role IN (" + ", ".join(f"'{r}'" for r in BAND_ROLES) + ")",
            name="ck_membership_role",
        ),
        CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in MEMBERSHIP_STATUSES) + ")",
            name="ck_membership_status",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(String(36), nullable=False, index=True)
    role = Column(String(16), nullable=False, default="member", server_default=text("'member'"))
    instrument = Column(String(64))  # instrumento en ESTA banda (opcional)
    status = Column(
        String(16), nullable=False, default="active", server_default=text("'active'")
    )
    left_at = Column(DateTime, nullable=True)  # cuándo causó baja (baja blanda)
    joined_at = Column(DateTime, default=_utcnow)

    band = relationship("Band", back_populates="memberships")


class BandInvite(Base):
    """Invitación por código/enlace para unirse a una banda (§8). No depende de emails."""

    __tablename__ = "band_invites"
    __table_args__ = (
        CheckConstraint(
            "role_to_grant IN (" + ", ".join(f"'{r}'" for r in BAND_ROLES) + ")",
            name="ck_invite_role",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code = Column(String(64), nullable=False, unique=True, index=True)  # token del enlace
    created_by = Column(String(36), nullable=False)  # user_id del admin que la generó
    role_to_grant = Column(
        String(16), nullable=False, default="member", server_default=text("'member'")
    )
    expires_at = Column(DateTime, nullable=True)  # caducidad opcional
    max_uses = Column(Integer, nullable=True)  # nº máximo de usos (null = ilimitado)
    used_count = Column(Integer, nullable=False, default=0, server_default=text("0"))
    created_at = Column(DateTime, default=_utcnow)

    band = relationship("Band", back_populates="invites")


# ── Giro V2 — Agenda: eventos (Fase 10, Áreas 2 y 3) ──────────────────────────


class Event(Base):
    """Evento de la banda: ensayo, concierto u otro. Hub de la operativa (agenda/booking).
    El setlist solo se adjunta a conciertos. Soft-delete (tiene histórico, §C.4.3)."""

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "type IN (" + ", ".join(f"'{t}'" for t in EVENT_TYPES) + ")",
            name="ck_events_type",
        ),
        CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in EVENT_STATUSES) + ")",
            name="ck_events_status",
        ),
        CheckConstraint(
            "visibility IN (" + ", ".join(f"'{v}'" for v in VISIBILITY_LEVELS) + ")",
            name="ck_events_visibility",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type = Column(String(16), nullable=False)  # rehearsal | concert | other
    title = Column(String(255), nullable=False)
    starts_at = Column(DateTime, nullable=True)  # fecha/hora de inicio
    ends_at = Column(DateTime, nullable=True)
    location = Column(String(255))  # lugar libre (ensayo/otro); el concierto usará Venue más tarde
    notes = Column(Text)
    status = Column(
        String(16), nullable=False, default="confirmed", server_default=text("'confirmed'")
    )
    # Visibilidad (V3-F7, D1): private por defecto; unlisted = compartible por enlace; public = listable.
    visibility = Column(
        String(16), nullable=False, default="private", server_default=text("'private'")
    )
    # Solo concierto: setlist adjunto (SET NULL si se borra el setlist; los setlists son soft-delete).
    setlist_id = Column(String(36), ForeignKey("setlists.id", ondelete="SET NULL"), nullable=True)
    # Booking (Fase 14, T-115): contacto del promotor + caché acordado (divisa de la banda). Opcional;
    # se explota en conciertos del funnel de booking. Decimal como en Transaction.amount.
    contact_name = Column(String(255), nullable=True)
    contact_phone = Column(String(64), nullable=True)
    fee = Column(Numeric(10, 2), nullable=True)
    # Sala reutilizable (T-116): un concierto puede apuntar a un Venue de la banda. SET NULL si se
    # borra la sala. El `location` libre sigue existiendo (para ensayos/otros sin sala formal).
    venue_id = Column(String(36), ForeignKey("venues.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(String(36), nullable=False)  # admin que lo creó
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)

    attendance = relationship(
        "EventAttendance", back_populates="event", cascade="all, delete-orphan"
    )


class EventAttendance(Base):
    """Confirmación de asistencia de un miembro a un evento (voy / no voy / quizás)."""

    __tablename__ = "event_attendance"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_attendance_event_user"),
        CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in ATTENDANCE_STATUSES) + ")",
            name="ck_attendance_status",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(String(36), nullable=False, index=True)
    status = Column(String(8), nullable=False)  # yes | no | maybe
    responded_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    event = relationship("Event", back_populates="attendance")


# ── Booking — Salas reutilizables (Fase 14, T-116) ────────────────────────────
class Venue(Base):
    """Sala/local de la banda, reutilizable entre conciertos (T-116). De banda (band_id obligatorio);
    el concierto la enlaza con `Event.venue_id`. Soft-delete (tiene histórico/valor, §C.4.3)."""

    __tablename__ = "venues"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    address = Column(String(512), nullable=True)
    city = Column(String(255), nullable=True)
    capacity = Column(Integer, nullable=True)
    contact = Column(String(255), nullable=True)  # contacto de la sala (técnico/responsable)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete


# ── Giro V2 — Finanzas con división (Fase 11, Áreas 4/6) ──────────────────────
# Modelo Splitwise: cada movimiento tiene quién pagó/cobró y un reparto cuyas partes suman el total.
# Dinero en Decimal(10,2), una divisa por banda (§C.4.3). El "fondo" es un participante virtual
# (flags paid_by_fund / to_fund), no una tabla aparte. Financieros nunca se borran físicamente
# (soft delete). El cálculo de saldos vive en UN solo servicio (services/balances.py) con tests
# que cuadran a cero.


class Transaction(Base):
    """Movimiento: gasto o ingreso. `paid_by` adelantó (gasto) o cobró (ingreso) el dinero;
    `paid_by_fund` = lo puso/recibió el fondo común. Ligable a un evento (caché del bolo)."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "type IN (" + ", ".join(f"'{t}'" for t in TRANSACTION_TYPES) + ")",
            name="ck_transactions_type",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type = Column(String(8), nullable=False)  # expense | income
    description = Column(String(255))
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(DateTime, default=_utcnow)
    category = Column(String(64))
    paid_by = Column(String(36), nullable=True)  # user_id (null si lo puso/recibió el fondo)
    paid_by_fund = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    event_id = Column(String(36), ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete (financiero: nunca duro)

    splits = relationship(
        "TransactionSplit", back_populates="transaction", cascade="all, delete-orphan"
    )


class TransactionSplit(Base):
    """Parte del reparto de un movimiento. `to_fund` = esta parte se asigna al fondo común.
    La suma de las partes = `amount` del movimiento (invariante, lo garantiza el endpoint)."""

    __tablename__ = "transaction_splits"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(
        String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(String(36), nullable=True, index=True)  # null si to_fund
    share_amount = Column(Numeric(10, 2), nullable=False)
    to_fund = Column(Boolean, nullable=False, default=False, server_default=text("false"))

    transaction = relationship("Transaction", back_populates="splits")


class Settlement(Base):
    """Liquidación: pago real que ajusta los saldos ("Ana paga a Juan 30 €"). `to_fund` = el pago
    va al fondo común."""

    __tablename__ = "settlements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_user_id = Column(String(36), nullable=False)  # quién paga
    to_user_id = Column(String(36), nullable=True)  # a quién (null si to_fund)
    to_fund = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(DateTime, default=_utcnow)
    note = Column(String(255))
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete (financiero)


# ── Giro V2 — Comunicación: mensajes (Fase 12, Área 7) ────────────────────────


class Message(Base):
    """Mensaje de la banda. `event_id` NULL = chat general; con valor = hilo de ese evento.
    `is_pinned` (lo fija un admin) = nota importante; aparecen arriba. Soft delete."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # NULL = chat general; con valor = hilo del evento (comentarios puedo/no puedo, etc.).
    event_id = Column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=True, index=True
    )
    author_id = Column(String(36), nullable=False)
    body = Column(Text, nullable=False)
    is_pinned = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at = Column(DateTime, default=_utcnow)
    edited_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete


# ── V3 — Giras (V3-F5) ────────────────────────────────────────────────────────
# Una gira agrupa varios conciertos (Event type=concert) en una ruta + presupuesto estimado.
# Aislada por band_id (regla de oro). NO duplica Agenda/Finanzas: las agrega/enriquece.


class Tour(Base):
    """Gira: colección ordenada de paradas (conciertos) + presupuesto estimado de la banda.
    Soft-delete (tiene histórico, §C.4.3)."""

    __tablename__ = "tours"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in TOUR_STATUSES) + ")",
            name="ck_tours_status",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    band_id = Column(
        String(36), ForeignKey("bands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    status = Column(
        String(16), nullable=False, default="planning", server_default=text("'planning'")
    )
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    notes = Column(Text)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)

    stops = relationship(
        "TourStop", back_populates="tour", cascade="all, delete-orphan",
        order_by="TourStop.position",
    )
    budget_lines = relationship(
        "TourBudgetLine", back_populates="tour", cascade="all, delete-orphan"
    )


class TourStop(Base):
    """Parada de una gira: fecha/ciudad, opcionalmente ligada a un Event(concert) de la MISMA banda.
    SET NULL si se borra el evento: la parada permanece en la ruta."""

    __tablename__ = "tour_stops"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tour_id = Column(
        String(36), ForeignKey("tours.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id = Column(
        String(36), ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position = Column(Integer, nullable=False)  # orden en la ruta (0,1,2…)
    city = Column(String(255))
    notes = Column(Text)

    tour = relationship("Tour", back_populates="stops")
    event = relationship("Event")


class TourBudgetLine(Base):
    """Línea de presupuesto ESTIMADO de la gira (el gasto real va en Transaction y se enlaza)."""

    __tablename__ = "tour_budget_lines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tour_id = Column(
        String(36), ForeignKey("tours.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept = Column(String(255), nullable=False)
    category = Column(String(64))
    estimated_amount = Column(Numeric(10, 2), nullable=False)

    tour = relationship("Tour", back_populates="budget_lines")


# ── V3 — Biblioteca global / catálogo público (V3-F9, D9) ─────────────────────
# El catálogo es el RECLAMO de la app: un buscador de muchos artistas que crece con lo que sube la
# gente. Es un PLANO DE DATOS SEPARADO (copia desacoplada, D1): publicar una canción crea aquí un
# snapshot independiente; los datos privados de la banda (arreglos, notas, finanzas) NUNCA entran.


class MusicalWork(Base):
    """La "canción" abstracta (p. ej. Wonderwall de Oasis), independiente de quién la suba. Agrupa
    las N versiones publicadas. Único por (artista, título) normalizados para buscar y agrupar."""

    __tablename__ = "musical_works"
    __table_args__ = (
        UniqueConstraint("norm_artist", "norm_title", name="uq_work_artist_title"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)        # título mostrado
    artist = Column(String(255))                       # artista mostrado
    norm_title = Column(String(255), nullable=False, index=True)   # normalizado (búsqueda/único)
    norm_artist = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)

    scores = relationship("PublicScore", back_populates="work", cascade="all, delete-orphan")


class PublicScore(Base):
    """Una versión publicada en el catálogo. `content_json` = snapshot inmutable del árbol de la
    partitura (lo pinta `score_render.js`). `source_band_id` es solo auditoría: NUNCA se expone."""

    __tablename__ = "public_scores"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in PUBLIC_SCORE_STATUSES) + ")",
            name="ck_public_scores_status",
        ),
        # Búsqueda/listado del catálogo filtra siempre por (status, deleted_at) → índice compuesto.
        Index("ix_public_scores_status_deleted", "status", "deleted_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    work_id = Column(
        String(36), ForeignKey("musical_works.id", ondelete="CASCADE"), nullable=False, index=True
    )
    publisher_id = Column(String(36), nullable=False, index=True)  # user_id que la subió (atribución)
    source_band_id = Column(String(36), nullable=True)            # auditoría; NUNCA se expone
    source_song_id = Column(String(36), nullable=True, index=True)  # origen (para evitar republicar, D9)
    title = Column(String(255), nullable=False)
    artist = Column(String(255))
    key_root = Column(String(4))
    key_mode = Column(String(32))
    bpm = Column(Integer)
    reference_url = Column(String(512))                # enlace de referencia (round-trip al importar)
    content_json = Column(JSON, nullable=False)        # snapshot del árbol (secciones→líneas→acordes)
    rating_avg = Column(Numeric(3, 2), nullable=False, default=0, server_default=text("0"))
    rating_count = Column(Integer, nullable=False, default=0, server_default=text("0"))
    import_count = Column(Integer, nullable=False, default=0, server_default=text("0"))
    status = Column(
        String(16), nullable=False, default="published", server_default=text("'published'")
    )
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete

    work = relationship("MusicalWork", back_populates="scores")
    ratings = relationship("ScoreRating", back_populates="score", cascade="all, delete-orphan")
    comments = relationship("ScoreComment", back_populates="score", cascade="all, delete-orphan")


class ScoreRating(Base):
    """Valoración de una partitura del catálogo (1–5 = lo fiel/completa que es). Una por usuario."""

    __tablename__ = "score_ratings"
    __table_args__ = (
        UniqueConstraint("public_score_id", "user_id", name="uq_rating_score_user"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    public_score_id = Column(
        String(36), ForeignKey("public_scores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(String(36), nullable=False, index=True)
    stars = Column(Integer, nullable=False)            # 1..5
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    score = relationship("PublicScore", back_populates="ratings")


class ScoreComment(Base):
    """Comentario sobre una partitura del catálogo ("falta el puente", "acordes del solo mal…")."""

    __tablename__ = "score_comments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    public_score_id = Column(
        String(36), ForeignKey("public_scores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(String(36), nullable=False, index=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)  # soft delete

    score = relationship("PublicScore", back_populates="comments")
