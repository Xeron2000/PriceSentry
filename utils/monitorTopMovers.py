from datetime import datetime
import pytz

def monitorTopMovers(minutes, symbols, threshold, exchange, config):
    """
    Retrieves the top movers for the given symbols on the given exchange over the given time period.

    Args:
        minutes (int): The number of minutes in the past to monitor.
        symbols (list): A list of symbol strings for which to fetch prices.
        threshold (float): The minimum percentage price change required to be a "top mover".
        exchange (Exchange): An instance of the Exchange class which implements the
            'getPriceMinutesAgo' and 'getCurrentPrices' methods.
        config (dict): Configuration dictionary loaded from config.yaml

    Returns:
        str or None: A message string detailing the top movers, or None if no movers meet the threshold.
    """
    if exchange is None or not all(
        hasattr(exchange, method) for method in ['getPriceMinutesAgo', 'getCurrentPrices']
    ):
        raise ValueError("Exchange must implement 'getPriceMinutesAgo' and 'getCurrentPrices' methods")

    initial_prices = exchange.getPriceMinutesAgo(symbols, minutes)
    updated_prices = exchange.getCurrentPrices(symbols)

    price_changes = {
        symbol: ((updated_prices[symbol] - initial_prices[symbol]) / initial_prices[symbol]) * 100
        for symbol in initial_prices if symbol in updated_prices
        if abs((updated_prices[symbol] - initial_prices[symbol]) / initial_prices[symbol]) * 100 > threshold
    }

    if not price_changes:
        return None

    top_movers_sorted = sorted(price_changes.items(), key=lambda x: abs(x[1]), reverse=True)
    timezone_str = config.get('notificationTimezone', 'Asia/Shanghai')
    timezone = pytz.timezone(timezone_str)
    current_time = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
    message = (f"\nTop Movers for symbols on {exchange.exchangeName} in the last {minutes} minutes (Threshold: {threshold}%):\n"
                f"Timestamp: {current_time}\n")

    for symbol, change in top_movers_sorted[:5]:
        message += f"Symbol: {symbol}, Price Change: {change:.2f}%\n"

    return message
