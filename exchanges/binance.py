import ccxt
from datetime import datetime, timedelta


class BinanceExchange:
    def __init__(self):
        self.exchange_name = "Binance" 
        self.exchange = ccxt.binance({
            'rateLimit': 1200,
            'enableRateLimit': True,
        })
    
    def getPriceMinutesAgo(self, symbols, minutes):
        prices = {}
        try:
            since = int((datetime.now() - timedelta(minutes=minutes)).timestamp() * 1000)
            for symbol in symbols:
                trades = self.exchange.fetch_trades(symbol, since=since, limit=1)
                if trades:
                    prices[symbol] = float(trades[-1]['price'])
                else:
                    print(f"No trades for {symbol} in the last {minutes} minutes.")
        except Exception as e:
            print(f"Failed to fetch price {minutes} minutes ago: {e}")
        return prices
    
    def getCurrentPrices(self, symbols):
        try:
            tickers = self.exchange.fetch_tickers()
            return {
                symbol: float(tickers[symbol]['last'])
                for symbol in symbols
                if symbol in tickers
            }
        except Exception as e:
            print(f"Failed to fetch current prices: {e}")
            return {}
