import asyncio
import logging
from utils.loadConfig import loadConfig
from utils.getExchange import getExchange
from utils.sendNotifications import sendNotifications
from utils.loadSymbolsFromFile import loadSymbolsFromFile
from utils.monitorTopMovers import monitorTopMovers
from utils.parseTimeframe import parseTimeframe
from utils.matchSymbols import matchSymbols

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    try:
        config = loadConfig()

        exchange = getExchange(config['exchange'])

        unmatched_symbols = loadSymbolsFromFile(config['symbolsFilePath'])

        symbols = matchSymbols(unmatched_symbols, config['exchange'])

        if not symbols:
            logging.error("No symbols found in the specified file.")
            return

        timeframe_minutes = parseTimeframe(config['defaultTimeframe'])

        message = await monitorTopMovers(
            timeframe_minutes, symbols, config['defaultThreshold'], exchange=exchange, config=config
        )

        if message:
            logging.info(f"Message to be sent:\n{message}")
            sendNotifications(message, config['notificationChannels'], config.get('telegram', {}), config.get('dingding', {}))
        else:
            logging.info("No price changes exceed the threshold.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if 'exchange' in locals():
            await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())
