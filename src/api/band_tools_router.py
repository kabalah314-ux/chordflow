"""
V6-F9 — Funciones de banda (GUIA_MAESTRA_V6 §9.6). Todo aislado por banda (regla de oro).

Semáforo del repertorio (T-V6-83)
  GET  /bands/{id}/song-status                  → lo mío + recuento de la banda (miembros)
  PUT  /bands/{id}/songs/{sid}/status           → marcar mi estado de una canción (miembros)
Vista por miembro (T-V6-81)
  GET  /songs/{sid}/my-prefs · PUT /songs/{sid}/my-prefs   (dueño o miembro de su banda)
Pizarra (T-V6-92)
  GET/POST /bands/{id}/notes · PATCH/DELETE /bands/{id}/notes/{nid}   (ver: miembros; editar: no guest)
Hoja del bolo (T-V6-86)
  GET/POST /bands/{id}/events/{eid}/checklist · PATCH/DELETE …/checklist/{iid}
  POST/DELETE /bands/{id}/events/{eid}/sheet-token   (admin: enlace de solo lectura)
  GET  /public/gig-sheets/{token}   (sin login, proyección segura)
Votación de fechas (T-V6-82)
  GET/POST /bands/{id}/polls · GET /bands/{id}/polls/{pid} · PUT …/votes · POST …/confirm · DELETE
  GET  /public/polls/{token} · PUT /public/polls/{token}/votes   (sin cuenta: eliges tu nombre)
Feedback y eventos de producto (T-V6-94)
  POST /feedback · POST /me/product-events
"""

import logging
import secrets
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.band_auth import (
    active_membership,
    require_band_admin,
    require_band_editor,
    require_band_member,
)
from ..services.db import get_db
from ..services.models import (
    Band,
    BandMembership,
    BandNote,
    DatePoll,
    DatePollOption,
    DatePollVote,
    Event,
    EventAttendance,
    EventChecklistItem,
    Feedback,
    MusicianProfile,
    ProductEvent,
    Setlist,
    SetlistItem,
    Song,
    SongMemberPref,
    SongStatus,
    Venue,
    _utcnow,
)
from ..services.ratelimit import check_rate
from ..services.schemas import (
    BandNoteCreate,
    BandNoteOut,
    BandNoteUpdate,
    ChecklistItemIn,
    ChecklistItemOut,
    ChecklistItemPatch,
    FeedbackIn,
    GigSheetPublic,
    PollConfirm,
    PollCreate,
    PollMember,
    PollOptionOut,
    PollOut,
    PollVotesIn,
    ProductEventIn,
    SongPrefIn,
    SongPrefOut,
    SongStatusBoard,
    SongStatusOut,
    SongStatusSet,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["band-tools"])

STATUSES = ("pending", "improving", "mastered")


# ── utilidades ────────────────────────────────────────────────────────────────
def _names(db: Session, user_ids) -> Dict[str, str]:
    ids = [u for u in set(user_ids) if u]
    if not ids:
        return {}
    rows = db.query(MusicianProfile.id, MusicianProfile.display_name).filter(
        MusicianProfile.id.in_(ids)).all()
    return {i: (n or "Alguien") for i, n in rows}


def _active_members(db: Session, band_id: str) -> List[BandMembership]:
    return (db.query(BandMembership)
            .filter(BandMembership.band_id == band_id, BandMembership.status == "active")
            .all())


def _band_song(db: Session, band_id: str, song_id: str) -> Song:
    s = (db.query(Song)
         .filter(Song.id == song_id, Song.band_id == band_id, Song.deleted_at.is_(None))
         .first())
    if s is None:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    return s


def _band_event(db: Session, band_id: str, event_id: str) -> Event:
    ev = (db.query(Event)
          .filter(Event.id == event_id, Event.band_id == band_id, Event.deleted_at.is_(None))
          .first())
    if ev is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return ev


def _check_member_id(db: Session, band_id: str, user_id: Optional[str]) -> None:
    """Un responsable/votante debe ser miembro ACTIVO de la banda (no se cuelan ids ajenos)."""
    if user_id and active_membership(db, band_id, user_id) is None:
        raise HTTPException(status_code=400, detail="Esa persona no es miembro de la banda")


# ══ Semáforo del repertorio (T-V6-83) ═════════════════════════════════════════
@router.get("/bands/{band_id}/song-status", response_model=SongStatusBoard)
def song_status_board(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    song_ids = [sid for (sid,) in db.query(Song.id).filter(
        Song.band_id == band_id, Song.deleted_at.is_(None)).all()]
    rows = (db.query(SongStatus)
            .filter(SongStatus.band_id == band_id, SongStatus.song_id.in_(song_ids or [""]))
            .all())
    me = membership.user_id
    mine = [r for r in rows if r.user_id == me]
    band: Dict[str, Dict[str, int]] = {}
    totals_band = {s: 0 for s in STATUSES}
    for r in rows:
        if not (r.shared or r.user_id == me):
            continue  # privado de otro miembro: no se cuenta ni se revela
        band.setdefault(r.song_id, {s: 0 for s in STATUSES})[r.status] += 1
        totals_band[r.status] += 1
    totals_mine = {s: 0 for s in STATUSES}
    marked = {r.song_id: r.status for r in mine}
    for sid in song_ids:
        totals_mine[marked.get(sid, "pending")] += 1
    return SongStatusBoard(
        mine=[SongStatusOut.model_validate(r) for r in mine], band=band,
        totals_mine=totals_mine, totals_band=totals_band, songs_total=len(song_ids))


@router.put("/bands/{band_id}/songs/{song_id}/status", response_model=SongStatusOut)
def set_song_status(
    band_id: str,
    song_id: str,
    payload: SongStatusSet,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    _band_song(db, band_id, song_id)
    row = (db.query(SongStatus)
           .filter(SongStatus.song_id == song_id, SongStatus.user_id == membership.user_id)
           .first())
    if row is None:
        row = SongStatus(song_id=song_id, band_id=band_id, user_id=membership.user_id,
                         status=payload.status, shared=bool(payload.shared))
        db.add(row)
    else:
        row.status = payload.status
        if payload.shared is not None:
            row.shared = payload.shared
    db.commit()
    db.refresh(row)
    return row


# ══ Vista por miembro (T-V6-81) ════════════════════════════════════════════════
def _readable_song(db: Session, song_id: str, user_id: str) -> Song:
    s = db.query(Song).filter(Song.id == song_id, Song.deleted_at.is_(None)).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    if s.band_id:
        if active_membership(db, s.band_id, user_id) is None:
            raise HTTPException(status_code=404, detail="Canción no encontrada")
    elif s.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    return s


@router.get("/songs/{song_id}/my-prefs", response_model=SongPrefOut)
def get_my_prefs(song_id: str, db: Session = Depends(get_db),
                 user_id: str = Depends(get_current_user)):
    _readable_song(db, song_id, user_id)
    row = (db.query(SongMemberPref)
           .filter(SongMemberPref.song_id == song_id, SongMemberPref.user_id == user_id).first())
    return row or SongPrefOut(song_id=song_id)


@router.put("/songs/{song_id}/my-prefs", response_model=SongPrefOut)
def put_my_prefs(song_id: str, payload: SongPrefIn, db: Session = Depends(get_db),
                 user_id: str = Depends(get_current_user)):
    _readable_song(db, song_id, user_id)
    row = (db.query(SongMemberPref)
           .filter(SongMemberPref.song_id == song_id, SongMemberPref.user_id == user_id).first())
    if row is None:
        row = SongMemberPref(song_id=song_id, user_id=user_id, transpose=0)
        db.add(row)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "transpose" and value is None:
            value = 0
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


# ══ Pizarra (T-V6-92) ══════════════════════════════════════════════════════════
def _note_out(n: BandNote, names: Dict[str, str]) -> BandNoteOut:
    out = BandNoteOut.model_validate(n)
    out.author_name = names.get(n.author_id)
    out.assignee_name = names.get(n.assignee_id) if n.assignee_id else None
    return out


def _get_note(db: Session, band_id: str, note_id: str) -> BandNote:
    n = (db.query(BandNote)
         .filter(BandNote.id == note_id, BandNote.band_id == band_id,
                 BandNote.deleted_at.is_(None)).first())
    if n is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return n


@router.get("/bands/{band_id}/notes", response_model=List[BandNoteOut])
def list_notes(
    band_id: str,
    include_done: bool = Query(False),
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    q = db.query(BandNote).filter(BandNote.band_id == band_id, BandNote.deleted_at.is_(None))
    if not include_done:
        q = q.filter(BandNote.done_at.is_(None))
    notes = q.order_by(BandNote.is_pinned.desc(), BandNote.created_at.desc()).limit(200).all()
    names = _names(db, [n.author_id for n in notes] + [n.assignee_id for n in notes])
    return [_note_out(n, names) for n in notes]


@router.post("/bands/{band_id}/notes", response_model=BandNoteOut,
             status_code=status.HTTP_201_CREATED)
def create_note(
    band_id: str,
    payload: BandNoteCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    _check_member_id(db, band_id, payload.assignee_id)
    if payload.song_id:
        _band_song(db, band_id, payload.song_id)
    if payload.event_id:
        _band_event(db, band_id, payload.event_id)
    n = BandNote(band_id=band_id, author_id=membership.user_id,
                 body=payload.body.strip(), assignee_id=payload.assignee_id,
                 is_pinned=payload.is_pinned, due_date=payload.due_date,
                 song_id=payload.song_id, event_id=payload.event_id)
    db.add(n)
    db.commit()
    db.refresh(n)
    return _note_out(n, _names(db, [n.author_id, n.assignee_id]))


@router.patch("/bands/{band_id}/notes/{note_id}", response_model=BandNoteOut)
def update_note(
    band_id: str,
    note_id: str,
    payload: BandNoteUpdate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    n = _get_note(db, band_id, note_id)
    data = payload.model_dump(exclude_unset=True)
    if "assignee_id" in data:
        _check_member_id(db, band_id, data["assignee_id"])
    done = data.pop("done", None)
    if done is not None:
        n.done_at = _utcnow() if done else None
    for field, value in data.items():
        if field == "body" and value is not None:
            value = value.strip()
        setattr(n, field, value)
    db.commit()
    db.refresh(n)
    return _note_out(n, _names(db, [n.author_id, n.assignee_id]))


@router.delete("/bands/{band_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    band_id: str,
    note_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    n = _get_note(db, band_id, note_id)
    # Borra el autor o un admin (no cualquiera: la pizarra es compartida pero no anárquica).
    if n.author_id != membership.user_id and membership.role != "admin":
        raise HTTPException(status_code=403, detail="Solo el autor o un admin puede borrarla")
    n.deleted_at = _utcnow()
    db.commit()


# ══ Hoja del bolo (T-V6-86) ════════════════════════════════════════════════════
@router.get("/bands/{band_id}/events/{event_id}/checklist", response_model=List[ChecklistItemOut])
def list_checklist(
    band_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    _band_event(db, band_id, event_id)
    return (db.query(EventChecklistItem).filter(EventChecklistItem.event_id == event_id)
            .order_by(EventChecklistItem.position, EventChecklistItem.created_at).all())


@router.post("/bands/{band_id}/events/{event_id}/checklist", response_model=ChecklistItemOut,
             status_code=status.HTTP_201_CREATED)
def add_checklist_item(
    band_id: str,
    event_id: str,
    payload: ChecklistItemIn,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    _band_event(db, band_id, event_id)
    _check_member_id(db, band_id, payload.assignee_id)
    pos = db.query(EventChecklistItem).filter(EventChecklistItem.event_id == event_id).count()
    it = EventChecklistItem(event_id=event_id, text=payload.text.strip(),
                            assignee_id=payload.assignee_id, position=pos)
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


def _get_item(db: Session, event_id: str, item_id: str) -> EventChecklistItem:
    it = (db.query(EventChecklistItem)
          .filter(EventChecklistItem.id == item_id, EventChecklistItem.event_id == event_id)
          .first())
    if it is None:
        raise HTTPException(status_code=404, detail="Elemento no encontrado")
    return it


@router.patch("/bands/{band_id}/events/{event_id}/checklist/{item_id}",
              response_model=ChecklistItemOut)
def patch_checklist_item(
    band_id: str,
    event_id: str,
    item_id: str,
    payload: ChecklistItemPatch,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    _band_event(db, band_id, event_id)
    it = _get_item(db, event_id, item_id)
    data = payload.model_dump(exclude_unset=True)
    if "assignee_id" in data:
        _check_member_id(db, band_id, data["assignee_id"])
    done = data.pop("done", None)
    if done is not None:
        it.done_at = _utcnow() if done else None
    for field, value in data.items():
        setattr(it, field, value)
    db.commit()
    db.refresh(it)
    return it


@router.delete("/bands/{band_id}/events/{event_id}/checklist/{item_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist_item(
    band_id: str,
    event_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    _band_event(db, band_id, event_id)
    db.delete(_get_item(db, event_id, item_id))
    db.commit()


@router.post("/bands/{band_id}/events/{event_id}/sheet-token")
def create_sheet_token(
    band_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    ev = _band_event(db, band_id, event_id)
    if not ev.sheet_token:
        ev.sheet_token = secrets.token_urlsafe(18)
        db.commit()
    return {"token": ev.sheet_token, "path": f"/static/bolo.html?t={ev.sheet_token}"}


@router.delete("/bands/{band_id}/events/{event_id}/sheet-token",
               status_code=status.HTTP_204_NO_CONTENT)
def revoke_sheet_token(
    band_id: str,
    event_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    ev = _band_event(db, band_id, event_id)
    ev.sheet_token = None
    db.commit()


@router.get("/public/gig-sheets/{token}", response_model=GigSheetPublic)
def public_gig_sheet(token: str, request: Request, db: Session = Depends(get_db)):
    check_rate(f"pub-sheet:{request.client.host if request.client else '-'}", 120, 60)
    ev = (db.query(Event)
          .filter(Event.sheet_token == token, Event.deleted_at.is_(None)).first())
    band = db.query(Band).filter(Band.id == ev.band_id, Band.deleted_at.is_(None)).first() \
        if ev else None
    if ev is None or band is None or len(token) < 16:
        raise HTTPException(status_code=404, detail="Hoja no disponible")
    venue_name = None
    if ev.venue_id:
        venue_name = db.query(Venue.name).filter(Venue.id == ev.venue_id).scalar()
    setlist: List[str] = []
    if ev.setlist_id:
        sl = db.query(Setlist).filter(Setlist.id == ev.setlist_id,
                                      Setlist.deleted_at.is_(None)).first()
        if sl is not None:
            rows = (db.query(Song.title)
                    .join(SetlistItem, SetlistItem.song_id == Song.id)
                    .filter(SetlistItem.setlist_id == sl.id)
                    .order_by(SetlistItem.position).all())
            setlist = [t for (t,) in rows]
    items = (db.query(EventChecklistItem).filter(EventChecklistItem.event_id == ev.id)
             .order_by(EventChecklistItem.position).all())
    return GigSheetPublic(
        title=ev.title, band_name=band.name, starts_at=ev.starts_at, load_in_at=ev.load_in_at,
        soundcheck_at=ev.soundcheck_at, doors_at=ev.doors_at, set_at=ev.set_at,
        venue_name=venue_name, address=ev.address or ev.location,
        parking_notes=ev.parking_notes, backline_notes=ev.backline_notes, setlist=setlist,
        checklist=[ChecklistItemOut.model_validate(i) for i in items])


# ══ Votación de fechas (T-V6-82) ═══════════════════════════════════════════════
def _poll_out(db: Session, poll: DatePoll, *, with_token: bool) -> PollOut:
    members = _active_members(db, poll.band_id)
    names = _names(db, [m.user_id for m in members])
    voted = set()
    opts = []
    for o in poll.options:
        votes = {v.user_id: v.status for v in o.votes}
        voted.update(votes.keys())
        opts.append(PollOptionOut(
            id=o.id, starts_at=o.starts_at, ends_at=o.ends_at, votes=votes,
            yes=sum(1 for s in votes.values() if s == "yes"),
            maybe=sum(1 for s in votes.values() if s == "maybe"),
            no=sum(1 for s in votes.values() if s == "no")))
    band_name = db.query(Band.name).filter(Band.id == poll.band_id).scalar()
    return PollOut(
        id=poll.id, band_id=poll.band_id if with_token else None, band_name=band_name,
        title=poll.title, type=poll.type, location=poll.location, notes=poll.notes,
        token=poll.token if with_token else None, status=poll.status, event_id=poll.event_id,
        created_at=poll.created_at, options=opts,
        members=[PollMember(user_id=m.user_id, display_name=names.get(m.user_id, "Alguien"))
                 for m in members],
        pending=sorted(names.get(m.user_id, "Alguien") for m in members
                       if m.user_id not in voted))


def _get_poll(db: Session, band_id: str, poll_id: str) -> DatePoll:
    p = (db.query(DatePoll)
         .filter(DatePoll.id == poll_id, DatePoll.band_id == band_id,
                 DatePoll.deleted_at.is_(None)).first())
    if p is None:
        raise HTTPException(status_code=404, detail="Votación no encontrada")
    return p


def _apply_votes(db: Session, poll: DatePoll, user_id: str, payload: PollVotesIn) -> None:
    if poll.status != "open":
        raise HTTPException(status_code=409, detail="La votación ya está cerrada")
    valid = {o.id for o in poll.options}
    for v in payload.votes:
        if v.option_id not in valid:
            raise HTTPException(status_code=400, detail="Opción no válida")
        row = (db.query(DatePollVote)
               .filter(DatePollVote.option_id == v.option_id, DatePollVote.user_id == user_id)
               .first())
        if row is None:
            db.add(DatePollVote(option_id=v.option_id, user_id=user_id, status=v.status))
        else:
            row.status = v.status
    db.commit()
    db.refresh(poll)


@router.get("/bands/{band_id}/polls", response_model=List[PollOut])
def list_polls(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    polls = (db.query(DatePoll)
             .filter(DatePoll.band_id == band_id, DatePoll.deleted_at.is_(None))
             .order_by(DatePoll.created_at.desc()).limit(50).all())
    return [_poll_out(db, p, with_token=True) for p in polls]


@router.post("/bands/{band_id}/polls", response_model=PollOut,
             status_code=status.HTTP_201_CREATED)
def create_poll(
    band_id: str,
    payload: PollCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    poll = DatePoll(band_id=band_id, title=payload.title.strip(), type=payload.type,
                    location=payload.location, notes=payload.notes,
                    token=secrets.token_urlsafe(18), created_by=membership.user_id)
    for i, o in enumerate(sorted(payload.options, key=lambda x: x.starts_at)):
        poll.options.append(DatePollOption(starts_at=o.starts_at, ends_at=o.ends_at, position=i))
    db.add(poll)
    db.commit()
    db.refresh(poll)
    return _poll_out(db, poll, with_token=True)


@router.get("/bands/{band_id}/polls/{poll_id}", response_model=PollOut)
def get_poll(
    band_id: str,
    poll_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    return _poll_out(db, _get_poll(db, band_id, poll_id), with_token=True)


@router.put("/bands/{band_id}/polls/{poll_id}/votes", response_model=PollOut)
def vote_poll(
    band_id: str,
    poll_id: str,
    payload: PollVotesIn,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    poll = _get_poll(db, band_id, poll_id)
    _apply_votes(db, poll, membership.user_id, payload)
    return _poll_out(db, poll, with_token=True)


@router.post("/bands/{band_id}/polls/{poll_id}/confirm", response_model=PollOut)
def confirm_poll(
    band_id: str,
    poll_id: str,
    payload: PollConfirm,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    poll = _get_poll(db, band_id, poll_id)
    if membership.role != "admin" and poll.created_by != membership.user_id:
        raise HTTPException(status_code=403, detail="Solo quien la creó o un admin la confirma")
    if poll.status != "open":
        raise HTTPException(status_code=409, detail="La votación ya está cerrada")
    opt = next((o for o in poll.options if o.id == payload.option_id), None)
    if opt is None:
        raise HTTPException(status_code=400, detail="Opción no válida")
    ev = Event(band_id=band_id, type=poll.type, title=poll.title, starts_at=opt.starts_at,
               ends_at=opt.ends_at, location=poll.location, notes=poll.notes,
               status="confirmed", created_by=membership.user_id)
    db.add(ev)
    db.flush()
    # Las respuestas de la opción elegida pasan a ser la asistencia del evento (nadie repite).
    for v in opt.votes:
        db.add(EventAttendance(event_id=ev.id, user_id=v.user_id, status=v.status))
    poll.status = "closed"
    poll.event_id = ev.id
    db.commit()
    db.refresh(poll)
    return _poll_out(db, poll, with_token=True)


@router.delete("/bands/{band_id}/polls/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poll(
    band_id: str,
    poll_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_editor),
):
    poll = _get_poll(db, band_id, poll_id)
    if membership.role != "admin" and poll.created_by != membership.user_id:
        raise HTTPException(status_code=403, detail="Solo quien la creó o un admin la borra")
    poll.deleted_at = _utcnow()
    db.commit()


def _public_poll(db: Session, token: str) -> DatePoll:
    p = (db.query(DatePoll)
         .join(Band, Band.id == DatePoll.band_id)
         .filter(DatePoll.token == token, DatePoll.deleted_at.is_(None),
                 Band.deleted_at.is_(None)).first())
    if p is None or len(token) < 16:
        raise HTTPException(status_code=404, detail="Votación no disponible")
    return p


@router.get("/public/polls/{token}", response_model=PollOut)
def public_poll(token: str, request: Request, db: Session = Depends(get_db)):
    check_rate(f"pub-poll:{request.client.host if request.client else '-'}", 120, 60)
    return _poll_out(db, _public_poll(db, token), with_token=False)


@router.put("/public/polls/{token}/votes", response_model=PollOut)
def public_vote(token: str, payload: PollVotesIn, request: Request,
                db: Session = Depends(get_db)):
    check_rate(f"pub-vote:{request.client.host if request.client else '-'}", 30, 60)
    poll = _public_poll(db, token)
    if not payload.user_id or active_membership(db, poll.band_id, payload.user_id) is None:
        raise HTTPException(status_code=400, detail="Elige tu nombre de la lista")
    _apply_votes(db, poll, payload.user_id, payload)
    return _poll_out(db, poll, with_token=False)


# ══ Feedback + eventos de producto (T-V6-94) ═══════════════════════════════════
@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def send_feedback(payload: FeedbackIn, request: Request, db: Session = Depends(get_db),
                  user_id: str = Depends(get_current_user)):
    check_rate(f"feedback:{user_id}", 10, 3600)
    ua = (request.headers.get("user-agent") or "")[:255]
    db.add(Feedback(user_id=user_id, body=payload.body.strip(), page=payload.page, user_agent=ua))
    db.commit()
    logger.info("Feedback recibido de %s en %s", user_id, payload.page)
    return {"ok": True}


@router.post("/me/product-events", status_code=status.HTTP_204_NO_CONTENT)
def product_event(payload: ProductEventIn, db: Session = Depends(get_db),
                  user_id: str = Depends(get_current_user)):
    check_rate(f"pevent:{user_id}", 120, 3600)
    band_id = payload.band_id
    if band_id and active_membership(db, band_id, user_id) is None:
        band_id = None  # no se registra contra una banda ajena
    db.add(ProductEvent(user_id=user_id, band_id=band_id, kind=payload.kind))
    db.commit()
