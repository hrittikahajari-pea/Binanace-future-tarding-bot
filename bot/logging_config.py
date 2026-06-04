from __future__ import annotations

import logging
from pathlib import Path


LOG_FILE = Path("logs") / "trading_bot.log"


def setup_logging() -> None:
    """Configure file logging for the trading bot."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
