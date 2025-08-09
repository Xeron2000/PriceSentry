import asyncio
import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler

from core.sentry import PriceSentry

# Configure logging
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Use RotatingFileHandler
file_handler = RotatingFileHandler(
    "pricesentry.log", maxBytes=5 * 1024 * 1024, backupCount=5
)
file_handler.setFormatter(log_formatter)

# Stream handler for console output
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)

# Get root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Default to INFO level
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


async def main():
    try:
        sentry = PriceSentry()
        
        # Allow overriding log level from config
        log_level = sentry.config.get('logLevel', 'INFO').upper()
        logger.setLevel(log_level)
        
        await sentry.run()
    except Exception as e:
        logging.error(f"An error occurred in main: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
