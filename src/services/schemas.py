from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _to_naive_utc(v: Optional[datetime]) -> Optional[datetime]:
    """Normaliza un datetime con zona a naive-UTC (la BD guarda DateTime sin tz). Así un input
    aware con offset ≠ UTC (p. ej. `...+02:00`) no queda desfasado frente al `now` naive-UTC de
    los filtros agregados (revisión T-078). naive y `Z`/UTC pasan tal cual."""
    if v is not None and v.tzinfo is not None:
        return v.astimezone(timezone.utc).replace(tzinfo=None)
    return v


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
    reference_url: Optional[str] = Field(None, max_length=512)
    tags: Optional[List[str]] = None
    duration_beats: Optional[float] = None

class SongCreate(SongBase):
    sections: Optional[List[SectionCreate]] = []


class SongCopyToBand(BaseModel):
    """Copiar una de mis canciones personales al repertorio de una banda (decisión §7)."""

    song_id: str

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
    reference_url: Optional[str] = Field(None, max_length=512)

class SongResponse(SongBase):
    id: str
    owner_id: Optional[str] = None
    band_id: Optional[str] = None  # null = personal; con valor = repertorio de esa banda
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
    band_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    section_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ── Setlists / repertorios (Fase 5) ──────────────────────────────────────────
class SetlistItemIn(BaseModel):
    song_id: str
    note: Optional[str] = Field(None, max_length=255)  # apunte por canción ("capo 2", "acústica"…)


class SetlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    song_ids: List[str] = []  # canciones en el orden deseado (compat sin nota)
    items: Optional[List[SetlistItemIn]] = None  # si viene, tiene prioridad: orden + nota por canción


class SetlistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    song_ids: Optional[List[str]] = None  # si viene, reemplaza la lista/orden completo (compat)
    items: Optional[List[SetlistItemIn]] = None  # alternativa a song_ids con nota por canción


class SetlistItemOut(BaseModel):
    song_id: str
    position: int
    title: str
    artist: Optional[str] = None
    bpm: Optional[int] = None
    note: Optional[str] = None  # apunte por canción (Fase 9): "aquí hablo al público"…


class SetlistResponse(BaseModel):
    id: str
    name: str
    owner_id: Optional[str] = None
    band_id: Optional[str] = None  # null = personal; con valor = setlist de esa banda
    created_at: datetime
    updated_at: datetime
    items: List[SetlistItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class SetlistSummary(BaseModel):
    id: str
    name: str
    band_id: Optional[str] = None
    song_count: int = 0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Repertorios de banda — colecciones temáticas (T-114) ──────────────────────
# A diferencia del Setlist (orden de bolo + notas por canción), una colección agrupa canciones del
# repertorio por tema, sin orden de concierto. Solo de banda (sin `owner_id`).
class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    song_ids: List[str] = []  # canciones iniciales (del repertorio de la banda)


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    song_ids: Optional[List[str]] = None  # si viene, reemplaza la pertenencia completa


class CollectionItemOut(BaseModel):
    song_id: str
    position: int
    title: str
    artist: Optional[str] = None
    bpm: Optional[int] = None


class CollectionResponse(BaseModel):
    id: str
    name: str
    band_id: str
    created_at: datetime
    updated_at: datetime
    items: List[CollectionItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class CollectionSummary(BaseModel):
    id: str
    name: str
    band_id: str
    song_count: int = 0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Giro V2 — Núcleo de identidad de banda (Fase 7, T-049) ────────────────────
# Los Literal de role/status reflejan las fuentes únicas models.BAND_ROLES y
# models.MEMBERSHIP_STATUSES (mismo patrón que LineBase.type). Si cambian allí, actualizar aquí.

# Perfil del músico
class MusicianProfileBase(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    instruments: Optional[List[str]] = None
    avatar_url: Optional[str] = Field(None, max_length=512)


class MusicianProfileUpsert(MusicianProfileBase):
    """Crear/editar el propio perfil (el id sale del usuario autenticado, no del body)."""


class MusicianProfileResponse(MusicianProfileBase):
    id: str  # = user_id de Supabase
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Banda
class BandCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=512)


BandPlan = Literal["free", "pro"]


class BandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=512)
    plan: Optional[BandPlan] = None  # andamiaje SaaS (V3-F3); lo cambia un admin


class BandResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    created_by: str
    plan: BandPlan = "free"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BandSummary(BaseModel):
    """Tarjeta de "Mis bandas": datos de la banda + mi rol en ella."""

    id: str
    name: str
    avatar_url: Optional[str] = None
    plan: BandPlan = "free"
    role: Literal["admin", "member", "guest"]  # mi rol en esta banda
    member_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# Pertenencia (membresía)
class BandMembershipResponse(BaseModel):
    id: str
    band_id: str
    user_id: str
    role: Literal["admin", "member", "guest"]
    instrument: Optional[str] = None
    status: Literal["active", "left"]
    left_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None
    # Nombre real del músico (de MusicianProfile), si existe → evita mostrar UUIDs.
    display_name: Optional[str] = None
    # ¿Esta fila soy yo? (lo rellena el endpoint) → el front sabe si es admin sin exponer ids.
    is_me: bool = False

    model_config = ConfigDict(from_attributes=True)


class MembershipRoleUpdate(BaseModel):
    role: Literal["admin", "member", "guest"]


# Invitación por código
class BandInviteCreate(BaseModel):
    role_to_grant: Literal["admin", "member", "guest"] = "member"
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1)


class BandInviteResponse(BaseModel):
    id: str
    band_id: str
    code: str
    role_to_grant: Literal["admin", "member", "guest"]
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    used_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvitePreview(BaseModel):
    """Lo que ve quien abre un enlace de invitación ANTES de aceptar (sin exponer datos
    sensibles de la banda): nombre, rol que se concede y si la invitación es válida."""

    band_id: str
    band_name: str
    role_to_grant: Literal["admin", "member", "guest"]
    valid: bool
    reason: Optional[str] = None  # si no es válida: "expirada" | "agotada" | "banda no disponible"


# ── Agenda: eventos + asistencia (Fase 10) ────────────────────────────────────
EventType = Literal["rehearsal", "concert", "other"]
EventStatus = Literal["lead", "contacted", "negotiating", "confirmed", "done", "cancelled"]
AttendanceStatus = Literal["yes", "no", "maybe"]


class EventCreate(BaseModel):
    type: EventType
    title: str = Field(min_length=1, max_length=255)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: Optional[EventStatus] = None  # default en el modelo: 'confirmed'
    setlist_id: Optional[str] = None  # solo conciertos

    _norm_dates = field_validator("starts_at", "ends_at")(_to_naive_utc)


class EventUpdate(BaseModel):
    type: Optional[EventType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: Optional[EventStatus] = None
    setlist_id: Optional[str] = None

    _norm_dates = field_validator("starts_at", "ends_at")(_to_naive_utc)


class AttendanceOut(BaseModel):
    user_id: str
    status: AttendanceStatus
    display_name: Optional[str] = None
    responded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AttendanceSet(BaseModel):
    status: AttendanceStatus


class EventSummary(BaseModel):
    id: str
    type: EventType
    title: str
    starts_at: Optional[datetime] = None
    status: EventStatus
    setlist_id: Optional[str] = None
    my_status: Optional[AttendanceStatus] = None  # mi asistencia (si la marqué)
    attendance: List[AttendanceOut] = []  # quién ha respondido (para mostrar confirmados en la agenda)

    model_config = ConfigDict(from_attributes=True)


class EventResponse(BaseModel):
    id: str
    band_id: str
    type: EventType
    title: str
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    status: EventStatus
    setlist_id: Optional[str] = None
    created_by: str
    created_at: datetime
    attendance: List[AttendanceOut] = []
    my_status: Optional[AttendanceStatus] = None

    model_config = ConfigDict(from_attributes=True)


# ── Finanzas: transacciones, reparto, liquidaciones, balances (Fase 11) ───────
TransactionType = Literal["expense", "income"]


class SplitIn(BaseModel):
    user_id: Optional[str] = None  # null si to_fund
    to_fund: bool = False
    share_amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class TransactionCreate(BaseModel):
    type: TransactionType
    description: Optional[str] = Field(None, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    date: Optional[datetime] = None
    category: Optional[str] = Field(None, max_length=64)
    paid_by: Optional[str] = None  # user_id; o usar paid_by_fund
    paid_by_fund: bool = False
    event_id: Optional[str] = None
    # Si se omite/queda vacío → reparto a partes iguales entre miembros activos.
    splits: Optional[List[SplitIn]] = None


class SplitOut(BaseModel):
    user_id: Optional[str] = None
    to_fund: bool = False
    share_amount: Decimal
    display_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: str
    band_id: str
    type: TransactionType
    description: Optional[str] = None
    amount: Decimal
    date: Optional[datetime] = None
    category: Optional[str] = None
    paid_by: Optional[str] = None
    paid_by_fund: bool = False
    event_id: Optional[str] = None
    created_at: datetime
    splits: List[SplitOut] = []

    model_config = ConfigDict(from_attributes=True)


class TransactionSummary(BaseModel):
    id: str
    type: TransactionType
    description: Optional[str] = None
    amount: Decimal
    date: Optional[datetime] = None
    category: Optional[str] = None
    paid_by: Optional[str] = None
    paid_by_fund: bool = False
    event_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SettlementCreate(BaseModel):
    from_user_id: str
    to_user_id: Optional[str] = None  # null si to_fund
    to_fund: bool = False
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    date: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=255)


class SettlementResponse(BaseModel):
    id: str
    band_id: str
    from_user_id: str
    to_user_id: Optional[str] = None
    to_fund: bool = False
    amount: Decimal
    date: Optional[datetime] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BalanceOut(BaseModel):
    """Saldo de un participante (miembro o el fondo). Positivo = le deben; negativo = debe."""

    participant: str  # user_id, o 'fund'
    is_fund: bool = False
    display_name: Optional[str] = None
    balance: Decimal


# ── Comunicación: mensajes (Fase 12) ──────────────────────────────────────────
class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    event_id: Optional[str] = None  # null = chat general; con valor = hilo del evento


class MessageEdit(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class MessagePin(BaseModel):
    is_pinned: bool


class MessageOut(BaseModel):
    id: str
    band_id: str
    event_id: Optional[str] = None
    author_id: str
    author_name: Optional[str] = None
    body: str
    is_pinned: bool
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_mine: bool = False

    model_config = ConfigDict(from_attributes=True)


# ── Inicio (dashboard agregado, contexto TÚ) — Fase 13, T-076 ─────────────────
# Agregan datos de TODAS mis bandas (con etiqueta de banda). El aislamiento es inherente:
# solo se consultan las bandas donde soy miembro activo.
class DashboardEvent(BaseModel):
    band_id: str
    band_name: str
    id: str
    title: str
    type: str
    starts_at: Optional[datetime] = None
    my_status: Optional[str] = None


class DashboardMessage(BaseModel):
    band_id: str
    band_name: str
    id: str
    author_name: Optional[str] = None
    body: str
    is_pinned: bool = False
    created_at: Optional[datetime] = None


class DashboardResponse(BaseModel):
    upcoming_events: List[DashboardEvent] = []
    recent_messages: List[DashboardMessage] = []


class MyBandBalance(BaseModel):
    """Mi saldo neto en una banda (T-079). Positivo = me deben; negativo = debo."""
    band_id: str
    band_name: str
    balance: Decimal


class MyConversation(BaseModel):
    """Una conversación = el chat general de una de mis bandas, con su último mensaje (T-080)."""
    band_id: str
    band_name: str
    last_body: Optional[str] = None
    last_author: Optional[str] = None
    last_at: Optional[datetime] = None


# ── V3 — Giras (V3-F5) ────────────────────────────────────────────────────────
TourStatus = Literal["planning", "active", "done", "cancelled"]


class TourBudgetLineCreate(BaseModel):
    concept: str = Field(min_length=1, max_length=255)
    category: Optional[str] = None
    estimated_amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class TourBudgetLineResponse(BaseModel):
    id: str
    concept: str
    category: Optional[str] = None
    estimated_amount: Decimal
    model_config = ConfigDict(from_attributes=True)


class TourStopCreate(BaseModel):
    event_id: Optional[str] = None     # concierto de la banda (validado en el router)
    city: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class TourStopUpdate(BaseModel):
    event_id: Optional[str] = None
    city: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    position: Optional[int] = Field(None, ge=0)


class TourStopResponse(BaseModel):
    id: str
    event_id: Optional[str] = None
    position: int
    city: Optional[str] = None
    notes: Optional[str] = None
    # Enriquecido desde el evento ligado (si lo hay), para pintar la ruta sin otra llamada.
    event_title: Optional[str] = None
    event_starts_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class TourBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    status: TourStatus = "planning"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None


class TourCreate(TourBase):
    pass


class TourUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[TourStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None


class TourSummary(BaseModel):
    id: str
    band_id: str
    name: str
    status: TourStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    stop_count: int = 0
    total_budget: Decimal = Decimal("0.00")
    model_config = ConfigDict(from_attributes=True)


class TourResponse(TourBase):
    id: str
    band_id: str
    created_at: datetime
    updated_at: datetime
    stops: List[TourStopResponse] = []
    budget_lines: List[TourBudgetLineResponse] = []
    total_budget: Decimal = Decimal("0.00")
    model_config = ConfigDict(from_attributes=True)


# ── V3 — Biblioteca global / catálogo público (V3-F9, D9) ─────────────────────
class PublicScoreSummary(BaseModel):
    id: str
    work_id: str
    title: str
    artist: Optional[str] = None
    key_root: Optional[str] = None
    key_mode: Optional[str] = None
    bpm: Optional[int] = None
    publisher_name: Optional[str] = None   # nombre del que la publicó (atribución)
    rating_avg: float = 0
    rating_count: int = 0
    import_count: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ScoreCommentOut(BaseModel):
    id: str
    user_id: str
    author_name: Optional[str] = None
    body: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PublicScoreDetail(PublicScoreSummary):
    sections: List[Any] = []               # snapshot del árbol (lo pinta score_render.js)
    comments: List[ScoreCommentOut] = []
    my_rating: Optional[int] = None


class CatalogPublishRequest(BaseModel):
    """Subir una de mis canciones al catálogo global (flujo "ponla aquí", D9)."""
    song_id: str


class CatalogImportRequest(BaseModel):
    """Importar una partitura del catálogo a mi espacio: a una banda mía o (null) a lo personal."""
    band_id: Optional[str] = None


class ScoreRatingSet(BaseModel):
    stars: int = Field(ge=1, le=5)


class CatalogCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
