import ccxt.async_support as ccxt
import asyncio
from datetime import datetime, timedelta
from expiringdict import ExpiringDict
import logging

logger = logging.getLogger(__name__)

class Exchange:
    def __init__(self, exchangeName):
        """
        Initialize the Exchange class for asynchronous operations.

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
        self.cache = ExpiringDict(max_len=1000, max_age_seconds=300)  # Initialize cache for prices with TTL

    async def get_cached_price(self, symbol, since):
        """
        Retrieves the cached price for a given symbol and timestamp asynchronously.
        """
        key = f"{symbol}-{since}"
        return self.cache.get(key)

    async def set_cached_price(self, symbol, price, since):
        """
        Sets the cached price for a given symbol, price, and timestamp asynchronously.
        """
        key = f"{symbol}-{since}"
        self.cache[key] = price

    async def fetchPrice(self, symbol, since=None, retries=3):
        """
        Fetches the current price of a given symbol from the exchange asynchronously.

        If a 'since' timestamp is provided, it fetches the OHLCV data from that time
        and returns the closing price of the last entry. If 'since' is not provided,
        it fetches the current ticker price asynchronously.

        Args:
            symbol (str): The symbol for which to fetch the price.
            since (int, optional): The timestamp in milliseconds since when to fetch the price.
            retries (int, optional): Number of retries for fetching price data.

        Returns:
            float or None: The latest price of the symbol, or None if fetching fails.

        Raises:
            ccxt.NetworkError: If there is a network-related error during the fetch.
            ccxt.ExchangeError: If there is an exchange-related error during the fetch.
            Exception: If an unexpected error occurs.
        """
        cached_price = await self.get_cached_price(symbol, since)
        if cached_price:
            return cached_price

        for attempt in range(retries):
            try:
                if since:
                    ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe='1m', since=since)
                    if ohlcv:
                        price = ohlcv[-1][4]
                    else:
                        price = None
                else:
                    ticker = await self.exchange.fetch_ticker(symbol)
                    price = float(ticker.get('last', 0))
                await self.set_cached_price(symbol, price, since)  # Cache the fetched price
                return price
            except ccxt.NetworkError as e:
                logger.warning(f"Network error while fetching data for {symbol} (Attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)  # Wait before retrying
                else:
                    raise # Propagate exception after max retries
            except ccxt.ExchangeError as e:
                logger.warning(f"Exchange error while fetching data for {symbol} (Attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)  # Wait before retrying
                else:
                    raise # Propagate exception after max retries
            except Exception as e:
                print(f"Failed to fetch price for {symbol}: {e}")
                return None  # Return None if fails after all retries or other exceptions
        return None # Return None if fails after all retries

    async def getPriceMinutesAgo(self, symbols, minutes):
        """
        Retrieves the prices of specified symbols from the exchange as of a given number of minutes ago asynchronously.

        This method calculates the timestamp for the specified number of minutes in the past and uses
        it to fetch the historical price data for each symbol asynchronously. If no price data is available for a
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
            return await self.fetchPrice(symbol, since)

        async def get_prices_async():
            tasks = [fetch_price_async(symbol, since) for symbol in symbols]
            return await asyncio.gather(*tasks, return_exceptions=True)

        results = await get_prices_async()
        prices = {}
        for symbol, price in zip(symbols, results):
            if isinstance(price, Exception) or price is None:
                print(f"No trades for {symbol} in the last {minutes} minutes.")
                prices[symbol] = None
            else:
                prices[symbol] = price
        return prices

    async def getCurrentPrices(self, symbols):
        """
        Retrieves the current prices of the specified symbols from the exchange asynchronously.

        Args:
            symbols (list): A list of symbol strings for which to fetch prices.

        Returns:
            dict: A dictionary where each key is a symbol and the value is the current price,
                or None if fetching fails.
        """
        prices = {}
        for symbol in symbols:
            try:
                if self.exchange.has['fetchTicker']:
                    ticker = await self.exchange.fetch_ticker(symbol)
                    prices[symbol] = float(ticker['last'])
            except Exception as e:
                print(f"Ticker not found for {symbol}. Error: {e}")
                prices[symbol] = None
        return prices

    async def close(self):
        await self.exchange.close()

    def align_since(self, minutes_ago):
        """
        Aligns the 'since' timestamp to the start of the minute, considering exchange timezones.
        """
        now = datetime.now() - timedelta(minutes=minutes_ago)
        aligned = now.replace(second=0, microsecond=0)
        return int(aligned.timestamp() * 1000)
