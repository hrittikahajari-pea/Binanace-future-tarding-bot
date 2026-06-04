from __future__ import annotations

import argparse
import logging
import sys

from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests import RequestException

from bot.client import BinanceTimeSyncError, create_futures_testnet_client_from_env
from bot.logging_config import setup_logging
from bot.orders import build_order_summary, place_futures_order
from bot.validators import ValidationError, validate_order_input


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


def main() -> int:
    setup_logging()
    args = parse_args()

    try:
        order = validate_order_input(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
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
