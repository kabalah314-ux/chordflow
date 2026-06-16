"""
seed_demo.py — Siembra datos de ejemplo en una BD de DEMO para revisar el giro a ojo.

Uso:
    DATABASE_URL=sqlite:///./demo_bandflow.db python harness/seed_demo.py

Crea, para el usuario de prueba (modo test), una banda con miembros, repertorio, un setlist,
un evento, un par de movimientos de finanzas y mensajes de chat (uno fijado). No toca producción.
Es idempotente-ish: si la banda demo ya existe, no duplica.
"""

import os
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("CHORDFLOW_TEST_MODE", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:///./demo_bandflow.db")

from src.services.db import Base, SessionLocal, engine  # noqa: E402
from src.services.models import (  # noqa: E402
    Band,
    BandMembership,
    ChordMarker,
    Event,
    EventAttendance,
    Line,
    Message,
    MusicianProfile,
    Section,
    Setlist,
    SetlistItem,
    Song,
    Transaction,
    TransactionSplit,
    _utcnow,
)

TEST_USER = "00000000-0000-0000-0000-000000000000"
ANA = "11111111-1111-1111-1111-111111111111"
LUIS = "22222222-2222-2222-2222-222222222222"


def _song(db, band_id, owner, title, artist):
    s = Song(title=title, artist=artist, bpm=120, owner_id=owner, band_id=band_id)
    sec = Section(name="Estrofa", order=1)
    line = Line(order=1, type="lyric", content="La la la la la", beat_start=0, beat_duration=4)
    line.chords.append(ChordMarker(chord_name="G", char_position=0, beat_offset=0))
    line.chords.append(ChordMarker(chord_name="C", char_position=6, beat_offset=2))
    sec.lines.append(line)
    s.sections.append(sec)
    db.add(s)
    db.flush()
    return s


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Band).filter(Band.name == "Los Demo Riff").first():
            print("La banda demo ya existe; no se siembra de nuevo.")
            return

        # Perfiles
        for uid, name, inst in [(TEST_USER, "Oscar (tú)", ["bajo", "voz"]),
                                (ANA, "Ana", ["guitarra"]), (LUIS, "Luis", ["batería"])]:
            if not db.get(MusicianProfile, uid):
                db.add(MusicianProfile(id=uid, display_name=name, instruments=inst))

        # Banda + miembros
        band = Band(name="Los Demo Riff", description="Banda de ejemplo de BandFlow",
                    created_by=TEST_USER, currency="EUR")
        db.add(band)
        db.flush()
        db.add_all([
            BandMembership(band_id=band.id, user_id=TEST_USER, role="admin", status="active", instrument="bajo"),
            BandMembership(band_id=band.id, user_id=ANA, role="member", status="active", instrument="guitarra"),
            BandMembership(band_id=band.id, user_id=LUIS, role="member", status="active", instrument="batería"),
        ])

        # Repertorio
        s1 = _song(db, band.id, TEST_USER, "Wonderwall (demo)", "Oasis")
        s2 = _song(db, band.id, ANA, "Seven Nation Army (demo)", "The White Stripes")
        s3 = _song(db, band.id, TEST_USER, "Zombie (demo)", "The Cranberries")

        # Setlist
        sl = Setlist(name="Bolo sábado", owner_id=TEST_USER, band_id=band.id)
        sl.items.append(SetlistItem(song_id=s1.id, position=0))
        sl.items.append(SetlistItem(song_id=s3.id, position=1, note="Hablar al público antes"))
        sl.items.append(SetlistItem(song_id=s2.id, position=2))
        db.add(sl)
        db.flush()

        # Agenda: un ensayo (próximo) y un concierto con setlist
        ensayo = Event(band_id=band.id, type="rehearsal", title="Ensayo general",
                       starts_at=_utcnow() + timedelta(days=2), location="Local de ensayo",
                       status="confirmed", created_by=TEST_USER)
        bolo = Event(band_id=band.id, type="concert", title="Sala Caracol",
                     starts_at=_utcnow() + timedelta(days=9), location="Madrid",
                     status="confirmed", setlist_id=sl.id, created_by=TEST_USER)
        db.add_all([ensayo, bolo])
        db.flush()
        db.add_all([
            EventAttendance(event_id=ensayo.id, user_id=TEST_USER, status="yes"),
            EventAttendance(event_id=ensayo.id, user_id=ANA, status="yes"),
            EventAttendance(event_id=ensayo.id, user_id=LUIS, status="maybe"),
        ])

        # Finanzas: gasto de local (60 €, lo puso Oscar) repartido 20/20/20
        gasto = Transaction(band_id=band.id, type="expense", description="Local de ensayo",
                            amount=Decimal("60.00"), paid_by=TEST_USER, category="ensayo",
                            created_by=TEST_USER)
        for uid in (TEST_USER, ANA, LUIS):
            gasto.splits.append(TransactionSplit(user_id=uid, share_amount=Decimal("20.00")))
        # Ingreso: caché del bolo 300 € cobrado por Oscar, repartido 100/100/100
        cache = Transaction(band_id=band.id, type="income", description="Caché Sala Caracol",
                            amount=Decimal("300.00"), paid_by=TEST_USER, category="bolo",
                            event_id=bolo.id, created_by=TEST_USER)
        for uid in (TEST_USER, ANA, LUIS):
            cache.splits.append(TransactionSplit(user_id=uid, share_amount=Decimal("100.00")))
        db.add_all([gasto, cache])

        # Chat: una nota fijada + un par de mensajes
        db.add_all([
            Message(band_id=band.id, author_id=TEST_USER, body="📌 Recordad traer cables XLR al bolo.",
                    is_pinned=True),
            Message(band_id=band.id, author_id=ANA, body="¿Ensayamos el viernes en vez del jueves?"),
            Message(band_id=band.id, author_id=LUIS, body="A mí me viene mejor el viernes 👍"),
        ])

        db.commit()
        print(f"Sembrado OK. Banda demo '{band.id}' con repertorio, setlist, agenda, finanzas y chat.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
