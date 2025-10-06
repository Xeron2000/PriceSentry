import argparse
import json
import logging

import ccxt
import yaml
from pathlib import Path
import sys

# Ensure src directory is on the import path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
for candidate in (SRC_DIR, ROOT_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from utils.setup_logging import setup_logging


def load_config():
    """Loads the YAML configuration file."""
    try:
        with open("config/config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error("config/config.yaml not found.")
        return None


def fetch_markets_for_exchange(exchange_name):
    """Fetches all market symbols for a given exchange."""
    try:
        exchange = getattr(ccxt, exchange_name)({"options": {"defaultType": "swap"}})
        markets = exchange.fetch_markets()
        return [market["symbol"] for market in markets]
    except (ccxt.ExchangeError, ccxt.NetworkError) as e:
        logging.error(f"Error fetching markets for {exchange_name}: {e}")
        return None


def update_supported_markets(exchange_names):
    """Fetches markets for a list of exchanges and saves them to a JSON file."""
    exchange_markets = {}
    for exchange_name in exchange_names:
        logging.info(f"Fetching markets for {exchange_name}...")
        markets = fetch_markets_for_exchange(exchange_name)
        if markets:
            exchange_markets[exchange_name] = markets
            logging.info(f"Found {len(markets)} markets for {exchange_name}.")

    if not exchange_markets:
        logging.warning(
            "No market data was fetched. The output file will not be updated."
        )
        return

    output_file = "config/supported_markets.json"
    with open(output_file, "w") as f:
        json.dump(exchange_markets, f, indent=4)

    logging.info(f"Supported markets saved to '{output_file}'.")


def main():
    """Main function to run the script."""
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Update supported markets for exchanges."
    )
    parser.add_argument(
        "--exchanges",
        nargs="+",
        help=(
            "A list of exchange names to update. If not provided, all exchanges from "
            "config.yaml will be used."
        ),
    )
    args = parser.parse_args()

    if args.exchanges:
        exchange_names = args.exchanges
    else:
        config = load_config()
        if not config:
            return
        exchange_names = config.get("exchanges", [])
        if not exchange_names:
            logging.warning(
                "No exchanges found in config.yaml. "
                "Please add them under the 'exchanges' key."
            )
            return

    update_supported_markets(exchange_names)


if __name__ == "__main__":
    main()
