"""
Finanzas de la banda — transacciones, reparto, balances y liquidaciones (Fase 11, Áreas 4/6).

`POST   /bands/{id}/transactions`   → registrar gasto/ingreso con reparto (**solo admin**).
`GET    /bands/{id}/transactions`   → listar movimientos (miembros).
`GET    /bands/{id}/transactions/{tid}` → detalle con su reparto (miembros).
`DELETE /bands/{id}/transactions/{tid}` → soft delete (**solo admin**; financiero nunca duro).
`GET    /bands/{id}/balances`       → saldo neto por miembro + fondo (miembros).
`POST   /bands/{id}/settlements`    → registrar una liquidación (**solo admin**).
`GET    /bands/{id}/settlements`    → listar liquidaciones (miembros).
`DELETE /bands/{id}/settlements/{sid}` → soft delete (**solo admin**).

Registrar/editar finanzas = solo admin (matriz §C.2). Ver = cualquier miembro. El cálculo de saldos
delega en el servicio único `services/balances.py`. Aislamiento por `require_band_*` + `band_id`.
"""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.balances import FUND_KEY, compute_balances, equal_split_amounts, q
from ..services.band_auth import require_band_admin, require_band_member
from ..services.db import get_db
from ..services.models import (
    BandMembership,
    Event,
    MusicianProfile,
    Settlement,
    Transaction,
    TransactionSplit,
    _utcnow,
)
from ..services.schemas import (
    BalanceOut,
    SettlementCreate,
    SettlementResponse,
    SplitOut,
    TransactionCreate,
    TransactionResponse,
    TransactionSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bands/{band_id}", tags=["finance"])


def _active_member_ids(db: Session, band_id: str) -> List[str]:
    rows = (db.query(BandMembership.user_id)
            .filter(BandMembership.band_id == band_id, BandMembership.status == "active").all())
    return [r[0] for r in rows]


def _display_names(db: Session, user_ids) -> Dict[str, str]:
    if not user_ids:
        return {}
    rows = (db.query(MusicianProfile.id, MusicianProfile.display_name)
            .filter(MusicianProfile.id.in_(list(user_ids))).all())
    return {uid: name for uid, name in rows if name}


def _split_out_list(db: Session, tx: Transaction) -> List[SplitOut]:
    names = _display_names(db, [s.user_id for s in tx.splits if s.user_id])
    return [SplitOut(user_id=s.user_id, to_fund=s.to_fund, share_amount=s.share_amount,
                     display_name=names.get(s.user_id)) for s in tx.splits]


def _tx_response(db: Session, tx: Transaction) -> TransactionResponse:
    resp = TransactionResponse.model_validate(tx)
    resp.splits = _split_out_list(db, tx)
    return resp


# ── Transacciones ─────────────────────────────────────────────────────────────

@router.post("/transactions", response_model=TransactionResponse,
             status_code=status.HTTP_201_CREATED)
def create_transaction(
    band_id: str,
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Registra un movimiento con su reparto (solo admin). Si no se envían `splits`, se reparte a
    partes iguales entre los miembros activos. Valida pagador, miembros del reparto y Σ partes."""
    members = set(_active_member_ids(db, band_id))
    amount = q(payload.amount)

    # Pagador: el fondo o un miembro activo.
    if not payload.paid_by_fund:
        if not payload.paid_by:
            raise HTTPException(status_code=400, detail="Falta quién pagó (paid_by o paid_by_fund)")
        if payload.paid_by not in members:
            raise HTTPException(status_code=400, detail="El pagador no es miembro activo de la banda")

    # Evento opcional: debe ser de la banda.
    if payload.event_id is not None:
        ok = (db.query(Event.id)
              .filter(Event.id == payload.event_id, Event.band_id == band_id,
                      Event.deleted_at.is_(None)).first())
        if not ok:
            raise HTTPException(status_code=400, detail="El evento no es de esta banda")

    # Reparto: el enviado (validado) o a partes iguales entre miembros activos.
    if payload.splits:
        splits = []
        suma = q(0)
        for s in payload.splits:
            if not s.to_fund:
                if not s.user_id or s.user_id not in members:
                    raise HTTPException(status_code=400,
                                        detail="Una parte del reparto no es de un miembro activo")
            splits.append((s.user_id, s.to_fund, q(s.share_amount)))
            suma += q(s.share_amount)
        if suma != amount:
            raise HTTPException(status_code=400,
                                detail=f"Las partes ({suma}) no suman el total ({amount})")
    else:
        if not members:
            raise HTTPException(status_code=400, detail="La banda no tiene miembros activos")
        ordered = sorted(members)
        shares = equal_split_amounts(amount, len(ordered))
        splits = [(uid, False, sh) for uid, sh in zip(ordered, shares)]

    tx = Transaction(
        band_id=band_id, type=payload.type, description=payload.description, amount=amount,
        date=payload.date or _utcnow(), category=payload.category,
        paid_by=None if payload.paid_by_fund else payload.paid_by,
        paid_by_fund=payload.paid_by_fund, event_id=payload.event_id,
        created_by=membership.user_id,
    )
    for user_id, to_fund, share in splits:
        tx.splits.append(TransactionSplit(user_id=None if to_fund else user_id,
                                          to_fund=to_fund, share_amount=share))
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return _tx_response(db, tx)


@router.get("/transactions", response_model=List[TransactionSummary])
def list_transactions(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    return (db.query(Transaction)
            .filter(Transaction.band_id == band_id, Transaction.deleted_at.is_(None))
            .order_by(Transaction.date.desc()).all())


@router.get("/transactions/{tx_id}", response_model=TransactionResponse)
def get_transaction(
    band_id: str,
    tx_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    tx = (db.query(Transaction)
          .filter(Transaction.id == tx_id, Transaction.band_id == band_id,
                  Transaction.deleted_at.is_(None)).first())
    if tx is None:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return _tx_response(db, tx)


@router.delete("/transactions/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    band_id: str,
    tx_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    tx = (db.query(Transaction)
          .filter(Transaction.id == tx_id, Transaction.band_id == band_id,
                  Transaction.deleted_at.is_(None)).first())
    if tx is None:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    tx.deleted_at = _utcnow()  # financiero: soft delete, nunca duro
    db.commit()


# ── Balances ──────────────────────────────────────────────────────────────────

@router.get("/balances", response_model=List[BalanceOut])
def get_balances(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    """Saldo neto por miembro + fondo (servicio único de balances)."""
    members = _active_member_ids(db, band_id)
    txs = (db.query(Transaction)
           .filter(Transaction.band_id == band_id, Transaction.deleted_at.is_(None)).all())
    settles = (db.query(Settlement)
               .filter(Settlement.band_id == band_id, Settlement.deleted_at.is_(None)).all())
    balances = compute_balances(txs, settles, members)
    names = _display_names(db, [k for k in balances if k != FUND_KEY])
    out = []
    for participant, value in balances.items():
        is_fund = participant == FUND_KEY
        out.append(BalanceOut(
            participant=participant, is_fund=is_fund,
            display_name="Fondo común" if is_fund else names.get(participant),
            balance=value,
        ))
    # Fondo al final; miembros por nombre/orden estable.
    out.sort(key=lambda b: (b.is_fund, (b.display_name or b.participant)))
    return out


# ── Liquidaciones ─────────────────────────────────────────────────────────────

@router.post("/settlements", response_model=SettlementResponse,
             status_code=status.HTTP_201_CREATED)
def create_settlement(
    band_id: str,
    payload: SettlementCreate,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    """Registra una liquidación ("A paga a B"/al fondo). Solo admin."""
    members = set(_active_member_ids(db, band_id))
    if payload.from_user_id not in members:
        raise HTTPException(status_code=400, detail="El pagador no es miembro activo")
    if not payload.to_fund:
        if not payload.to_user_id or payload.to_user_id not in members:
            raise HTTPException(status_code=400, detail="El receptor no es miembro activo")
        if payload.to_user_id == payload.from_user_id:
            raise HTTPException(status_code=400, detail="El pagador y el receptor no pueden coincidir")
    st = Settlement(
        band_id=band_id, from_user_id=payload.from_user_id,
        to_user_id=None if payload.to_fund else payload.to_user_id,
        to_fund=payload.to_fund, amount=q(payload.amount),
        date=payload.date or _utcnow(), note=payload.note, created_by=membership.user_id,
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


@router.get("/settlements", response_model=List[SettlementResponse])
def list_settlements(
    band_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_member),
):
    return (db.query(Settlement)
            .filter(Settlement.band_id == band_id, Settlement.deleted_at.is_(None))
            .order_by(Settlement.date.desc()).all())


@router.delete("/settlements/{settlement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_settlement(
    band_id: str,
    settlement_id: str,
    db: Session = Depends(get_db),
    membership: BandMembership = Depends(require_band_admin),
):
    st = (db.query(Settlement)
          .filter(Settlement.id == settlement_id, Settlement.band_id == band_id,
                  Settlement.deleted_at.is_(None)).first())
    if st is None:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    st.deleted_at = _utcnow()
    db.commit()
