import requests

class BinanceExchange:
    def __init__(self):
        self.baseUrl = "https://api.binance.com/api/v3"
    
    def getTopGainersAndLosers(self, start, end):
        url = f"{self.baseUrl}/ticker/24hr"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            usdtPairs = [coin for coin in data if coin["symbol"].endswith("USDT")]

            def safeFloat(val):
                try:
                    return float(val)
                except ValueError:
                    return 0.0

            topGainers = sorted(
                usdtPairs, key=lambda x: safeFloat(x["priceChangePercent"]), reverse=True
            )[start:end]
            topLosers = sorted(
                usdtPairs, key=lambda x: safeFloat(x["priceChangePercent"])
            )[start:end]
            return topGainers, topLosers
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return [], []
    
    def getPriceMinutesAgo(self, symbols, minutes):
        import time

        timestamp = int(time.time() * 1000) - minutes * 60 * 1000
        url = f"{self.baseUrl}/aggTrades"
        prices = {}
        for symbol in symbols:
            params = {"symbol": symbol, "startTime": timestamp, "limit": 1}
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    prices[symbol] = float(data[-1]["p"])
                else:
                    print(
                        f"No trade data found for {symbol} within the last {minutes} minutes."
                    )
            else:
                print(f"Failed to fetch price for {symbol}: {response.status_code}")
        return prices
    
    def getCurrentPrices(self, symbols):
        url = f"{self.baseUrl}/ticker/price"
        response = requests.get(url)
        if response.status_code == 200:
            prices = response.json()
            return {
                price["symbol"]: float(price["price"])
                for price in prices
                if price["symbol"] in symbols
            }
        else:
            print(f"Failed to fetch current prices: {response.status_code}")
            return {}
