import ccxt
import asyncio
from datetime import datetime, timedelta


class Exchange:
    def __init__(self, exchangeName):
        """
        Initialize the Exchange class.

        Args:
            exchangeName (str): The name of the exchange that this object represents.

        Raises:
            ValueError: If the provided exchange name is not supported by ccxt.

        """
        if exchangeName.lower() not in ccxt.exchanges:
            raise ValueError(f"Exchange '{exchangeName}' is not supported by ccxt.")
        
        self.exchangeName = exchangeName.capitalize()
        self.exchange = getattr(ccxt, exchangeName.lower())({
            'rateLimit': 1000,
            'enableRateLimit': True,
        })
        self.cache = {}  # Initialize cache

    def get_cached_price(self, symbol, since):
        """
        Retrieves the cached price for a given symbol and timestamp.
        """
        key = f"{symbol}-{since}"
        return self.cache.get(key)

    def set_cached_price(self, symbol, price, since):
        """
        Sets the cached price for a given symbol, price, and timestamp.
        """
        key = f"{symbol}-{since}"
        self.cache[key] = price

    def fetchPrice(self, symbol, since=None):
        """
        Fetches the current price of a given symbol from the exchange.

        If a 'since' timestamp is provided, it fetches the OHLCV data from that time
        and returns the closing price of the last entry. If 'since' is not provided,
        it fetches the current ticker price.

        Args:
            symbol (str): The symbol for which to fetch the price.
            since (int, optional): The timestamp in milliseconds since when to fetch the price.

        Returns:
            float or None: The latest price of the symbol, or None if fetching fails.

        Raises:
            ccxt.NetworkError: If there is a network-related error during the fetch.
            ccxt.ExchangeError: If there is an exchange-related error during the fetch.
            Exception: If an unexpected error occurs.
        """
        cached_price = self.get_cached_price(symbol, since)
        if cached_price:
            return cached_price

        try:
            if since:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1m', since=since)
                if ohlcv:
                    price = ohlcv[-1][4]
                else:
                    price = None
            else:
                ticker = self.exchange.fetch_ticker(symbol)
                price = float(ticker.get('last', 0))
            self.set_cached_price(symbol, price, since)  # Cache the fetched price
            return price
        except ccxt.NetworkError as e:
            print(f"Network error while fetching data for {symbol}: {e}")
        except ccxt.ExchangeError as e:
            print(f"Exchange error while fetching data for {symbol}: {e}")
        except Exception as e:
            print(f"Failed to fetch price for {symbol}: {e}")
        return None

    def getPriceMinutesAgo(self, symbols, minutes):
        """
        Retrieves the prices of specified symbols from the exchange as of a given number of minutes ago.

        This method calculates the timestamp for the specified number of minutes in the past and uses 
        it to fetch the historical price data for each symbol. If no price data is available for a 
        symbol in the specified time range, a message is printed.

        Args:
            symbols (list): A list of symbol strings for which to fetch prices.
            minutes (int): The number of minutes in the past to retrieve the prices from.

        Returns:
            dict: A dictionary where each key is a symbol and the value is the latest price
                as of the specified number of minutes ago, or None if fetching fails.
        """

        since = int((datetime.now() - timedelta(minutes=minutes)).timestamp() * 1000)
        async def fetch_price_async(symbol, since):
            return self.fetchPrice(symbol, since)

        async def get_prices_async():
            tasks = [fetch_price_async(symbol, since) for symbol in symbols]
            return await asyncio.gather(*tasks, return_exceptions=True)

        results = asyncio.run(get_prices_async())
        prices = {}
        for symbol, price in zip(symbols, results):
            if isinstance(price, Exception) or price is None:
                print(f"No trades for {symbol} in the last {minutes} minutes.")
                prices[symbol] = None
            else:
                prices[symbol] = price
        return prices

    def getCurrentPrices(self, symbols):
        """
        Retrieves the current prices of the specified symbols from the exchange.

        Args:
            symbols (list): A list of symbol strings for which to fetch prices.

        Returns:
            dict: A dictionary where each key is a symbol and the value is the current price,
                or None if fetching fails.
        """
        tickers = self.exchange.fetch_tickers(symbols)
        prices = {}
        for symbol in symbols:
            ticker = tickers.get(symbol)
            if ticker:
                prices[symbol] = float(ticker['last'])
            else:
                print(f"Ticker not found for {symbol}.")
                prices[symbol] = None  # Or consider excluding from prices dict
        return prices
