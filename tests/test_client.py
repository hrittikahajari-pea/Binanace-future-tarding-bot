import unittest

from binance.exceptions import BinanceAPIException

from bot.client import (
    BinanceTimeSyncError,
    SafeFuturesClient,
    extract_server_time_ms,
    is_timestamp_drift_error,
)


class DummyBinanceException(BinanceAPIException):
    def __init__(self, code=None, message=""):
        self.code = code
        self.message = message
        self.status_code = 400
        self.response = None
        self.request = None


class DummySafeFuturesClient(SafeFuturesClient):
    def __init__(self):
        self.timestamp_offset = 0
        self.sync_count = 0
        self.session = None

    def sync_futures_time(self):
        self.sync_count += 1
        self.timestamp_offset = 123
        return self.timestamp_offset


class ClientTimeSyncTests(unittest.TestCase):
    def test_extracts_common_server_time_shapes(self):
        self.assertEqual(extract_server_time_ms({"serverTime": 1710000000123}), 1710000000123)
        self.assertEqual(extract_server_time_ms({"data": {"serverTime": "1710000000123"}}), 1710000000123)
        self.assertEqual(extract_server_time_ms({"result": {"time": 1710000000}}), 1710000000000)
        self.assertEqual(extract_server_time_ms("1710000000123"), 1710000000123)

    def test_raises_clear_error_when_time_is_missing(self):
        with self.assertRaises(BinanceTimeSyncError):
            extract_server_time_ms({"status": 0, "msg": "normal"})

    def test_timestamp_drift_detection(self):
        self.assertTrue(is_timestamp_drift_error(DummyBinanceException(-1021, "anything")))
        self.assertTrue(
            is_timestamp_drift_error(
                DummyBinanceException(message="Timestamp for this request is outside of the recvWindow.")
            )
        )
        self.assertFalse(is_timestamp_drift_error(DummyBinanceException(-2015, "Invalid API-key")))

    def test_call_retries_once_after_timestamp_sync(self):
        client = DummySafeFuturesClient()
        calls = {"count": 0}

        def flaky_call():
            calls["count"] += 1
            if calls["count"] == 1:
                raise DummyBinanceException(-1021, "timestamp drift")
            return "ok"

        self.assertEqual(client.call_with_timestamp_retry(flaky_call), "ok")
        self.assertEqual(calls["count"], 2)
        self.assertEqual(client.sync_count, 1)


if __name__ == "__main__":
    unittest.main()
