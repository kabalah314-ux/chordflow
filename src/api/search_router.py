"""
Búsqueda global (T-V6-67, Ctrl+K): canciones (mías y de mis bandas), setlists, eventos y bandas.
Todo filtrado por lo que el usuario puede ver (dueño o miembro activo). Máx. 8 por tipo.
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..services.auth import get_current_user
from ..services.db import get_db
from ..services.models import Band, BandMembership, Event, Setlist, Song

router = APIRouter(tags=["search"])


@router.get("/me/search")
def search(q: str = Query(..., min_length=1, max_length=80), db: Session = Depends(get_db),
           user_id: str = Depends(get_current_user)) -> List[dict]:
    like = f"%{q.strip()}%"
    bands = dict(db.query(Band.id, Band.name).join(BandMembership, BandMembership.band_id == Band.id)
                 .filter(BandMembership.user_id == user_id, BandMembership.status == "active",
                         Band.deleted_at.is_(None)).all())
    bids = list(bands) or [""]
    out: List[dict] = []
    for b_id, name in bands.items():
        if q.strip().lower() in (name or "").lower():
            out.append({"kind": "band", "title": name, "subtitle": "Banda",
                        "href": f"band.html?id={b_id}"})
    songs = (db.query(Song).filter(Song.deleted_at.is_(None),
                                   or_(Song.owner_id == user_id, Song.band_id.in_(bids)),
                                   or_(Song.title.ilike(like), Song.artist.ilike(like)))
             .order_by(Song.updated_at.desc()).limit(8).all())
    for s in songs:
        if s.band_id and s.band_id not in bands:
            continue
        out.append({"kind": "song", "title": s.title,
                    "subtitle": " · ".join(x for x in (s.artist, bands.get(s.band_id, "Personal")) if x),
                    "href": f"index.html?songId={s.id}"})
    sls = (db.query(Setlist).filter(Setlist.deleted_at.is_(None), Setlist.name.ilike(like),
                                    or_(Setlist.band_id.in_(bids),
                                        (Setlist.band_id.is_(None)) & (Setlist.owner_id == user_id)))
           .limit(8).all())
    for sl in sls:
        out.append({"kind": "setlist", "title": sl.name,
                    "subtitle": f"Setlist · {bands.get(sl.band_id, 'Personal')}",
                    "href": f"band.html?id={sl.band_id}" if sl.band_id else "setlists.html"})
    evs = (db.query(Event).filter(Event.deleted_at.is_(None), Event.band_id.in_(bids),
                                  or_(Event.title.ilike(like), Event.location.ilike(like)))
           .order_by(Event.starts_at.desc()).limit(8).all())
    for e in evs:
        out.append({"kind": "event", "title": e.title,
                    "subtitle": " · ".join(x for x in (bands.get(e.band_id),
                                                        e.starts_at.strftime("%d/%m/%Y %H:%M")
                                                        if e.starts_at else None) if x),
                    "href": f"band.html?id={e.band_id}", "type": e.type})
    return out[:30]
