from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MONEY_PRECISION = 18
MONEY_SCALE = 2
MONEY_QUANTUM = Decimal("0.01")
ZERO_MONEY = Decimal("0.00")


def to_money(value: object) -> Decimal:
    """Convert user/database input to a two-decimal fixed-point monetary value."""
    if isinstance(value, Decimal):
        decimal_value = value
    else:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("Invalid monetary value") from exc

    if not decimal_value.is_finite():
        raise ValueError("Monetary value must be finite")
    return decimal_value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def to_weight(value: object | None, *, default: str = "50") -> Decimal:
    raw = default if value is None else str(value)
    try:
        decimal_value = Decimal(raw)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid numeric weight") from exc
    if not decimal_value.is_finite():
        raise ValueError("Numeric weight must be finite")
    return max(decimal_value, Decimal("0"))
