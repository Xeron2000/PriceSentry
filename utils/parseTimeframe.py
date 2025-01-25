def parseTimeframe(timeframe):
    """
    Converts a timeframe string into minutes.

    The input string should represent a timeframe, ending with 'm', 'h', or 'd',
    indicating minutes, hours, and days respectively. The numeric part of the string 
    is parsed and converted to minutes.

    Args:
        timeframe (str): A string representing a timeframe, e.g., '15m', '2h', '1d'.

    Returns:
        int: The equivalent number of minutes.

    Raises:
        ValueError: If the timeframe format is invalid or not recognized.
    """

    if timeframe.endswith("m"):
        return int(timeframe[:-1])
    elif timeframe.endswith("h"):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith("d"):
        return int(timeframe[:-1]) * 1440
    else:
        raise ValueError("Invalid timeframe format. Use 'Xm', 'Xh', or 'Xd'.")
