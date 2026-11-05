"""
V6-F9b — Red profesional (GUIA_MAESTRA_V6 §9.9): salas, bookers y profesionales; convocatorias de
bolos y candidaturas (I-20); EPK de banda y página pública (I-16/I-21); mensajes de contacto (I-3);
valoraciones con relación previa y reportes (I-22, §9.9.5); calendario de sala (I-23).

Reglas:
- Perfiles: los gestiona SOLO su dueño (`user_id`). Los listados públicos usan proyección segura
  (`ProProfileCard`): jamás teléfono ni user_id. El teléfono solo sale en la ficha, a usuarios con
  sesión, y si el dueño lo permite (`show_phone`).
- Convocatorias: solo perfiles `venue`/`booker`. Postula el ADMIN de una banda (con su EPK).
  "Elegir" crea el concierto en la agenda de esa banda (y la sala en sus Salas), declina el resto
  y abre una conversación con la banda.
- Rutas de banda con `require_band_member/admin` (regla de oro, test de aislamiento).
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.band_auth import active_membership, require_band_admin, require_band_member
from ..services.db import get_db
from ..services.models import (
    Band,
    BandEpk,
    BandMembership,
    ContactMessage,
    ContactThread,
    Event,
    GigApplication,
    GigCall,
    MusicianProfile,
    ProProfile,
    PublicScore,
    Report,
    Review,
    ScoreComment,
    Venue,
    _utcnow,
)
from ..services.notify import band_member_ids, notify
from ..services.ratelimit import check_rate
from ..services.schemas import (
    ContactIn,
    ContactMessageOut,
    ContactThreadOut,
    EpkIn,
    EpkOut,
    GigApplicationOut,
    GigApplicationPatch,
    GigApplyIn,
    GigCallIn,
    GigCallOut,
    GigCallUpdate,
    ProProfileCard,
    ProProfileIn,
    ProProfileOwn,
    ProProfilePublic,
    ProProfileUpdate,
    PublicBandOut,
    ReportIn,
    ReviewIn,
    ReviewOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["network"])

CALL_KINDS = ("venue", "booker")
AUTO_HIDE_REPORTS = 3


def _now():
    return _utcnow().replace(tzinfo=None)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "-"


# ── utilidades ────────────────────────────────────────────────────────────────
def _user_names(db: Session, ids) -> Dict[str, str]:
    ids = [i for i in set(ids) if i]
    if not ids:
        return {}
    return {i: (n or "Alguien") for i, n in db.query(MusicianProfile.id, MusicianProfile.display_name)
            .filter(MusicianProfile.id.in_(ids)).all()}


def _band_names(db: Session, ids) -> Dict[str, str]:
    ids = [i for i in set(ids) if i]
    if not ids:
        return {}
    return dict(db.query(Band.id, Band.name).filter(Band.id.in_(ids)).all())


def _ratings(db: Session, *, pro_ids=None, band_ids=None) -> Dict[str, tuple]:
    col = Review.to_pro_id if pro_ids is not None else Review.to_band_id
    ids = list(pro_ids if pro_ids is not None else band_ids)
    if not ids:
        return {}
    rows = (db.query(col, func.avg(Review.stars), func.count(Review.id))
            .filter(col.in_(ids), Review.hidden_at.is_(None)).group_by(col).all())
    return {k: (round(float(a), 1), int(c)) for k, a, c in rows}


def _reviews(db: Session, *, pro_id=None, band_id=None) -> List[ReviewOut]:
    q = db.query(Review).filter(Review.hidden_at.is_(None))
    q = q.filter(Review.to_pro_id == pro_id) if pro_id else q.filter(Review.to_band_id == band_id)
    rows = q.order_by(Review.created_at.desc()).limit(20).all()
    names = _user_names(db, [r.from_user_id for r in rows])
    return [ReviewOut(id=r.id, author_name=names.get(r.from_user_id, "Alguien"), stars=r.stars,
                      body=r.body, created_at=r.created_at) for r in rows]


def _open_calls_filter(q):
    now = _now()
    return q.filter(GigCall.status == "open", GigCall.deleted_at.is_(None),
                    or_(GigCall.deadline_at.is_(None), GigCall.deadline_at >= now))


def _visible_pros(db: Session):
    return db.query(ProProfile).filter(ProProfile.deleted_at.is_(None),
                                       ProProfile.hidden_at.is_(None))


def _card(p: ProProfile, ratings, open_calls) -> dict:
    avg, cnt = ratings.get(p.id, (None, 0))
    return dict(id=p.id, kind=p.kind, name=p.name, zone=p.zone,
                bio=(p.bio or "")[:280] or None, services=p.services, styles=p.styles,
                price_hint=p.price_hint, capacity=p.capacity, avatar_url=p.avatar_url,
                verified=p.verified_at is not None, rating_avg=avg, rating_count=cnt,
                open_calls=open_calls.get(p.id, 0))


def _open_calls_count(db: Session, pro_ids) -> Dict[str, int]:
    ids = list(pro_ids)
    if not ids:
        return {}
    q = db.query(GigCall.pro_profile_id, func.count(GigCall.id)).filter(
        GigCall.pro_profile_id.in_(ids))
    return dict(_open_calls_filter(q).group_by(GigCall.pro_profile_id).all())


def _full(db: Session, p: ProProfile, viewer: Optional[str], own: bool = False):
    r = _ratings(db, pro_ids=[p.id])
    data = _card(p, r, _open_calls_count(db, [p.id]))
    data.update(bio=p.bio, links=p.links, photos=p.photos, deal_types=p.deal_types,
                backline=p.backline, address=p.address,
                phone=p.phone if (viewer and (p.show_phone or p.user_id == viewer)) else None,
                reviews=_reviews(db, pro_id=p.id), is_mine=(viewer == p.user_id))
    if own:
        data.update(show_phone=p.show_phone, visibility=p.visibility, created_at=p.created_at)
        return ProProfileOwn(**data)
    return ProProfilePublic(**data)


def _my_pro(db: Session, pro_id: str, user_id: str) -> ProProfile:
    p = (db.query(ProProfile)
         .filter(ProProfile.id == pro_id, ProProfile.user_id == user_id,
                 ProProfile.deleted_at.is_(None)).first())
    if p is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return p


def _dump_links(payload_links):
    return [lk.model_dump() for lk in payload_links] if payload_links is not None else None


# ══ Perfiles (T-V6-96) ═════════════════════════════════════════════════════════
@router.get("/me/pro-profiles", response_model=List[ProProfileOwn])
def my_profiles(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    rows = (db.query(ProProfile)
            .filter(ProProfile.user_id == user_id, ProProfile.deleted_at.is_(None))
            .order_by(ProProfile.created_at).all())
    return [_full(db, p, user_id, own=True) for p in rows]


@router.post("/me/pro-profiles", response_model=ProProfileOwn, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProProfileIn, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    check_rate(f"pro-create:{user_id}", 10, 86400)
    n = db.query(ProProfile).filter(ProProfile.user_id == user_id,
                                    ProProfile.deleted_at.is_(None)).count()
    if n >= 10:
        raise HTTPException(status_code=400, detail="Máximo 10 perfiles por cuenta")
    data = payload.model_dump()
    data["links"] = _dump_links(payload.links)
    p = ProProfile(user_id=user_id, **data)
    db.add(p)
    db.commit()
    db.refresh(p)
    return _full(db, p, user_id, own=True)


@router.patch("/me/pro-profiles/{pro_id}", response_model=ProProfileOwn)
def update_profile(pro_id: str, payload: ProProfileUpdate, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    p = _my_pro(db, pro_id, user_id)
    data = payload.model_dump(exclude_unset=True)
    if "links" in data:
        data["links"] = _dump_links(payload.links)
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return _full(db, p, user_id, own=True)


@router.delete("/me/pro-profiles/{pro_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(pro_id: str, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    p = _my_pro(db, pro_id, user_id)
    p.deleted_at = _utcnow()
    for c in db.query(GigCall).filter(GigCall.pro_profile_id == p.id, GigCall.deleted_at.is_(None)):
        c.status = "closed"
    db.commit()


@router.get("/public/pros", response_model=List[ProProfileCard])
def list_pros(
    request: Request,
    kind: Optional[str] = Query(None, max_length=24),
    zone: Optional[str] = Query(None, max_length=100),
    q: Optional[str] = Query(None, max_length=100),
    limit: int = Query(24, ge=1, le=50),
    offset: int = Query(0, ge=0, le=5000),
    db: Session = Depends(get_db),
):
    check_rate(f"pub-pros:{_ip(request)}", 120, 60)
    qry = _visible_pros(db).filter(ProProfile.visibility == "public")
    if kind == "pros":  # todos menos salas
        qry = qry.filter(ProProfile.kind != "venue")
    elif kind:
        qry = qry.filter(ProProfile.kind == kind)
    if zone:
        qry = qry.filter(ProProfile.zone.ilike(f"%{zone.strip()}%"))
    if q:
        like = f"%{q.strip()}%"
        qry = qry.filter(or_(ProProfile.name.ilike(like), ProProfile.bio.ilike(like)))
    rows = (qry.order_by(ProProfile.verified_at.is_(None), ProProfile.updated_at.desc())
            .offset(offset).limit(limit).all())
    ids = [p.id for p in rows]
    ratings, calls = _ratings(db, pro_ids=ids), _open_calls_count(db, ids)
    return [ProProfileCard(**_card(p, ratings, calls)) for p in rows]


@router.get("/public/pros/{pro_id}", response_model=ProProfilePublic)
def public_pro(pro_id: str, request: Request, db: Session = Depends(get_db)):
    check_rate(f"pub-pro:{_ip(request)}", 120, 60)
    p = _visible_pros(db).filter(ProProfile.id == pro_id,
                                 ProProfile.visibility.in_(("public", "unlisted"))).first()
    if p is None:
        raise HTTPException(status_code=404, detail="Perfil no disponible")
    return _full(db, p, None)


@router.get("/pros/{pro_id}", response_model=ProProfilePublic)
def get_pro(pro_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    p = _visible_pros(db).filter(ProProfile.id == pro_id).first()
    if p is None or (p.visibility == "private" and p.user_id != user_id):
        raise HTTPException(status_code=404, detail="Perfil no disponible")
    return _full(db, p, user_id)


# ══ Convocatorias (T-V6-97) ════════════════════════════════════════════════════
def _call_out(db: Session, c: GigCall, *, owner_view=False, viewer: Optional[str] = None,
              pro: Optional[ProProfile] = None) -> GigCallOut:
    pro = pro or db.get(ProProfile, c.pro_profile_id)
    out = GigCallOut(
        id=c.id, pro_profile_id=c.pro_profile_id, venue_name=pro.name if pro else None,
        venue_kind=pro.kind if pro else None, venue_verified=bool(pro and pro.verified_at),
        title=c.title, description=c.description, starts_at=c.starts_at, ends_at=c.ends_at,
        flexible_dates=c.flexible_dates, styles=c.styles, format=c.format, deal_type=c.deal_type,
        fee=c.fee, conditions=c.conditions, zone=c.zone, deadline_at=c.deadline_at,
        status=c.status, created_at=c.created_at)
    if owner_view:
        out.applications = db.query(GigApplication).filter(
            GigApplication.gig_call_id == c.id).count()
    if viewer:
        my_bands = [b for (b,) in db.query(BandMembership.band_id).filter(
            BandMembership.user_id == viewer, BandMembership.status == "active").all()]
        if my_bands:
            out.my_applications = [
                {"band_id": a.band_id, "status": a.status, "id": a.id}
                for a in db.query(GigApplication).filter(
                    GigApplication.gig_call_id == c.id, GigApplication.band_id.in_(my_bands))]
    return out


def _my_call(db: Session, call_id: str, user_id: str) -> tuple:
    row = (db.query(GigCall, ProProfile).join(ProProfile, ProProfile.id == GigCall.pro_profile_id)
           .filter(GigCall.id == call_id, GigCall.deleted_at.is_(None),
                   ProProfile.user_id == user_id).first())
    if row is None:
        raise HTTPException(status_code=404, detail="Convocatoria no encontrada")
    return row


@router.post("/me/pro-profiles/{pro_id}/gig-calls", response_model=GigCallOut,
             status_code=status.HTTP_201_CREATED)
def create_call(pro_id: str, payload: GigCallIn, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    p = _my_pro(db, pro_id, user_id)
    if p.kind not in CALL_KINDS:
        raise HTTPException(status_code=400, detail="Solo salas y bookers publican convocatorias")
    check_rate(f"call-create:{user_id}", 20, 86400)
    data = payload.model_dump()
    if not data.get("zone"):
        data["zone"] = p.zone
    c = GigCall(pro_profile_id=p.id, **data)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _call_out(db, c, owner_view=True, pro=p)


@router.get("/me/gig-calls", response_model=List[GigCallOut])
def my_calls(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    rows = (db.query(GigCall, ProProfile).join(ProProfile, ProProfile.id == GigCall.pro_profile_id)
            .filter(ProProfile.user_id == user_id, GigCall.deleted_at.is_(None),
                    ProProfile.deleted_at.is_(None))
            .order_by(GigCall.created_at.desc()).limit(100).all())
    return [_call_out(db, c, owner_view=True, pro=p) for c, p in rows]


@router.patch("/me/gig-calls/{call_id}", response_model=GigCallOut)
def update_call(call_id: str, payload: GigCallUpdate, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    c, p = _my_call(db, call_id, user_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return _call_out(db, c, owner_view=True, pro=p)


@router.delete("/me/gig-calls/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call(call_id: str, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    c, _ = _my_call(db, call_id, user_id)
    c.deleted_at = _utcnow()
    c.status = "closed"
    db.commit()


@router.get("/public/gig-calls", response_model=List[GigCallOut])
def list_calls(
    request: Request,
    zone: Optional[str] = Query(None, max_length=100),
    style: Optional[str] = Query(None, max_length=40),
    q: Optional[str] = Query(None, max_length=100),
    limit: int = Query(24, ge=1, le=50),
    offset: int = Query(0, ge=0, le=5000),
    db: Session = Depends(get_db),
):
    check_rate(f"pub-calls:{_ip(request)}", 120, 60)
    qry = _open_calls_filter(db.query(GigCall, ProProfile).join(
        ProProfile, ProProfile.id == GigCall.pro_profile_id)).filter(
        ProProfile.deleted_at.is_(None), ProProfile.hidden_at.is_(None),
        ProProfile.visibility != "private")
    if zone:
        qry = qry.filter(GigCall.zone.ilike(f"%{zone.strip()}%"))
    if q:
        like = f"%{q.strip()}%"
        qry = qry.filter(or_(GigCall.title.ilike(like), GigCall.description.ilike(like),
                             ProProfile.name.ilike(like)))
    rows = qry.order_by(GigCall.starts_at.is_(None), GigCall.starts_at.asc(),
                        GigCall.created_at.desc()).offset(offset).limit(200 if style else limit).all()
    out = [_call_out(db, c, pro=p) for c, p in rows]
    if style:  # JSON portable: filtramos en Python (pocas filas, ya paginadas)
        s = style.strip().lower()
        out = [c for c in out if any(s in (t or "").lower() for t in (c.styles or []))][:limit]
    return out


@router.get("/public/gig-calls/{call_id}", response_model=GigCallOut)
def public_call(call_id: str, request: Request, db: Session = Depends(get_db)):
    check_rate(f"pub-call:{_ip(request)}", 120, 60)
    row = (db.query(GigCall, ProProfile).join(ProProfile, ProProfile.id == GigCall.pro_profile_id)
           .filter(GigCall.id == call_id, GigCall.deleted_at.is_(None),
                   ProProfile.deleted_at.is_(None), ProProfile.hidden_at.is_(None)).first())
    if row is None:
        raise HTTPException(status_code=404, detail="Convocatoria no disponible")
    return _call_out(db, row[0], pro=row[1])


@router.get("/gig-calls/{call_id}", response_model=GigCallOut)
def get_call(call_id: str, db: Session = Depends(get_db),
             user_id: str = Depends(get_current_user)):
    row = (db.query(GigCall, ProProfile).join(ProProfile, ProProfile.id == GigCall.pro_profile_id)
           .filter(GigCall.id == call_id, GigCall.deleted_at.is_(None),
                   ProProfile.deleted_at.is_(None)).first())
    if row is None or (row[1].hidden_at and row[1].user_id != user_id):
        raise HTTPException(status_code=404, detail="Convocatoria no disponible")
    return _call_out(db, row[0], viewer=user_id, pro=row[1],
                     owner_view=row[1].user_id == user_id)


# ── Candidaturas ──────────────────────────────────────────────────────────────
def _epk_dict(db: Session, band: Band) -> dict:
    e = db.get(BandEpk, band.id)
    d = {"name": band.name, "avatar_url": band.avatar_url}
    if e is not None:
        d.update(bio=e.bio, styles=e.styles, formation=e.formation, zone=e.zone, links=e.links,
                 photos=e.photos, fee_hint=e.fee_hint, rider_notes=e.rider_notes)
    return d


def _app_out(db: Session, a: GigApplication, call: Optional[GigCall] = None,
             pro: Optional[ProProfile] = None, band_name: Optional[str] = None) -> GigApplicationOut:
    call = call or db.get(GigCall, a.gig_call_id)
    pro = pro or (db.get(ProProfile, call.pro_profile_id) if call else None)
    return GigApplicationOut(
        id=a.id, gig_call_id=a.gig_call_id, call_title=call.title if call else None,
        venue_name=pro.name if pro else None, starts_at=call.starts_at if call else None,
        band_id=a.band_id, band_name=band_name or db.query(Band.name).filter(
            Band.id == a.band_id).scalar(),
        message=a.message, epk=a.epk_snapshot, status=a.status, event_id=a.event_id,
        created_at=a.created_at)


def _thread_for(db: Session, *, initiator_id: str, initiator_band_id=None, target_pro_id=None,
                target_band_id=None, context_kind=None, context_id=None) -> ContactThread:
    q = db.query(ContactThread).filter(ContactThread.initiator_id == initiator_id)
    q = q.filter(ContactThread.target_pro_id == target_pro_id) if target_pro_id \
        else q.filter(ContactThread.target_pro_id.is_(None))
    q = q.filter(ContactThread.target_band_id == target_band_id) if target_band_id \
        else q.filter(ContactThread.target_band_id.is_(None))
    t = q.first()
    if t is None:
        t = ContactThread(initiator_id=initiator_id, initiator_band_id=initiator_band_id,
                          target_pro_id=target_pro_id, target_band_id=target_band_id,
                          context_kind=context_kind, context_id=context_id)
        db.add(t)
        db.flush()
    elif context_kind:
        t.context_kind, t.context_id = context_kind, context_id
    return t


def _post(db: Session, t: ContactThread, author_id: str, body: str) -> ContactMessage:
    m = ContactMessage(thread_id=t.id, author_id=author_id, body=body.strip())
    db.add(m)
    t.last_message_at = _utcnow()
    # Aviso a los demás participantes (T-V6-61)
    others = {t.initiator_id}
    if t.target_pro_id:
        others.add(db.query(ProProfile.user_id).filter(ProProfile.id == t.target_pro_id).scalar())
    for bid in (t.target_band_id, t.initiator_band_id):
        if bid:
            others.update(band_member_ids(db, bid))
    others.discard(author_id)
    notify(db, others, kind="message", title="Mensaje nuevo en Explorar", body=body.strip()[:200],
           link=f"red.html#mensajes/{t.id}")
    return m


@router.post("/bands/{band_id}/gig-applications", response_model=GigApplicationOut,
             status_code=status.HTTP_201_CREATED)
def apply_to_call(band_id: str, payload: GigApplyIn, db: Session = Depends(get_db),
                  membership: BandMembership = Depends(require_band_admin)):
    check_rate(f"apply:{band_id}", 30, 86400)
    row = (_open_calls_filter(db.query(GigCall, ProProfile).join(
        ProProfile, ProProfile.id == GigCall.pro_profile_id))
        .filter(GigCall.id == payload.gig_call_id, ProProfile.deleted_at.is_(None),
                ProProfile.hidden_at.is_(None)).first())
    if row is None:
        raise HTTPException(status_code=404, detail="La convocatoria no existe o ya está cerrada")
    call, pro = row
    if db.query(GigApplication).filter(GigApplication.gig_call_id == call.id,
                                       GigApplication.band_id == band_id).first():
        raise HTTPException(status_code=409, detail="Tu banda ya se ha postulado a esta convocatoria")
    band = db.get(Band, band_id)
    a = GigApplication(gig_call_id=call.id, band_id=band_id, applied_by=membership.user_id,
                       message=(payload.message or "").strip() or None,
                       epk_snapshot=_epk_dict(db, band))
    db.add(a)
    # La sala recibe la candidatura también como mensaje (abre la conversación, I-20 → I-3).
    t = _thread_for(db, initiator_id=membership.user_id, initiator_band_id=band_id,
                    target_pro_id=pro.id, context_kind="gig_call", context_id=call.id)
    _post(db, t, membership.user_id,
          f"Candidatura de «{band.name}» para «{call.title}»."
          + (f"\n\n{a.message}" if a.message else ""))
    notify(db, [pro.user_id], kind="gig_application",
           title=f"Nueva candidatura: {band.name}", body=f"Para «{call.title}».",
           link="red.html#mios")
    db.commit()
    db.refresh(a)
    return _app_out(db, a, call, pro, band.name)


@router.get("/bands/{band_id}/gig-applications", response_model=List[GigApplicationOut])
def band_applications(band_id: str, db: Session = Depends(get_db),
                      membership: BandMembership = Depends(require_band_member)):
    rows = (db.query(GigApplication).filter(GigApplication.band_id == band_id)
            .order_by(GigApplication.created_at.desc()).limit(100).all())
    name = db.query(Band.name).filter(Band.id == band_id).scalar()
    return [_app_out(db, a, band_name=name) for a in rows]


@router.delete("/bands/{band_id}/gig-applications/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_application(band_id: str, app_id: str, db: Session = Depends(get_db),
                         membership: BandMembership = Depends(require_band_admin)):
    a = (db.query(GigApplication)
         .filter(GigApplication.id == app_id, GigApplication.band_id == band_id).first())
    if a is None:
        raise HTTPException(status_code=404, detail="Candidatura no encontrada")
    if a.status == "chosen":
        raise HTTPException(status_code=409, detail="Ya os han elegido: cancélalo desde la agenda")
    db.delete(a)
    db.commit()


@router.get("/me/gig-calls/{call_id}/applications", response_model=List[GigApplicationOut])
def call_applications(call_id: str, db: Session = Depends(get_db),
                      user_id: str = Depends(get_current_user)):
    call, pro = _my_call(db, call_id, user_id)
    rows = (db.query(GigApplication).filter(GigApplication.gig_call_id == call.id)
            .order_by(GigApplication.created_at).all())
    names = _band_names(db, [a.band_id for a in rows])
    changed = False
    for a in rows:
        if a.status == "sent":
            a.status, changed = "seen", True
    if changed:
        db.commit()
    return [_app_out(db, a, call, pro, names.get(a.band_id)) for a in rows]


@router.patch("/me/gig-calls/{call_id}/applications/{app_id}", response_model=GigApplicationOut)
def patch_application(call_id: str, app_id: str, payload: GigApplicationPatch,
                      db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    call, pro = _my_call(db, call_id, user_id)
    a = (db.query(GigApplication)
         .filter(GigApplication.id == app_id, GigApplication.gig_call_id == call.id).first())
    if a is None:
        raise HTTPException(status_code=404, detail="Candidatura no encontrada")
    if a.status == "chosen":
        raise HTTPException(status_code=409, detail="Esta banda ya está elegida")
    a.status = payload.status
    db.commit()
    db.refresh(a)
    return _app_out(db, a, call, pro)


@router.post("/me/gig-calls/{call_id}/applications/{app_id}/choose",
             response_model=GigApplicationOut)
def choose_application(call_id: str, app_id: str, db: Session = Depends(get_db),
                       user_id: str = Depends(get_current_user)):
    call, pro = _my_call(db, call_id, user_id)
    a = (db.query(GigApplication)
         .filter(GigApplication.id == app_id, GigApplication.gig_call_id == call.id).first())
    if a is None:
        raise HTTPException(status_code=404, detail="Candidatura no encontrada")
    if call.status == "filled" or a.status == "chosen":
        raise HTTPException(status_code=409, detail="Ya elegiste banda para esta convocatoria")
    band = db.query(Band).filter(Band.id == a.band_id, Band.deleted_at.is_(None)).first()
    if band is None:
        raise HTTPException(status_code=409, detail="Esa banda ya no existe")
    venue_id = None
    if pro.kind == "venue":
        # La sala entra en las Salas de la banda (reutiliza si ya la tenía por nombre).
        v = (db.query(Venue).filter(Venue.band_id == band.id, Venue.name == pro.name,
                                    Venue.deleted_at.is_(None)).first())
        if v is None:
            v = Venue(band_id=band.id, name=pro.name, address=pro.address, city=pro.zone,
                      capacity=pro.capacity, contact=pro.name)
            db.add(v)
            db.flush()
        venue_id = v.id
    ev = Event(band_id=band.id, type="concert", title=f"{call.title} · {pro.name}",
               starts_at=call.starts_at, ends_at=call.ends_at,
               location=pro.address or pro.zone, notes=call.conditions,
               status="confirmed", fee=call.fee, venue_id=venue_id,
               contact_name=pro.name, created_by=a.applied_by)
    db.add(ev)
    db.flush()
    a.status, a.event_id = "chosen", ev.id
    for other in db.query(GigApplication).filter(GigApplication.gig_call_id == call.id,
                                                 GigApplication.id != a.id):
        if other.status != "declined":
            other.status = "declined"
    call.status = "filled"
    t = _thread_for(db, initiator_id=a.applied_by, initiator_band_id=band.id,
                    target_pro_id=pro.id, context_kind="gig_call", context_id=call.id)
    _post(db, t, user_id, f"¡Os hemos elegido para «{call.title}»! El concierto ya está en vuestra "
                          "agenda. Escribidnos por aquí para cerrar detalles.")
    notify(db, band_member_ids(db, band.id), kind="gig_chosen",
           title=f"¡{pro.name} os ha elegido!", body=f"«{call.title}» ya está en la agenda.",
           link=f"band.html?id={band.id}", band_id=band.id)
    db.commit()
    db.refresh(a)
    return _app_out(db, a, call, pro, band.name)


@router.get("/me/pro-profiles/{pro_id}/calendar")
def venue_calendar(pro_id: str, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user)):
    """Calendario de sala (T-V6-100, I-23): convocatorias + bolos cerrados con banda."""
    p = _my_pro(db, pro_id, user_id)
    items = []
    for c in db.query(GigCall).filter(GigCall.pro_profile_id == p.id,
                                      GigCall.deleted_at.is_(None)):
        chosen = (db.query(GigApplication).filter(GigApplication.gig_call_id == c.id,
                                                  GigApplication.status == "chosen").first())
        items.append({
            "date": c.starts_at.isoformat() if c.starts_at else None,
            "kind": "gig" if chosen else "call", "title": c.title, "status": c.status,
            "call_id": c.id,
            "band_name": db.query(Band.name).filter(Band.id == chosen.band_id).scalar()
            if chosen else None,
        })
    items.sort(key=lambda i: (i["date"] is None, i["date"] or ""))
    return items


# ══ EPK + página pública de banda (T-V6-98) ════════════════════════════════════
@router.get("/bands/{band_id}/epk", response_model=EpkOut)
def get_epk(band_id: str, db: Session = Depends(get_db),
            membership: BandMembership = Depends(require_band_member)):
    e = db.get(BandEpk, band_id)
    return e or EpkOut(band_id=band_id)


@router.put("/bands/{band_id}/epk", response_model=EpkOut)
def put_epk(band_id: str, payload: EpkIn, db: Session = Depends(get_db),
            membership: BandMembership = Depends(require_band_admin)):
    e = db.get(BandEpk, band_id)
    if e is None:
        e = BandEpk(band_id=band_id)
        db.add(e)
    data = payload.model_dump(exclude_unset=True)
    if "links" in data:
        data["links"] = _dump_links(payload.links)
    for k, v in data.items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return e


@router.get("/public/bands/{target_band_id}", response_model=PublicBandOut)
def public_band(target_band_id: str, request: Request, db: Session = Depends(get_db)):
    band_id = target_band_id
    check_rate(f"pub-band:{_ip(request)}", 120, 60)
    band = db.query(Band).filter(Band.id == band_id, Band.deleted_at.is_(None)).first()
    e = db.get(BandEpk, band_id) if band else None
    if band is None or e is None or not e.is_public:
        raise HTTPException(status_code=404, detail="Banda no disponible")
    now = _now()
    evs = (db.query(Event).filter(Event.band_id == band_id, Event.deleted_at.is_(None),
                                  Event.visibility == "public", Event.starts_at >= now,
                                  Event.status != "cancelled")
           .order_by(Event.starts_at).limit(10).all())
    r = _ratings(db, band_ids=[band_id]).get(band_id, (None, 0))
    epk = EpkOut.model_validate(e)
    epk.rider_notes = None  # el rider se comparte en la candidatura, no en público
    return PublicBandOut(
        id=band.id, name=band.name, avatar_url=band.avatar_url, cover_url=band.cover_url, epk=epk,
        upcoming=[{"id": ev.id, "title": ev.title, "starts_at": ev.starts_at, "type": ev.type}
                  for ev in evs],
        rating_avg=r[0], rating_count=r[1], reviews=_reviews(db, band_id=band_id))


# ══ Mensajes de contacto (I-3) ═════════════════════════════════════════════════
def _participant(db: Session, t: ContactThread, user_id: str) -> bool:
    if t.initiator_id == user_id:
        return True
    if t.target_pro_id:
        owner = db.query(ProProfile.user_id).filter(ProProfile.id == t.target_pro_id).scalar()
        if owner == user_id:
            return True
    for bid in (t.target_band_id, t.initiator_band_id):
        if bid and active_membership(db, bid, user_id) is not None:
            return True
    return False


def _thread_title(db: Session, t: ContactThread, user_id: str) -> tuple:
    """Desde mi lado: con quién hablo."""
    pro = db.get(ProProfile, t.target_pro_id) if t.target_pro_id else None
    i_am_target = (pro is not None and pro.user_id == user_id) or (
        t.target_band_id and active_membership(db, t.target_band_id, user_id) is not None)
    if i_am_target:
        if t.initiator_band_id:
            name = db.query(Band.name).filter(Band.id == t.initiator_band_id).scalar() or "Banda"
            who = _user_names(db, [t.initiator_id]).get(t.initiator_id, "Alguien")
            return name, f"{who} · a {pro.name if pro else 'tu banda'}"
        return _user_names(db, [t.initiator_id]).get(t.initiator_id, "Alguien"), \
            (pro.name if pro else None)
    if pro is not None:
        return pro.name, None
    return db.query(Band.name).filter(Band.id == t.target_band_id).scalar() or "Banda", None


def _relationship_ok(db: Session, t: ContactThread, me: str) -> bool:
    """Hubo conversación de ida y vuelta (el otro lado respondió)."""
    authors = {a for (a,) in db.query(ContactMessage.author_id).filter(
        ContactMessage.thread_id == t.id).distinct()}
    return any(a != me for a in authors) and me in authors


def _thread_out(db: Session, t: ContactThread, user_id: str, with_messages=False):
    title, subtitle = _thread_title(db, t, user_id)
    out = ContactThreadOut(id=t.id, title=title, subtitle=subtitle, context_kind=t.context_kind,
                           context_id=t.context_id, last_message_at=t.last_message_at)
    last = (db.query(ContactMessage).filter(ContactMessage.thread_id == t.id)
            .order_by(ContactMessage.created_at.desc()).first())
    out.last_message = (last.body[:140] if last else None)
    if with_messages:
        msgs = (db.query(ContactMessage).filter(ContactMessage.thread_id == t.id)
                .order_by(ContactMessage.created_at).limit(500).all())
        names = _user_names(db, [m.author_id for m in msgs])
        out.messages = [ContactMessageOut(id=m.id, author_id=m.author_id,
                                          author_name=names.get(m.author_id, "Alguien"),
                                          mine=m.author_id == user_id, body=m.body,
                                          created_at=m.created_at) for m in msgs]
        if _relationship_ok(db, t, user_id):
            pro = db.get(ProProfile, t.target_pro_id) if t.target_pro_id else None
            if pro is not None and pro.user_id != user_id:
                out.can_review, out.review_target = True, {"kind": "pro", "id": pro.id}
            elif pro is not None and t.initiator_band_id:
                out.can_review = True
                out.review_target = {"kind": "band", "id": t.initiator_band_id}
            elif t.target_band_id and active_membership(db, t.target_band_id, user_id) is None:
                out.can_review = True
                out.review_target = {"kind": "band", "id": t.target_band_id}
    return out


@router.post("/pros/{pro_id}/contact", response_model=ContactThreadOut,
             status_code=status.HTTP_201_CREATED)
def contact_pro(pro_id: str, payload: ContactIn, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    p = _visible_pros(db).filter(ProProfile.id == pro_id).first()
    if p is None:
        raise HTTPException(status_code=404, detail="Perfil no disponible")
    if p.user_id == user_id:
        raise HTTPException(status_code=400, detail="Es tu propio perfil")
    if payload.as_band_id and active_membership(db, payload.as_band_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Banda no encontrada")
    check_rate(f"contact-msg:{user_id}", 60, 3600)
    exists = db.query(ContactThread).filter(ContactThread.initiator_id == user_id,
                                            ContactThread.target_pro_id == pro_id).first()
    if exists is None:
        check_rate(f"contact-new:{user_id}", 15, 86400)  # anti-spam: conversaciones nuevas/día
    t = _thread_for(db, initiator_id=user_id, initiator_band_id=payload.as_band_id,
                    target_pro_id=pro_id, context_kind="gig_call" if payload.gig_call_id else
                    ("venue" if p.kind == "venue" else "pro"),
                    context_id=payload.gig_call_id or pro_id)
    _post(db, t, user_id, payload.body)
    db.commit()
    return _thread_out(db, t, user_id, with_messages=True)


@router.post("/network/bands/{target_band_id}/contact", response_model=ContactThreadOut,
             status_code=status.HTTP_201_CREATED)
def contact_band(target_band_id: str, payload: ContactIn, db: Session = Depends(get_db),
                 user_id: str = Depends(get_current_user)):
    """Escribir a una banda con EPK público (salas/profesionales → banda, I-21 inverso).
    NO es una ruta "de banda" (no exige pertenencia): por eso no lleva `{band_id}`."""
    band_id = target_band_id
    band = db.query(Band).filter(Band.id == band_id, Band.deleted_at.is_(None)).first()
    e = db.get(BandEpk, band_id) if band else None
    if band is None or e is None or not e.is_public:
        raise HTTPException(status_code=404, detail="Banda no disponible")
    if active_membership(db, band_id, user_id) is not None:
        raise HTTPException(status_code=400, detail="Es tu propia banda")
    check_rate(f"contact-msg:{user_id}", 60, 3600)
    exists = db.query(ContactThread).filter(ContactThread.initiator_id == user_id,
                                            ContactThread.target_band_id == band_id).first()
    if exists is None:
        check_rate(f"contact-new:{user_id}", 15, 86400)
    t = _thread_for(db, initiator_id=user_id, target_band_id=band_id, context_kind="band",
                    context_id=band_id)
    _post(db, t, user_id, payload.body)
    db.commit()
    return _thread_out(db, t, user_id, with_messages=True)


@router.get("/me/threads", response_model=List[ContactThreadOut])
def my_threads(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    my_pros = [i for (i,) in db.query(ProProfile.id).filter(ProProfile.user_id == user_id).all()]
    my_bands = [b for (b,) in db.query(BandMembership.band_id).filter(
        BandMembership.user_id == user_id, BandMembership.status == "active").all()]
    conds = [ContactThread.initiator_id == user_id]
    if my_pros:
        conds.append(ContactThread.target_pro_id.in_(my_pros))
    if my_bands:
        conds.append(ContactThread.target_band_id.in_(my_bands))
        conds.append(ContactThread.initiator_band_id.in_(my_bands))
    rows = (db.query(ContactThread).filter(or_(*conds))
            .order_by(ContactThread.last_message_at.desc()).limit(100).all())
    return [_thread_out(db, t, user_id) for t in rows]


def _get_thread(db: Session, thread_id: str, user_id: str) -> ContactThread:
    t = db.get(ContactThread, thread_id)
    if t is None or not _participant(db, t, user_id):
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return t


@router.get("/me/threads/{thread_id}", response_model=ContactThreadOut)
def get_thread(thread_id: str, db: Session = Depends(get_db),
               user_id: str = Depends(get_current_user)):
    return _thread_out(db, _get_thread(db, thread_id, user_id), user_id, with_messages=True)


@router.post("/me/threads/{thread_id}/messages", response_model=ContactThreadOut)
def reply_thread(thread_id: str, payload: ContactIn, db: Session = Depends(get_db),
                 user_id: str = Depends(get_current_user)):
    t = _get_thread(db, thread_id, user_id)
    check_rate(f"contact-msg:{user_id}", 60, 3600)
    _post(db, t, user_id, payload.body)
    db.commit()
    return _thread_out(db, t, user_id, with_messages=True)


# ══ Valoraciones y reportes (T-V6-99) ══════════════════════════════════════════
def _chosen_between(db: Session, pro_id: str, band_id: str) -> bool:
    return db.query(GigApplication).join(GigCall, GigCall.id == GigApplication.gig_call_id).filter(
        GigCall.pro_profile_id == pro_id, GigApplication.band_id == band_id,
        GigApplication.status == "chosen").first() is not None


@router.post("/pros/{pro_id}/reviews", response_model=ReviewOut)
def review_pro(pro_id: str, payload: ReviewIn, db: Session = Depends(get_db),
               user_id: str = Depends(get_current_user)):
    p = _visible_pros(db).filter(ProProfile.id == pro_id).first()
    if p is None:
        raise HTTPException(status_code=404, detail="Perfil no disponible")
    if p.user_id == user_id:
        raise HTTPException(status_code=400, detail="No puedes valorar tu propio perfil")
    threads = db.query(ContactThread).filter(ContactThread.target_pro_id == pro_id).all()
    ok = any(_participant(db, t, user_id) and _relationship_ok(db, t, user_id) for t in threads)
    if not ok:
        my_bands = [b for (b,) in db.query(BandMembership.band_id).filter(
            BandMembership.user_id == user_id, BandMembership.status == "active").all()]
        ok = any(_chosen_between(db, pro_id, b) for b in my_bands)
    if not ok:
        raise HTTPException(status_code=403,
                            detail="Solo puedes valorar a quien hayas tratado por BandFlow")
    r = db.query(Review).filter(Review.from_user_id == user_id, Review.to_pro_id == pro_id).first()
    if r is None:
        r = Review(from_user_id=user_id, to_pro_id=pro_id, stars=payload.stars)
        db.add(r)
    r.stars, r.body = payload.stars, (payload.body or "").strip() or None
    db.commit()
    db.refresh(r)
    return ReviewOut(id=r.id, author_name=_user_names(db, [user_id]).get(user_id), stars=r.stars,
                     body=r.body, created_at=r.created_at)


@router.post("/network/bands/{target_band_id}/reviews", response_model=ReviewOut)
def review_band(target_band_id: str, payload: ReviewIn, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user)):
    band_id = target_band_id
    if db.query(Band).filter(Band.id == band_id, Band.deleted_at.is_(None)).first() is None:
        raise HTTPException(status_code=404, detail="Banda no disponible")
    if active_membership(db, band_id, user_id) is not None:
        raise HTTPException(status_code=400, detail="No puedes valorar tu propia banda")
    my_pros = [i for (i,) in db.query(ProProfile.id).filter(ProProfile.user_id == user_id,
                                                            ProProfile.deleted_at.is_(None)).all()]
    ok = any(_chosen_between(db, pid, band_id) for pid in my_pros)
    if not ok:
        threads = db.query(ContactThread).filter(or_(
            ContactThread.target_band_id == band_id,
            ContactThread.initiator_band_id == band_id)).all()
        ok = any(_participant(db, t, user_id) and _relationship_ok(db, t, user_id)
                 for t in threads)
    if not ok:
        raise HTTPException(status_code=403,
                            detail="Solo puedes valorar a quien hayas tratado por BandFlow")
    r = db.query(Review).filter(Review.from_user_id == user_id,
                                Review.to_band_id == band_id).first()
    if r is None:
        r = Review(from_user_id=user_id, to_band_id=band_id, stars=payload.stars)
        db.add(r)
    r.stars, r.body = payload.stars, (payload.body or "").strip() or None
    db.commit()
    db.refresh(r)
    return ReviewOut(id=r.id, author_name=_user_names(db, [user_id]).get(user_id), stars=r.stars,
                     body=r.body, created_at=r.created_at)


@router.post("/reports", status_code=status.HTTP_201_CREATED)
def report(payload: ReportIn, db: Session = Depends(get_db),
           user_id: str = Depends(get_current_user)):
    check_rate(f"report:{user_id}", 10, 86400)
    db.add(Report(reporter_id=user_id, target_kind=payload.target_kind,
                  target_id=payload.target_id, reason=payload.reason.strip()))
    db.flush()
    # Moderación automática mínima: N reporteros distintos ocultan el perfil/la reseña hasta revisión.
    distinct = (db.query(func.count(func.distinct(Report.reporter_id)))
                .filter(Report.target_kind == payload.target_kind,
                        Report.target_id == payload.target_id,
                        Report.resolved_at.is_(None)).scalar())
    if distinct >= AUTO_HIDE_REPORTS:
        if payload.target_kind == "score":   # catálogo (T-V6-66): se oculta hasta revisión
            sc = db.get(PublicScore, payload.target_id)
            if sc is not None and sc.status == "published":
                sc.status = "hidden"
                logger.warning("Partitura %s oculta por %d reportes", sc.id, distinct)
        if payload.target_kind == "comment":
            cm = db.get(ScoreComment, payload.target_id)
            if cm is not None and cm.deleted_at is None:
                cm.deleted_at = _utcnow()
        target = {"pro": ProProfile, "review": Review}.get(payload.target_kind)
        obj = db.get(target, payload.target_id) if target else None
        if obj is not None and obj.hidden_at is None:
            obj.hidden_at = _utcnow()
            logger.warning("Ocultado %s %s por %d reportes", payload.target_kind,
                           payload.target_id, distinct)
    db.commit()
    return {"ok": True}

