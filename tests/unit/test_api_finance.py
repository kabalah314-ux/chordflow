"""
Tests de la API de finanzas (Fase 11): transacciones con reparto, balances, liquidaciones,
permisos (solo admin registra) y aislamiento. El cálculo en sí lo cubre test_balances.py.
"""

import contextlib

import pytest

from src.main import app
from src.services.auth import get_current_user
from src.services.db import SessionLocal
from src.services.models import BandMembership

pytestmark = pytest.mark.unit

ADMIN = "00000000-0000-0000-0000-000000000000"
MEMBER = "22222222-2222-2222-2222-222222222222"
STRANGER = "99999999-9999-9999-9999-999999999999"


@contextlib.contextmanager
def acting_as(user_id):
    app.dependency_overrides[get_current_user] = lambda: user_id
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def _band(client):
    bid = client.post("/bands/", json={"name": "Banda Plata"}).json()["id"]
    db = SessionLocal()
    try:
        db.add(BandMembership(band_id=bid, user_id=MEMBER, role="member", status="active"))
        db.commit()
    finally:
        db.close()
    return bid


def _bal(client, bid):
    return {b["participant"]: float(b["balance"]) for b in client.get(f"/bands/{bid}/balances").json()}


def test_gasto_con_reparto_por_defecto_y_balances(client):
    bid = _band(client)  # 2 miembros activos: ADMIN, MEMBER
    r = client.post(f"/bands/{bid}/transactions", json={
        "type": "expense", "description": "Local", "amount": "100.00", "paid_by": ADMIN})
    assert r.status_code == 201, r.text
    tx = r.json()
    # Reparto por defecto: 50 y 50
    assert sorted(float(s["share_amount"]) for s in tx["splits"]) == [50.0, 50.0]

    bal = _bal(client, bid)
    assert bal[ADMIN] == 50.0      # puso 100, consume 50 → +50
    assert bal[MEMBER] == -50.0
    assert bal["fund"] == 0.0
    assert round(sum(bal.values()), 2) == 0.0  # cuadra a cero


def test_reparto_que_no_suma_da_400(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/transactions", json={
        "type": "expense", "amount": "100.00", "paid_by": ADMIN,
        "splits": [{"user_id": ADMIN, "share_amount": "40.00"},
                   {"user_id": MEMBER, "share_amount": "40.00"}]})  # suma 80 ≠ 100
    assert r.status_code == 400


def test_pagador_no_miembro_da_400(client):
    bid = _band(client)
    r = client.post(f"/bands/{bid}/transactions", json={
        "type": "expense", "amount": "10.00", "paid_by": STRANGER})
    assert r.status_code == 400


def test_ingreso_y_liquidacion_acercan_a_cero(client):
    bid = _band(client)
    # Ingreso 200 cobrado por ADMIN, repartido por defecto (100/100)
    client.post(f"/bands/{bid}/transactions", json={
        "type": "income", "amount": "200.00", "paid_by": ADMIN})
    bal = _bal(client, bid)
    assert bal[ADMIN] == -100.0   # cobró 200, debe repartir → -100
    assert bal[MEMBER] == 100.0

    # ADMIN paga a MEMBER 100 → todo a cero
    r = client.post(f"/bands/{bid}/settlements", json={
        "from_user_id": ADMIN, "to_user_id": MEMBER, "amount": "100.00"})
    assert r.status_code == 201
    bal = _bal(client, bid)
    assert bal[ADMIN] == 0.0 and bal[MEMBER] == 0.0


def test_aportacion_al_fondo(client):
    bid = _band(client)
    # ADMIN aporta 30 al fondo (ingreso con la parte al fondo)
    r = client.post(f"/bands/{bid}/transactions", json={
        "type": "income", "amount": "30.00", "paid_by": ADMIN,
        "splits": [{"to_fund": True, "share_amount": "30.00"}]})
    assert r.status_code == 201
    bal = _bal(client, bid)
    assert bal[ADMIN] == -30.0
    assert bal["fund"] == 30.0
    assert round(sum(bal.values()), 2) == 0.0


def test_solo_admin_registra_miembro_solo_ve(client):
    bid = _band(client)
    tx = client.post(f"/bands/{bid}/transactions", json={
        "type": "expense", "amount": "10.00", "paid_by": ADMIN}).json()
    with acting_as(MEMBER):
        # Ver: sí
        assert client.get(f"/bands/{bid}/transactions").status_code == 200
        assert client.get(f"/bands/{bid}/balances").status_code == 200
        # Registrar / borrar / liquidar: no (solo admin)
        assert client.post(f"/bands/{bid}/transactions", json={
            "type": "expense", "amount": "5.00", "paid_by": MEMBER}).status_code == 403
        assert client.delete(f"/bands/{bid}/transactions/{tx['id']}").status_code == 403
        assert client.post(f"/bands/{bid}/settlements", json={
            "from_user_id": MEMBER, "to_user_id": ADMIN, "amount": "1.00"}).status_code == 403


def test_borrar_transaccion_es_soft_y_recalcula(client):
    bid = _band(client)
    tx = client.post(f"/bands/{bid}/transactions", json={
        "type": "expense", "amount": "100.00", "paid_by": ADMIN}).json()
    assert client.delete(f"/bands/{bid}/transactions/{tx['id']}").status_code == 204
    # Tras borrar, balances vuelven a cero y no aparece en la lista
    bal = _bal(client, bid)
    assert all(v == 0.0 for v in bal.values())
    assert client.get(f"/bands/{bid}/transactions").json() == []


def test_aislamiento_finanzas(client):
    bid = _band(client)
    tx = client.post(f"/bands/{bid}/transactions", json={
        "type": "expense", "amount": "10.00", "paid_by": ADMIN}).json()
    with acting_as(STRANGER):
        assert client.get(f"/bands/{bid}/transactions").status_code == 404
        assert client.get(f"/bands/{bid}/balances").status_code == 404
        assert client.post(f"/bands/{bid}/transactions", json={
            "type": "expense", "amount": "1.00", "paid_by": STRANGER}).status_code == 404
        assert client.delete(f"/bands/{bid}/transactions/{tx['id']}").status_code == 404
        assert client.get(f"/bands/{bid}/settlements").status_code == 404
