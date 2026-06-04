from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


class ValidationError(ValueError):
    """Raised when CLI order input is invalid."""


@dataclass(frozen=True)
class OrderInput:
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None


def validate_order_input(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
) -> OrderInput:
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_order_type = validate_order_type(order_type)
    clean_quantity = validate_positive_decimal(quantity, "quantity")

    clean_price = None
    if clean_order_type == "LIMIT":
        if price is None or not price.strip():
            raise ValidationError("price is required for LIMIT orders.")
        clean_price = validate_positive_decimal(price, "price")
    elif price is not None and price.strip():
        raise ValidationError("price should only be provided for LIMIT orders.")

    return OrderInput(
        symbol=clean_symbol,
        side=clean_side,
        order_type=clean_order_type,
        quantity=clean_quantity,
        price=clean_price,
    )


def validate_symbol(symbol: str) -> str:
    value = (symbol or "").strip().upper()
    if not value:
        raise ValidationError("symbol is required, for example BTCUSDT.")
    if not SYMBOL_PATTERN.match(value):
        raise ValidationError("symbol must be 5-20 uppercase letters/numbers, for example BTCUSDT.")
    return value


def validate_side(side: str) -> str:
    value = (side or "").strip().upper()
    if value not in VALID_SIDES:
        raise ValidationError("side must be BUY or SELL.")
    return value


def validate_order_type(order_type: str) -> str:
    value = (order_type or "").strip().upper()
    if value not in VALID_ORDER_TYPES:
        raise ValidationError("order type must be MARKET or LIMIT.")
    return value


def validate_positive_decimal(raw_value: str, field_name: str) -> Decimal:
    value = (raw_value or "").strip()
    if not value:
        raise ValidationError(f"{field_name} is required.")

    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValidationError(f"{field_name} must be a valid number.") from exc

    if decimal_value <= 0:
        raise ValidationError(f"{field_name} must be greater than 0.")

    return decimal_value
