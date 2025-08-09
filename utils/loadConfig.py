import logging

import yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def loadConfig(configPath="config/config.yaml"):
    """
    Loads the configuration from a YAML file.

    Args:
        configPath (str): The path to the configuration file.

    Returns:
        dict: The configuration as a dictionary.

    Raises:
        ValueError: If the configuration is missing any of the required keys.
        Exception: If there is an error loading the configuration.

    Required keys in the configuration file:
        - 'exchange': The name of the exchange to connect to.
        - 'symbolsFilePath': The file path containing trading pair symbols.
        - 'defaultTimeframe': The default timeframe (frequency of data retrieval).
        - 'defaultThreshold': The default price change threshold.
        - 'notificationChannels': The channels for receiving notifications.
    """
    try:
        with open(configPath, "r") as file:
            config = yaml.safe_load(file)
        required_keys = [
            "exchange",
            "symbolsFilePath",
            "defaultTimeframe",
            "defaultThreshold",
            "notificationChannels",
            "notificationTimezone",
        ]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")

        if "notificationTimezone" not in config or not config["notificationTimezone"]:
            config["notificationTimezone"] = "Asia/Shanghai"  # Default timezone

        return config
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        raise
