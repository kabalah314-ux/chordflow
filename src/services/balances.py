"""
Servicio ÚNICO de balances (Fase 11, §C.4.3) — la zona de mayor riesgo de bug del giro.

Una sola función calcula el saldo neto de cada participante integrando `Transaction` +
`TransactionSplit` + flags de **fondo** + `Settlement`. Fórmula (modelo Splitwise):

- **Gasto** (`expense`): el pagador adelantó el dinero → `+amount`; cada parte del reparto consume
  su trozo → `-share`.
- **Ingreso** (`income`): el pagador recibió el dinero y debe repartirlo → `-amount`; cada parte
  tiene derecho a su trozo → `+share`.
- **Liquidación** (`Settlement`): "A paga a B" → `+amount` a A (puso dinero), `-amount` a B (lo
  recibió). Acerca los saldos a cero.
- El **fondo** común es un participante virtual (`FUND_KEY`): `paid_by_fund` / `to_fund`.

Invariante: como Σ(partes) = amount en cada movimiento y cada liquidación es +/-, **la suma de
todos los saldos es siempre 0**. Saldo **positivo** = le deben; **negativo** = debe.

Todo en `Decimal` cuantizado a céntimos. Sin dependencias de la BD: recibe objetos con los
atributos esperados (ORM o de prueba), por eso es trivial de testear de forma aislada.
"""

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")
FUND_KEY = "fund"  # clave del participante virtual "fondo común"


def q(value) -> Decimal:
    """Cuantiza a céntimos (2 decimales), redondeo bancario hacia arriba en el .5."""
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


def equal_split_amounts(amount, n: int) -> list[Decimal]:
    """Reparte `amount` en `n` partes iguales (a céntimos); el **último** absorbe los céntimos
    sobrantes para que Σ partes == amount EXACTO (§C.4.3)."""
    if n <= 0:
        return []
    total = q(amount)
    base = (total / n).quantize(CENTS, rounding=ROUND_DOWN)
    shares = [base for _ in range(n)]
    shares[-1] = q(shares[-1] + (total - base * n))
    return shares


def compute_balances(transactions, settlements, member_ids) -> dict:
    """Saldo neto por participante. Devuelve `{user_id: Decimal, ..., FUND_KEY: Decimal}`.

    `transactions`: objetos con `.type` ('expense'|'income'), `.amount`, `.paid_by`,
      `.paid_by_fund` y `.splits` (cada uno con `.user_id`, `.share_amount`, `.to_fund`).
    `settlements`: objetos con `.from_user_id`, `.to_user_id`, `.to_fund`, `.amount`.
    `member_ids`: ids a inicializar a 0 (para que todos aparezcan aunque tengan saldo 0)."""
    bal: dict[str, Decimal] = {uid: Decimal("0.00") for uid in member_ids}
    bal.setdefault(FUND_KEY, Decimal("0.00"))

    def add(key, amount):
        bal[key] = bal.get(key, Decimal("0.00")) + amount

    for t in transactions:
        amount = q(t.amount)
        payer = FUND_KEY if t.paid_by_fund else t.paid_by
        # expense: pagador +amount, partes -share ; income: pagador -amount, partes +share
        sign = Decimal(1) if t.type == "expense" else Decimal(-1)
        add(payer, sign * amount)
        for s in t.splits:
            key = FUND_KEY if s.to_fund else s.user_id
            add(key, -sign * q(s.share_amount))

    for st in settlements:
        amount = q(st.amount)
        add(st.from_user_id, amount)
        add(FUND_KEY if st.to_fund else st.to_user_id, -amount)

    return {k: v.quantize(CENTS) for k, v in bal.items()}
