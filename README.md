# Binance Futures Testnet Trading Bot

A simple Python 3 CLI assignment project for placing Binance USD-M Futures Testnet
orders. It supports `MARKET` and `LIMIT` orders with `BUY` and `SELL` sides.

The bot is Testnet-only and reads credentials from `.env`. API keys are never
printed to the terminal or intentionally written to logs.

## Project Structure

```text
bot/
  client.py          Binance Futures Testnet client and time sync
  orders.py          Order placement and terminal summary helpers
  validators.py      CLI input validation
  logging_config.py  File logging setup
cli.py               Main CLI application
testing.py           Connection test
requirements.txt     Python dependencies
```

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv envi
envi\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root.

```text
Binance_api_key=your_testnet_api_key
Binance_api_secret_key=your_testnet_api_secret
```

You can also use these environment variable names:

```text
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

4. Test the Binance Futures Testnet connection.

```bash
python testing.py
```

## Run Examples

Place a MARKET buy order:

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Place a LIMIT sell order:

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000
```

## CLI Inputs

- `--symbol`: Futures symbol, for example `BTCUSDT`
- `--side`: `BUY` or `SELL`
- `--type`: `MARKET` or `LIMIT`
- `--quantity`: positive number
- `--price`: positive number, required only for `LIMIT`

Invalid inputs are rejected before the API call with a clear terminal message.

## Logging

Logs are written to:

```text
logs/trading_bot.log
```

The log includes API requests, successful responses, order placement events, and
errors. Sensitive fields such as API keys and signatures are redacted if present.

## Assumptions

- This project is for Binance Futures Testnet only.
- Testnet API keys must be created from Binance Futures Testnet.
- LIMIT orders use `GTC` time-in-force.
- Symbol filters such as minimum quantity, tick size, and account balance are
  enforced by Binance after submission.
- The client synchronizes timestamp offset with Binance Futures server time and
  retries once when Binance reports timestamp drift.
