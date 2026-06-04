from bot.client import create_futures_testnet_client_from_env
from bot.logging_config import setup_logging


setup_logging()
client = create_futures_testnet_client_from_env()

account = client.futures_account()

print("Connected Successfully")
print("Wallet Balance:", account["totalWalletBalance"])
