
from exchanges import BinanceExchange, OkxExchange


def get_exchange(exchange_name):
    """
    Create an instance of an Exchange class based on the name provided.

    Args:
        exchange_name (str): The name of the exchange to create an instance of.

    Returns:
        Exchange: An instance of an Exchange class.

    Raises:
        ValueError: If the provided exchange name is not supported.
    """
    if exchange_name.lower() == "okx":
        return OkxExchange()
    elif exchange_name.lower() == "binance":
        return BinanceExchange()
    else:
        raise ValueError(f"Exchange {exchange_name} not supported.")
