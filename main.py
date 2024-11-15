import argparse
from config import parseTimeframe
from utils.api import getTopGainersAndLosers, getCurrentPrices, getPriceMinutesAgo
from utils.file_io import loadSymbolsFromFile
from utils.price_analysis import monitorTopMovers
from telegram.notifier import sendTelegramMessage

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor top gainers and losers on Binance."
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="15m",
        help="Timeframe to check (e.g., 15m, 1h, 1d)",
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help="Path to a file containing symbols to monitor (one per line)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Starting rank of gainers/losers (default: 0)",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=10,
        help="Ending rank of gainers/losers (default: 10)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Minimum percentage change to display (default: 2%)",
    )

    args = parser.parse_args()

try:
    timeframe_minutes = parseTimeframe(args.timeframe)
    top_gainers, top_losers = getTopGainersAndLosers(args.start, args.end)

    if args.symbols:
        custom_symbols = loadSymbolsFromFile(args.symbols)
        if custom_symbols:
            custom_message = monitorTopMovers(
                timeframe_minutes, custom_symbols, args.threshold, is_custom=True
            )
            if custom_message:
                print(custom_message)
                sendTelegramMessage(custom_message)
            else:
                print(f"No price changes exceed the threshold of {
                      args.threshold}% for custom symbols.")
        else:
            print("No valid symbols found in the file. Exiting.")
            exit(1)

    else:
        symbols_to_monitor = [coin["symbol"]
                              for coin in top_gainers + top_losers]
        default_message = monitorTopMovers(
            timeframe_minutes, symbols_to_monitor, args.threshold
        )
        if default_message:
            print(default_message)
            sendTelegramMessage(default_message)
        else:
            print(f"No price changes exceed the threshold of {
                  args.threshold}% in top gainers/losers.")

except ValueError as e:
    print(e)
    exit(1)
