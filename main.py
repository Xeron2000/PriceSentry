import json
from notifications.telegram import sendTelegramMessage
from exchanges.binance import BinanceExchange
from utils.fileUtils import loadSymbolsFromFile
from utils.priceUtils import monitorTopMovers
from utils.timeUtils import parseTimeframe

def loadConfig(configPath='config/config.json'):
    with open(configPath, 'r') as file:
        return json.load(file)

def getExchange(exchangeName):
    if exchangeName == "binance":
        return BinanceExchange()
    else:
        raise ValueError(f"Unsupported exchange: {exchangeName}")

def sendNotifications(message, notificationChannels, telegram_token, chat_id):
    for channel in notificationChannels:
        if channel == 'telegram':
            sendTelegramMessage(message, telegram_token, chat_id)
        else:
            print(f"Unsupported notification channel: {channel}")

def main():
    config = loadConfig()

    exchange = getExchange(config['exchange'])

    notificationChannels = config['notificationChannels']
    telegram_token = config.get("telegramToken")
    chat_id = config.get("chatId")

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

    if symbols:
        message = monitorTopMovers(
            timeframe_minutes, symbols, defaultThreshold, is_custom=bool(symbolsFilePath), exchange=exchange
        )
        if message:
            print(f"Message to be sent:\n{message}")
            sendNotifications(message, notificationChannels, telegram_token, chat_id)
        else:
            print("No price changes exceed the threshold.")
    else:
        print("No symbols to monitor.")

if __name__ == "__main__":
    main()
