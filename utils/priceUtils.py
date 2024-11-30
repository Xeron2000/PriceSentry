def monitorTopMovers(minutes, symbols, threshold, is_custom=False, exchange=None):
    if exchange is None or not hasattr(exchange, 'getPriceMinutesAgo') or not hasattr(exchange, 'getCurrentPrices'):
        raise ValueError("Exchange must implement 'getPriceMinutesAgo' and 'getCurrentPrices' methods")

    initial_prices = exchange.getPriceMinutesAgo(symbols, minutes)
    updated_prices = exchange.getCurrentPrices(symbols)

    price_changes = {}
    for symbol in initial_prices:
        if symbol in updated_prices:
            price_change = (
                (updated_prices[symbol] - initial_prices[symbol])
                / initial_prices[symbol]
            ) * 100
            if abs(price_change) > threshold:
                price_changes[symbol] = price_change

    if not price_changes:
        return None
    
    top_movers_sorted = sorted(
        price_changes.items(), key=lambda x: abs(x[1]), reverse=True
    )

    message = (f"\nTop Movers for custom symbols on {exchange.exchange_name} in the last {minutes} minutes (Threshold: {threshold}%):\n")

    for symbol, change in top_movers_sorted[:5]:
        message += f"Symbol: {symbol}, Price Change: {change:.2f}%\n"

    return message
