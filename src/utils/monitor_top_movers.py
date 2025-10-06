from datetime import datetime

import pytz


async def monitor_top_movers(minutes, symbols, threshold, exchange, config):
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
        tuple[str, list[tuple[str, float]]] | None: (message, top_movers_sorted) where
            top_movers_sorted is a list of (symbol, percent_change). Returns None if
            no movers meet the threshold.
    """
    if exchange is None or not all(
        hasattr(exchange, method)
        for method in ["get_price_minutes_ago", "get_current_prices"]
    ):
        raise ValueError(
            "Exchange must implement 'get_price_minutes_ago' and 'get_current_prices' "
            "methods"
        )

    initial_prices = exchange.get_price_minutes_ago(symbols, minutes)

    updated_prices = await exchange.get_current_prices(symbols)

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

    header = f"**📈 {exchange.exchange_name} Top 6 Movers ({minutes}m)**\n\n"
    time_info = f"**Time:** {current_time} ({timezone_str})\n"
    stats = (
        f"**Threshold:** {threshold}% | **Symbols:** {len(symbols)} | "
        f"**Alerts:** {len(price_changes)}\n\n"
    )
    message = header + time_info + stats

    for i, (symbol, change) in enumerate(top_movers_sorted[:6], 1):
        price_diff = updated_prices[symbol] - initial_prices[symbol]
        arrow = "🔼" if change > 0 else "🔽"
        color = "🟢" if change > 0 else "🔴"
        price_range = (
            f"(*{initial_prices[symbol]:.4f}* → *{updated_prices[symbol]:.4f}*)"
        )
        message += (
            f"{color} **{i}. `{symbol}`**\n"
            f"   - **Change:** {arrow} {abs(change):.2f}%\n"
            f"   - **Diff:** {price_diff:+.4f} {price_range}\n\n"
        )

    return message, top_movers_sorted
