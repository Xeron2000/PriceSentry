def monitorTopMovers(minutes, symbols, threshold=2.0, is_custom=False):
    from exchanges.binance import getPriceMinutesAgo, getCurrentPrices

    initial_prices = getPriceMinutesAgo(symbols, minutes)
    updated_prices = getCurrentPrices(symbols)

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

    message = (
        f"\nTop Movers in the last {minutes} minutes (Threshold: {threshold}%):\n"
        if not is_custom
        else f"\nTop Movers for custom symbols in the last {minutes} minutes (Threshold: {threshold}%):\n"
    )

    for symbol, change in top_movers_sorted[:5]:
        message += f"Symbol: {symbol}, Price Change: {change:.2f}%\n"

    return message
