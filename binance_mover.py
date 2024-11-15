import os
import requests
import time
import argparse

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def sendTelegramMessage(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

def getTopGainersAndLosers(start, end):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        usdt_pairs = [coin for coin in data if coin['symbol'].endswith('USDT')]

        def safeFloat(val):
            try:
                return float(val)
            except ValueError:
                return 0.0

        topGainers = sorted(usdt_pairs, key=lambda x: safeFloat(x['priceChangePercent']), reverse=True)[start:end]
        topLosers = sorted(usdt_pairs, key=lambda x: safeFloat(x['priceChangePercent']))[start:end]

        return topGainers, topLosers
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return [], []


def getPriceMinutesAgo(symbols, minutes):
    timestamp = int(time.time() * 1000) - minutes * 60 * 1000
    url = "https://api.binance.com/api/v3/aggTrades"

    prices = {}
    for symbol in symbols:
        params = {
            'symbol': symbol,
            'startTime': timestamp,
            'limit': 1
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                prices[symbol] = float(data[-1]['p'])
            else:
                print(f"No trade data found for {symbol} within the last {minutes} minutes.")
        else:
            print(f"Failed to fetch price for {symbol}: {response.status_code}")

    return prices

def getCurrentPrices(symbols):
    url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url)

    if response.status_code == 200:
        prices = response.json()
        return {price['symbol']: float(price['price']) for price in prices if price['symbol'] in symbols}
    else:
        print(f"Failed to fetch current prices: {response.status_code}")
        return {}

def loadSymbolsFromFile(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []

    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]

def monitorTopMovers(minutes, symbols, threshold=2.0, is_custom=False):
    initial_prices = getPriceMinutesAgo(symbols, minutes)
    updated_prices = getCurrentPrices(symbols)

    price_changes = {}
    for symbol in initial_prices:
        if symbol in updated_prices:
            price_change = ((updated_prices[symbol] - initial_prices[symbol]) / initial_prices[symbol]) * 100
            if abs(price_change) > threshold:
                price_changes[symbol] = price_change

    if not price_changes:
        return None

    top_movers_sorted = sorted(price_changes.items(), key=lambda x: abs(x[1]), reverse=True)

    if is_custom:
        message = f"\nTop Movers for custom symbols in the last {minutes} minutes (Threshold: {threshold}%):\n"
    else:
        message = f"\nTop Movers in the last {minutes} minutes (Threshold: {threshold}%):\n"

    for symbol, change in top_movers_sorted[:5]:
        message += f"Symbol: {symbol}, Price Change: {change:.2f}%\n"

    return message

def parseTimeframe(timeframe):
    if timeframe.endswith('m'):
        return int(timeframe[:-1])
    elif timeframe.endswith('h'):
        return int(timeframe[:-1]) * 60
    elif timeframe.endswith('d'):
        return int(timeframe[:-1]) * 1440
    else:
        raise ValueError("Invalid timeframe format. Use 'Xm', 'Xh', or 'Xd'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor top gainers and losers on Binance.")
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe to check (e.g., 15m, 1h, 1d)')
    parser.add_argument('--symbols', type=str, help='Path to a file containing symbols to monitor (one per line)')
    parser.add_argument('--start', type=int, default=0, help='Starting rank of gainers/losers (default: 0)')
    parser.add_argument('--end', type=int, default=10, help='Ending rank of gainers/losers (default: 10)')
    parser.add_argument('--threshold', type=float, default=2.0, help='Minimum percentage change to display (default: 2%)')

    args = parser.parse_args()

    try:
        timeframe_minutes = parseTimeframe(args.timeframe)

        top_gainers, top_losers = getTopGainersAndLosers(args.start, args.end)

        symbols_to_monitor = [coin['symbol'] for coin in top_gainers + top_losers]
        default_message = monitorTopMovers(timeframe_minutes, symbols_to_monitor, args.threshold)

        custom_message = ""
        if args.symbols:
            custom_symbols = loadSymbolsFromFile(args.symbols)
            if custom_symbols:
                custom_message = monitorTopMovers(timeframe_minutes, custom_symbols, args.threshold, is_custom=True)
            else:
                print("No valid symbols found in the file. Exiting.")
                exit(1)

        full_message = (default_message or "") + (custom_message or "")
        if full_message.strip():
            print(full_message)
            sendTelegramMessage(full_message)
        else:
            print(f"No price changes exceed the threshold of {args.threshold}%. No message sent.")

    except ValueError as e:
        print(e)
        exit(1)
