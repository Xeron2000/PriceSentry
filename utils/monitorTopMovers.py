from datetime import datetime

import pytz


async def monitorTopMovers(minutes, symbols, threshold, exchange, config):
    """
    Retrieves the top movers for the given symbols on the given exchange
    over the given time period asynchronously.

    Args:
        minutes (int): The number of minutes in the past to monitor.
        symbols (list): A list of symbol strings for which to fetch prices.
        threshold (float): The minimum percentage price change required to be a
            "top mover".
        exchange (Exchange): An instance of the Exchange class which implements the
            'getPriceMinutesAgo' and 'getCurrentPrices' methods.
        config (dict): Configuration dictionary loaded from config.yaml

    Returns:
        str or None: A message string detailing the top movers, or None if no
            movers meet the threshold.
    """
    if exchange is None or not all(
        hasattr(exchange, method)
        for method in ["getPriceMinutesAgo", "getCurrentPrices"]
    ):
        raise ValueError(
            "Exchange must implement 'getPriceMinutesAgo' and 'getCurrentPrices' "
            "methods"
        )

    initial_prices = exchange.getPriceMinutesAgo(symbols, minutes)

    updated_prices = await exchange.getCurrentPrices(symbols)

    price_changes = {
        symbol: (
            (updated_prices[symbol] - initial_prices[symbol]) / initial_prices[symbol]
        )
        * 100
        for symbol in initial_prices
        if symbol in updated_prices
        if abs(
            (updated_prices[symbol] - initial_prices[symbol]) / initial_prices[symbol]
        )
        * 100
        > threshold
    }

    if not price_changes:
        return None

    top_movers_sorted = sorted(
        price_changes.items(), key=lambda x: abs(x[1]), reverse=True
    )
    timezone_str = config.get("notificationTimezone", "Asia/Shanghai")
    timezone = pytz.timezone(timezone_str)
    current_time = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")

    message = (
        f"📊 **{exchange.exchangeName} Price Alert** ({minutes} minutes)\n"
        f"▫️ Time: {current_time} ({timezone_str})\n"
        f"▫️ Threshold: {threshold}% | Symbols: {len(symbols)} → Alerts: "
        f"{len(price_changes)}\n"
        f"══════════════════\n"
    )

    for i, (symbol, change) in enumerate(top_movers_sorted[:5], 1):
        price_diff = updated_prices[symbol] - initial_prices[symbol]
        arrow = "↑" if change > 0 else "↓"
        color = "🟢" if change > 0 else "🔴"
        message += (
            f"{color} **{i}. #{symbol.ljust(6)}** {arrow} {abs(change):.2f}%\n"
            f"├ Current: {updated_prices[symbol]:.4f}\n"
            f"└ Change: {price_diff:+.4f} ({initial_prices[symbol]:.4f} → "
            f"{updated_prices[symbol]:.4f})\n\n"
        )

    message += (
        f"══════════════════\n"
        f"Note: Volatility threshold {threshold}% | Data precision: 4 decimal places\n"
        f"⚠️ Market risk: Invest with caution"
    )

    return message
