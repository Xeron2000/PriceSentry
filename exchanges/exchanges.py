import ccxt
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

        try:
            if since:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1m', since=since)
                if ohlcv:
                    return ohlcv[-1][4]
            else:
                ticker = self.exchange.fetch_ticker(symbol)
                return float(ticker.get('last', 0))
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
        prices = {symbol: self.fetchPrice(symbol, since) for symbol in symbols}
        for symbol, price in prices.items():
            if price is None:
                print(f"No trades for {symbol} in the last {minutes} minutes.")
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
        prices = {symbol: self.fetchPrice(symbol) for symbol in symbols}
        for symbol, price in prices.items():
            if price is None:
                print(f"Ticker not found for {symbol}.")
        return prices
