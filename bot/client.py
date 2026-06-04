from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
from requests import RequestException


T = TypeVar("T")

TIMESTAMP_DRIFT_CODE = -1021
SENSITIVE_KEYS = {"apiKey", "signature", "secret", "api_secret", "api_key"}

logger = logging.getLogger(__name__)


class BinanceTimeSyncError(RuntimeError):
    """Raised when Binance server time cannot be read from the response."""


class SafeFuturesClient(Client):
    """Binance client with robust Futures Testnet timestamp synchronization."""

    def sync_futures_time(self) -> int:
        """Synchronize timestamp_offset from the Futures server time endpoint."""
        server_time = extract_server_time_ms(self.futures_time())
        local_time = int(time.time() * 1000)
        self.timestamp_offset = server_time - local_time
        return self.timestamp_offset

    def call_with_timestamp_retry(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run a Binance call and retry once after time sync on drift errors."""
        try:
            return func(*args, **kwargs)
        except BinanceAPIException as exc:
            if not is_timestamp_drift_error(exc):
                raise
            self.sync_futures_time()
            return func(*args, **kwargs)

    def _request(
        self,
        method: str,
        uri: str,
        signed: bool,
        force_params: bool = False,
        **kwargs: Any,
    ) -> Any:
        logger.info(
            "API request: method=%s uri=%s signed=%s params=%s",
            method.upper(),
            uri,
            signed,
            sanitize_for_log(kwargs.get("data", {})),
        )
        try:
            response = super()._request(method, uri, signed, force_params, **kwargs)
        except BinanceAPIException as exc:
            if not signed or not is_timestamp_drift_error(exc):
                logger.exception("Binance API error: code=%s message=%s", exc.code, exc.message)
                raise
            logger.warning("Timestamp drift detected. Syncing Binance Futures server time and retrying once.")
            self.sync_futures_time()
            try:
                response = super()._request(method, uri, signed, force_params, **kwargs)
            except BinanceAPIException as retry_exc:
                logger.exception(
                    "Binance API error after timestamp sync retry: code=%s message=%s",
                    retry_exc.code,
                    retry_exc.message,
                )
                raise
            except RequestException:
                logger.exception("Network error while retrying Binance API request after timestamp sync.")
                raise
        except RequestException:
            logger.exception("Network error while calling Binance API.")
            raise
        except Exception:
            logger.exception("Unexpected error while calling Binance API.")
            raise

        logger.info("API response: %s", sanitize_for_log(response))
        return response


def create_futures_testnet_client(api_key: str, api_secret: str) -> SafeFuturesClient:
    """Create a Binance Futures Testnet client and synchronize its timestamp."""
    client = SafeFuturesClient(api_key, api_secret, testnet=True)
    client.sync_futures_time()
    return client


def create_futures_testnet_client_from_env() -> SafeFuturesClient:
    """Load Binance credentials from .env and create a Futures Testnet client."""
    load_dotenv()
    api_key = os.getenv("Binance_api_key") or os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("Binance_api_secret_key") or os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise RuntimeError(
            "Binance API credentials are missing. Set Binance_api_key and "
            "Binance_api_secret_key in .env."
        )

    return create_futures_testnet_client(api_key, api_secret)


def extract_server_time_ms(response: Any) -> int:
    """Extract a millisecond server timestamp from common Binance response shapes."""
    value = _find_time_value(response)
    if value is None:
        raise BinanceTimeSyncError(
            f"Binance server time response did not include a timestamp: {response!r}"
        )

    try:
        timestamp = int(value)
    except (TypeError, ValueError) as exc:
        raise BinanceTimeSyncError(
            f"Binance server time value is not numeric: {value!r}"
        ) from exc

    return timestamp * 1000 if timestamp < 10_000_000_000 else timestamp


def is_timestamp_drift_error(exc: BinanceAPIException) -> bool:
    message = (getattr(exc, "message", "") or "").lower()
    return getattr(exc, "code", None) == TIMESTAMP_DRIFT_CODE or (
        "timestamp" in message and ("recvwindow" in message or "ahead" in message)
    )


def sanitize_for_log(value: Any) -> Any:
    """Return a copy of value with sensitive fields redacted for logging."""
    if isinstance(value, Mapping):
        sanitized = {}
        for key, item in value.items():
            if str(key) in SENSITIVE_KEYS:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = sanitize_for_log(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_for_log(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_for_log(item) for item in value)
    return value


def _find_time_value(response: Any) -> Any | None:
    if isinstance(response, Mapping):
        for key in ("serverTime", "server_time", "time", "timestamp"):
            if key in response:
                return response[key]
        for key in ("data", "result"):
            value = _find_time_value(response.get(key))
            if value is not None:
                return value
    elif isinstance(response, (int, float, str)):
        return response
    return None
