from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from bot.validators import OrderInput


logger = logging.getLogger(__name__)


def place_futures_order(client: Any, order: OrderInput) -> dict[str, Any]:
    """Place a MARKET or LIMIT order on Binance Futures Testnet."""
    params: dict[str, Any] = {
        "symbol": order.symbol,
        "side": order.side,
        "type": order.order_type,
        "quantity": decimal_to_string(order.quantity),
    }

    if order.order_type == "LIMIT":
        params["timeInForce"] = "GTC"
        params["price"] = decimal_to_string(order.price)

    logger.info("Placing futures order: %s", params)
    response = client.futures_create_order(**params)
    logger.info("Order placed successfully: %s", response)
    return response


def decimal_to_string(value: Decimal | None) -> str:
    if value is None:
        raise ValueError("Decimal value cannot be None.")
    return format(value.normalize(), "f")


def build_order_summary(order: OrderInput, response: dict[str, Any]) -> str:
    avg_price = response.get("avgPrice") or response.get("averagePrice") or "N/A"
    lines = [
        "Order Submitted Successfully",
        "",
        "Order Summary",
        f"Symbol       : {order.symbol}",
        f"Side         : {order.side}",
        f"Order Type   : {order.order_type}",
        f"Quantity     : {decimal_to_string(order.quantity)}",
    ]

    if order.price is not None:
        lines.append(f"Price        : {decimal_to_string(order.price)}")

    lines.extend(
        [
            "",
            f"Order ID     : {response.get('orderId', 'N/A')}",
            f"Status       : {response.get('status', 'N/A')}",
            f"Executed Qty : {response.get('executedQty', 'N/A')}",
            f"Avg Price    : {avg_price}",
        ]
    )
    return "\n".join(lines)
