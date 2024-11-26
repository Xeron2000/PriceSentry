import yaml
from notifications.telegram import sendTelegramMessage
from notifications.dingding import sendDingDingMessage
from exchanges.binance import BinanceExchange
from utils.fileUtils import loadSymbolsFromFile
from utils.priceUtils import monitorTopMovers
from utils.timeUtils import parseTimeframe

def loadConfig(configPath='config/config.yaml'):
    with open(configPath, 'r') as file:
        return yaml.safe_load(file)

def getExchange(exchangeName):
    if exchangeName == "binance":
        return BinanceExchange()
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
    symbols = []

    if symbolsFilePath:
        symbols = loadSymbolsFromFile(symbolsFilePath)
    else:
        defaultStart = config['defaultStart']
        defaultEnd = config['defaultEnd']
        topGainers, topLosers = exchange.getTopGainersAndLosers(defaultStart, defaultEnd)
        symbols = [coin['symbol'] for coin in topGainers] + [coin['symbol'] for coin in topLosers]

    defaultTimeframe = config['defaultTimeframe']
    defaultThreshold = config['defaultThreshold']
    timeframe_minutes = parseTimeframe(defaultTimeframe)

    notificationChannels = config['notificationChannels']
    telegram_config = config.get('telegram', {})
    dingding_config = config.get('dingding', {})

    if symbols:
        message = monitorTopMovers(
            timeframe_minutes, symbols, defaultThreshold, is_custom=bool(symbolsFilePath), exchange=exchange
        )
        if message:
            print(f"Message to be sent:\n{message}")
            sendNotifications(message, notificationChannels, telegram_config, dingding_config)
        else:
            print("No price changes exceed the threshold.")
    else:
        print("No symbols to monitor.")

if __name__ == "__main__":
    main()
