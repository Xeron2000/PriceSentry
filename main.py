import asyncio
import logging
import traceback

from core.sentry import PriceSentry
from utils.setup_logging import setup_logging


async def main():
    try:
        sentry = PriceSentry()
        log_level = sentry.config.get("logLevel", "INFO")
        setup_logging(log_level)
        await sentry.run()
    except Exception as e:
        logging.error(f"An error occurred in main: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
