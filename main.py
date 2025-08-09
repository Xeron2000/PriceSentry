import logging
import sys
import traceback
from core.sentry import PriceSentry

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pricesentry.log")
    ]
)

logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

def main():
    try:
        sentry = PriceSentry()
        sentry.run()
    except Exception as e:
        logging.error(f"An error occurred in main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
