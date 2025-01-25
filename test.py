import ccxt
import json

"""
update config/supported_markets.json
"""

exchange_names = ['binance', 'bybit', 'okx']
exchange_markets = {}

for exchange_name in exchange_names:
    exchange = getattr(ccxt, exchange_name)()
    markets = exchange.fetch_markets()
    exchange_markets[exchange_name] = [market['symbol'] for market in markets]

with open('config/supported_markets.json', 'w') as f:
    json.dump(exchange_markets, f, indent=4)

print("Supported markets saved to 'supported_markets.json'.")
