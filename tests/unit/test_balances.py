"""
Tests del servicio de balances (Fase 11, §C.4.3) — la zona de mayor riesgo.

Función pura: usamos objetos de prueba ligeros (no la BD). Cubre el ejemplo de la guía, el
invariante "todo cuadra a cero", el reparto con céntimos sobrantes, el fondo y las liquidaciones.
"""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.services.balances import FUND_KEY, compute_balances, equal_split_amounts, q

pytestmark = pytest.mark.unit

A, B, C, D = "A", "B", "C", "D"


def _split(user_id=None, share=None, to_fund=False):
    return SimpleNamespace(user_id=user_id, share_amount=Decimal(str(share)), to_fund=to_fund)


def _tx(type, amount, paid_by=None, paid_by_fund=False, splits=()):
    return SimpleNamespace(type=type, amount=Decimal(str(amount)),
                           paid_by=paid_by, paid_by_fund=paid_by_fund, splits=list(splits))


def _settle(from_user, to_user=None, amount=0, to_fund=False):
    return SimpleNamespace(from_user_id=from_user, to_user_id=to_user,
                           amount=Decimal(str(amount)), to_fund=to_fund)


def _sum_zero(balances):
    assert sum(balances.values()) == Decimal("0.00"), balances


def test_reparto_igual_absorbe_centimos():
    shares = equal_split_amounts(100, 3)
    assert shares == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert sum(shares) == Decimal("100.00")  # cuadra exacto


def test_ejemplo_de_la_guia_cuadra_a_cero():
    # Ingreso 400 cobrado por A, repartido 100 a cada uno (A,B,C,D)
    ingreso = _tx("income", 400, paid_by=A, splits=[
        _split(A, 100), _split(B, 100), _split(C, 100), _split(D, 100)])
    # Gasto 60 de gasolina puesto por B, repartido 15 a cada uno
    gasto = _tx("expense", 60, paid_by=B, splits=[
        _split(A, 15), _split(B, 15), _split(C, 15), _split(D, 15)])

    bal = compute_balances([ingreso, gasto], [], [A, B, C, D])
    # A cobró 400 y debe repartir (-400+100) y consumió 15 de gasolina → -315
    assert bal[A] == Decimal("-315.00")
    # B puso 60 de gasolina (+60-15) y tiene derecho a 100 del bolo → +145
    assert bal[B] == Decimal("145.00")
    assert bal[C] == Decimal("85.00")
    assert bal[D] == Decimal("85.00")
    _sum_zero(bal)


def test_solo_gasto_simple():
    # B adelanta 60, reparto 15 a 4 → B le deben 45, cada otro debe 15
    gasto = _tx("expense", 60, paid_by=B, splits=[
        _split(A, 15), _split(B, 15), _split(C, 15), _split(D, 15)])
    bal = compute_balances([gasto], [], [A, B, C, D])
    assert bal[B] == Decimal("45.00")
    assert bal[A] == bal[C] == bal[D] == Decimal("-15.00")
    _sum_zero(bal)


def test_aportacion_al_fondo_y_gasto_del_fondo():
    # Cuota: A aporta 30 al fondo (ingreso cuyo destino es el fondo). Modelado como ingreso
    # pagado por A con la parte asignada al fondo.
    cuota = _tx("income", 30, paid_by=A, splits=[_split(share=30, to_fund=True)])
    # Gasto de 20 pagado POR el fondo, repartido entre A y B (10 cada uno)
    gasto_fondo = _tx("expense", 20, paid_by_fund=True, splits=[_split(A, 10), _split(B, 10)])
    bal = compute_balances([cuota, gasto_fondo], [], [A, B])
    # A: ingreso -30 (lo recibió, lo mete al fondo); gasto: -10 → -40
    assert bal[A] == Decimal("-40.00")
    assert bal[B] == Decimal("-10.00")
    # Fondo: +30 (cuota) +20 (puso el gasto) → +50
    assert bal[FUND_KEY] == Decimal("50.00")
    _sum_zero(bal)


def test_liquidacion_acerca_a_cero():
    # B le deben 45 (del gasto). A le paga a B 15 (su parte).
    gasto = _tx("expense", 60, paid_by=B, splits=[
        _split(A, 15), _split(B, 15), _split(C, 15), _split(D, 15)])
    bal0 = compute_balances([gasto], [], [A, B, C, D])
    assert bal0[A] == Decimal("-15.00") and bal0[B] == Decimal("45.00")

    liq = _settle(A, B, 15)  # A paga a B 15
    bal1 = compute_balances([gasto], [liq], [A, B, C, D])
    assert bal1[A] == Decimal("0.00")     # A saldó su parte
    assert bal1[B] == Decimal("30.00")    # a B aún le deben 30 (C y D)
    _sum_zero(bal1)


def test_reparto_con_centimos_cuadra_a_cero():
    # 100 entre 3, reparto desigual por redondeo (último absorbe)
    shares = equal_split_amounts(100, 3)
    gasto = _tx("expense", 100, paid_by=A,
                splits=[_split(A, shares[0]), _split(B, shares[1]), _split(C, shares[2])])
    bal = compute_balances([gasto], [], [A, B, C])
    _sum_zero(bal)  # pese a los céntimos, cuadra exacto
    assert bal[A] == q(100 - shares[0])  # A puso 100, consume su parte
