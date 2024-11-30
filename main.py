import yaml
from notifications.telegram import sendTelegramMessage
from notifications.dingding import sendDingDingMessage
from exchanges.binance import BinanceExchange
from exchanges.okx import OKXExchange
from utils.fileUtils import loadSymbolsFromFile
from utils.priceUtils import monitorTopMovers
from utils.timeUtils import parseTimeframe


def loadConfig(configPath='config/config.yaml'):
    with open(configPath, 'r') as file:
        return yaml.safe_load(file)


def getExchange(exchangeName):
    if exchangeName == "binance":
        return BinanceExchange()
    elif exchangeName == "okx":
        return OKXExchange()
    else:
        raise ValueError(f"Unsupported exchange: {exchangeName}")


def sendNotifications(message, notificationChannels, telegram_config, dingding_config):
    for channel in notificationChannels:
        if channel == 'telegram':
            sendTelegramMessage(
                message, telegram_config['token'], telegram_config['chatId']
            )
        elif channel == 'dingding':
            sendDingDingMessage(
                message, dingding_config['webhook'], dingding_config['secret']
            )
        else:
            print(f"Unsupported notification channel: {channel}")


def main():
    config = loadConfig()

    exchange = getExchange(config['exchange'])
    symbolsFilePath = config['symbolsFilePath']

    if not symbolsFilePath:
        print("Error: `symbolsFilePath` is not configured.")
        return

    symbols = loadSymbolsFromFile(symbolsFilePath)
    if not symbols:
        print("Error: No symbols found in the specified file.")
        return

    defaultTimeframe = config['defaultTimeframe']
    defaultThreshold = config['defaultThreshold']
    timeframe_minutes = parseTimeframe(defaultTimeframe)

    notificationChannels = config['notificationChannels']
    telegram_config = config.get('telegram', {})
    dingding_config = config.get('dingding', {})

    message = monitorTopMovers(
        timeframe_minutes, symbols, defaultThreshold, is_custom=True, exchange=exchange
    )
    if message:
        print(f"Message to be sent:\n{message}")
        sendNotifications(message, notificationChannels, telegram_config, dingding_config)
    else:
        print("No price changes exceed the threshold.")


if __name__ == "__main__":
    main()
