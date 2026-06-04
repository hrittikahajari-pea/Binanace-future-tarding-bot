from __future__ import annotations

import argparse
import logging
import sys

from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests import RequestException

from bot.client import BinanceTimeSyncError, create_futures_testnet_client_from_env
from bot.logging_config import setup_logging
from bot.orders import build_order_summary, decimal_to_string, place_futures_order
from bot.validators import OrderInput, ValidationError, validate_order_input


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Place Binance Futures Testnet MARKET or LIMIT orders."
    )
    parser.add_argument("--symbol", required=True, help="Futures symbol, for example BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument("--type", required=True, dest="order_type", help="MARKET or LIMIT")
    parser.add_argument("--quantity", required=True, help="Order quantity, for example 0.001")
    parser.add_argument("--price", help="Limit price. Required only for LIMIT orders.")
    return parser.parse_args()


def get_order_from_args(args: argparse.Namespace) -> OrderInput:
    return validate_order_input(
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
    )


def get_order_interactively() -> tuple[OrderInput, bool]:
    print("Binance Futures Testnet Trading Bot")
    print("Interactive Order Entry")
    print()

    symbol = prompt_required("Symbol (example BTCUSDT): ")
    side = prompt_choice("Side (BUY/SELL): ", {"BUY", "SELL"})
    order_type = prompt_choice("Order type (MARKET/LIMIT): ", {"MARKET", "LIMIT"})
    quantity = prompt_required("Quantity: ")
    price = None

    if order_type == "LIMIT":
        price = prompt_required("Price: ")

    order = validate_order_input(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )

    print()
    print(build_order_request_summary(order))
    print()

    if not confirm("Submit order? (y/n): "):
        logger.info("Interactive order cancelled before API call.")
        print("Order cancelled. No API call was made.")
        return order, False

    return order, True


def prompt_required(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field is required.")


def prompt_choice(prompt: str, choices: set[str]) -> str:
    while True:
        value = input(prompt).strip().upper()
        if value in choices:
            return value
        print(f"Please enter one of: {', '.join(sorted(choices))}.")


def confirm(prompt: str) -> bool:
    while True:
        value = input(prompt).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please enter y or n.")


def build_order_request_summary(order: OrderInput) -> str:
    lines = [
        "Order Request Summary",
        f"Symbol     : {order.symbol}",
        f"Side       : {order.side}",
        f"Order Type : {order.order_type}",
        f"Quantity   : {decimal_to_string(order.quantity)}",
    ]

    if order.price is not None:
        lines.append(f"Price      : {decimal_to_string(order.price)}")

    return "\n".join(lines)


def main() -> int:
    setup_logging()

    try:
        if len(sys.argv) == 1:
            order, should_submit = get_order_interactively()
            if not should_submit:
                return 0
        else:
            order = get_order_from_args(parse_args())

        client = create_futures_testnet_client_from_env()
        response = place_futures_order(client, order)
    except ValidationError as exc:
        logger.error("Invalid input: %s", exc)
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 1
    except BinanceAPIException as exc:
        logger.exception("Binance API error: code=%s message=%s", exc.code, exc.message)
        print(f"Binance API error: {exc.message} (code: {exc.code})", file=sys.stderr)
        return 1
    except BinanceRequestException as exc:
        logger.exception("Binance request error: %s", exc.message)
        print(f"Binance request error: {exc.message}", file=sys.stderr)
        return 1
    except RequestException as exc:
        logger.exception("Network error: %s", exc)
        print("Network error while connecting to Binance. Check your internet connection.", file=sys.stderr)
        return 1
    except (RuntimeError, BinanceTimeSyncError) as exc:
        logger.exception("Configuration or time sync error: %s", exc)
        print(str(exc), file=sys.stderr)
        return 1

    print(build_order_summary(order, response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
