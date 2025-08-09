import json
import re


def match_symbols(symbols, exchange):
    """
    Match a list of symbols to the markets supported by the given exchange.

    Parameters
    ----------
    symbols : list
        List of symbols to match
    exchange : str
        Exchange to match the symbols against

    Returns
    -------
    list
        List of matched symbols
    """

    with open("config/supported_markets.json", "r") as f:
        supported_markets = json.load(f)

    if exchange not in supported_markets:
        print(f"Exchange {exchange} not supported.")
        return []

    usdt_pattern = re.compile(
        r"([A-Za-z]+)\d*/USDT:USDT$|(\d*[A-Za-z]+)\s*/\s*USDT:USDT$"
    )

    matched_symbols = []

    for symbol in symbols:
        matched_symbol = None
        shortest_match = None
        for market in supported_markets[exchange]:
            match = usdt_pattern.match(market)
            if match:
                base_symbol = match.group(1) if match.group(1) else match.group(2)
                if symbol in base_symbol:
                    if shortest_match is None or len(base_symbol) < len(shortest_match):
                        shortest_match = base_symbol
                        matched_symbol = market
        if matched_symbol:
            matched_symbols.append(matched_symbol)

    return matched_symbols
