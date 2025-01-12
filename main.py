import yaml
import logging
from notifications.telegram import sendTelegramMessage
from notifications.dingding import sendDingDingMessage
from exchanges.exchanges import Exchange
from utils.fileUtils import loadSymbolsFromFile
from utils.priceUtils import monitorTopMovers
from utils.timeUtils import parseTimeframe

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def loadConfig(configPath='config/config.yaml'):
    try:
        with open(configPath, 'r') as file:
            config = yaml.safe_load(file)
        required_keys = ['exchange', 'symbolsFilePath', 'defaultTimeframe', 'defaultThreshold', 'notificationChannels']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
        return config
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        raise


def getExchange(exchangeName):
    try:
        return Exchange(exchangeName)
    except ValueError as e:
        logging.error(e)
        raise


def sendNotifications(message, notificationChannels, telegram_config, dingding_config):
    for channel in notificationChannels:
        try:
            if channel == 'telegram':
                sendTelegramMessage(
                    message, telegram_config['token'], telegram_config['chatId']
                )
            elif channel == 'dingding':
                sendDingDingMessage(
                    message, dingding_config['webhook'], dingding_config['secret']
                )
            else:
                logging.warning(f"Unsupported notification channel: {channel}")
        except Exception as e:
            logging.error(f"Failed to send message via {channel}: {e}")


def main():
    try:
        config = loadConfig()

        exchange = getExchange(config['exchange'])

        symbols = loadSymbolsFromFile(config['symbolsFilePath'])
        if not symbols:
            logging.error("No symbols found in the specified file.")
            return

        timeframe_minutes = parseTimeframe(config['defaultTimeframe'])

        message = monitorTopMovers(
            timeframe_minutes, symbols, config['defaultThreshold'], is_custom=True, exchange=exchange
        )

        if message:
            logging.info(f"Message to be sent:\n{message}")
            sendNotifications(message, config['notificationChannels'], config.get('telegram', {}), config.get('dingding', {}))
        else:
            logging.info("No price changes exceed the threshold.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
