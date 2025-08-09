import logging

from exchanges.exchanges import Exchange


def getExchange(exchangeName):
    """
    Create an instance of an Exchange class based on the name provided.

    Args:
        exchangeName (str): The name of the exchange to create an instance of.

    Returns:
        Exchange: An instance of an Exchange class.

    Raises:
        ValueError: If the provided exchange name is not supported.
    """
    try:
        return Exchange(exchangeName)
    except ValueError as e:
        logging.error(e)
        raise
