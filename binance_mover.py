import os
import requests
import time
import argparse
import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_message_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")

def get_binance_top_gainers_and_losers(limit=10):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        usdt_pairs = [coin for coin in data if coin['symbol'].endswith('USDT')]
        top_gainers = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)[:limit]
        top_losers = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']))[:limit]
        return top_gainers, top_losers
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return [], []

def get_price_n_minutes_ago(symbols, minutes):
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
            print(f"Failed to fetch price for {symbol}: {response.status_code}")

    return prices

def get_current_prices(symbols):
    url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url)

    if response.status_code == 200:
        prices = response.json()
        return {price['symbol']: float(price['price']) for price in prices if price['symbol'] in symbols}
    else:
        print(f"Failed to fetch current prices: {response.status_code}")
        return {}

def load_symbols_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]

def monitor_top_movers_once(minutes, symbols):
    initial_prices = get_price_n_minutes_ago(symbols, minutes)
    updated_prices = get_current_prices(symbols)

    price_changes = {}
    for symbol in initial_prices:
        if symbol in updated_prices:
            price_change = ((updated_prices[symbol] - initial_prices[symbol]) / initial_prices[symbol]) * 100
            price_changes[symbol] = price_change

    top_movers_sorted = sorted(price_changes.items(), key=lambda x: abs(x[1]), reverse=True)

    message = f"\nTop 5 Movers in the last {minutes} minutes:\n"
    for symbol, change in top_movers_sorted[:5]:
        message += f"Symbol: {symbol}, Price Change: {change:.2f}%\n"

    print(message)
    send_message_to_telegram(message)
def parse_timeframe(timeframe):
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

    args = parser.parse_args()

    try:
        timeframe_minutes = parse_timeframe(args.timeframe)
        
        if args.symbols:
            symbols_to_monitor = load_symbols_from_file(args.symbols)
            if not symbols_to_monitor:
                print("No valid symbols found. Exiting.")
                exit(1)
        else:
            top_gainers, top_losers = get_binance_top_gainers_and_losers()
            symbols_to_monitor = [coin['symbol'] for coin in top_gainers + top_losers]

        monitor_top_movers_once(timeframe_minutes, symbols_to_monitor)
    except ValueError as e:
        print(e)
        exit(1)
