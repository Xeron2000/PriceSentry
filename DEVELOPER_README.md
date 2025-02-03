# PriceSentry Developer Documentation

## Project Overview

PriceSentry is a lightweight cryptocurrency contract price monitoring tool designed for traders and enthusiasts. It tracks price movements on Binance and OKX exchanges and sends notifications via Telegram or DingTalk when significant price changes occur.

**Key Features:**

* **Multi-channel Notifications:** Supports Telegram and DingTalk.
* **Exchange Support:** Binance and OKX.
* **Timezone-Aware Notifications:** Notifications are displayed in the configured timezone.
* **YAML Configuration:** Secure configuration using YAML files.

## Architecture

PriceSentry follows a modular design, with the following key components:

* **`main.py`**: The main entry point of the application. It loads configurations, initializes the exchange, fetches symbols, monitors price movements, and sends notifications.
* **`exchanges/exchanges.py`**:  Handles interactions with cryptocurrency exchanges (Binance, OKX) using the `ccxt` library. It provides functionalities to fetch current and historical prices, with caching to improve performance and reduce API calls.
* **`utils/monitorTopMovers.py`**: Implements the core logic for monitoring price movements. It compares current prices with historical prices (fetched from `exchanges/exchanges.py`) and identifies top movers based on a configured threshold.
* **`utils/loadConfig.py`**: Loads configuration settings from `config/config.yaml`.
* **`utils/loadSymbolsFromFile.py`**: Loads trading symbols from a specified file (e.g., `config/symbols.txt`).
* **`utils/matchSymbols.py`**: Matches symbols from the symbols file with the symbols supported by the configured exchange.
* **`utils/parseTimeframe.py`**: Parses the timeframe string from the configuration file into minutes.
* **`utils/sendNotifications.py`**: Handles sending notifications via configured channels (Telegram, DingTalk).
* **`config/config.yaml`**: YAML configuration file for setting exchange, timeframe, threshold, notification channels, and API keys.
* **`config/symbols.txt`**:  A text file listing the trading symbols to monitor.

## Key Modules

### `main.py`

* **Purpose**: Entry point of the PriceSentry application.
* **Functionality**:
    * Loads configuration from `config/config.yaml` using `loadConfig.loadConfig()`.
    * Initializes the exchange client using `getExchange.getExchange()`.
    * Loads symbols to monitor from `config/symbols.txt` using `loadSymbolsFromFile.loadSymbolsFromFile()`.
    * Matches loaded symbols with exchange supported symbols using `matchSymbols.matchSymbols()`.
    * Parses the default timeframe using `parseTimeframe.parseTimeframe()`.
    * Calls `monitorTopMovers.monitorTopMovers()` to detect top price movers.
    * Sends notifications using `sendNotifications.sendNotifications()` if price changes exceed the threshold.
    * Handles exceptions and logs errors.
    * Closes the exchange connection gracefully.

### `exchanges/exchanges.py`

* **Purpose**:  Abstracts exchange interactions using the `ccxt` library.
* **Classes**:
    * `Exchange`:
        * **Initialization (`__init__`)**:
            * Takes `exchangeName` as input (e.g., "binance", "okx").
            * Validates exchange name against `ccxt.exchanges`.
            * Initializes `ccxt` exchange client with rate limiting enabled.
            * Initializes an `ExpiringDict` cache for prices to reduce API calls.
        * **`fetchPrice(symbol, since=None, retries=3)`**:
            * Fetches the price of a given `symbol`.
            * If `since` timestamp is provided, fetches OHLCV data and returns the closing price.
            * Implements caching of fetched prices with a TTL of 300 seconds.
            * Includes retry logic with exponential backoff for network and exchange errors.
        * **`getPriceMinutesAgo(symbols, minutes)`**:
            * Fetches prices of multiple `symbols` as of `minutes` ago.
            * Uses `fetchPrice` to get historical prices.
        * **`getCurrentPrices(symbols)`**:
            * Fetches current prices of multiple `symbols`.
            * Uses `fetch_ticker` to get current prices.
        * **`align_since(minutes_ago)`**:
            * Aligns the 'since' timestamp to the start of the minute.

### `utils/monitorTopMovers.py`

* **Purpose**:  Detects top price movers based on price changes over a specified time period.
* **Function**:
    * `monitorTopMovers(minutes, symbols, threshold, exchange, config)`:
        * Takes `minutes`, `symbols`, `threshold`, `exchange` (Exchange object), and `config` as input.
        * Fetches historical prices using `exchange.getPriceMinutesAgo()`.
        * Fetches current prices using `exchange.getCurrentPrices()`.
        * Calculates price changes as a percentage.
        * Identifies symbols with price changes exceeding the `threshold`.
        * Sorts top movers by price change percentage in descending order.
        * Formats a notification message with top movers' details, including symbol, price change percentage, current price, and price difference.
        * Returns the formatted message string or `None` if no movers exceed the threshold.

### `utils/loadConfig.py`

* **Purpose**: Loads and parses the configuration file (`config/config.yaml`).
* **Function**:
    * `loadConfig()`:
        * Reads `config/config.yaml`.
        * Parses YAML content and returns a configuration dictionary.
        * Handles file not found and YAML parsing errors.

### `utils/loadSymbolsFromFile.py`

* **Purpose**: Loads trading symbols from a text file.
* **Function**:
    * `loadSymbolsFromFile(symbolsFilePath)`:
        * Reads symbols from the file specified by `symbolsFilePath`.
        * Returns a list of symbols, stripping whitespace and newlines.
        * Handles file not found errors and returns an empty list if the file is not found.

### `utils/matchSymbols.py`

* **Purpose**: Matches provided symbols with symbols supported by the exchange.
* **Function**:
    * `matchSymbols(unmatched_symbols, exchange_name)`:
        * Takes a list of `unmatched_symbols` and `exchange_name` as input.
        * Initializes the specified exchange using `ccxt`.
        * Fetches markets from the exchange.
        * Filters markets to include only 'swap' markets (contract markets).
        * Extracts contract symbols from the exchange markets.
        * Finds the intersection between `unmatched_symbols` and exchange contract symbols to get matched symbols.
        * Returns a list of matched symbols.

### `utils/parseTimeframe.py`

* **Purpose**: Parses a timeframe string (e.g., "1m", "5m", "1h", "1d") into minutes.
* **Function**:
    * `parseTimeframe(timeframe_str)`:
        * Parses the `timeframe_str`.
        * Converts timeframe string to minutes.
        * Supports minute ('m'), hour ('h'), and day ('d') timeframes.
        * Returns the timeframe in minutes as an integer.
        * Raises ValueError for invalid timeframe formats.

### `utils/sendNotifications.py`

* **Purpose**: Sends notifications via configured channels (Telegram, DingTalk).
* **Function**:
    * `sendNotifications(message, notificationChannels, telegram_config, dingding_config)`:
        * Takes the notification `message`, a list of `notificationChannels`, and configuration dictionaries for `telegram` and `dingding`.
        * Iterates through `notificationChannels` and sends notifications via the specified channels.
        * For Telegram:
            * Sends message using Telegram Bot API if 'telegram' is in `notificationChannels` and Telegram configuration is provided.
        * For DingTalk:
            * Sends message using DingTalk Bot API if 'dingding' is in `notificationChannels` and DingTalk configuration is provided.
        * Logs success or failure for each notification channel.

## Configuration (`config/config.yaml`)

The `config/config.yaml` file is used to configure PriceSentry. Below is a sample configuration:

```yaml
# Exchange and default behavior configuration
exchange: "okx"          # Exchange to connect to ("binance", "okx")
defaultTimeframe: "1d"    # Default timeframe for price monitoring ("1m", "5m", "15m", "1h", "1d")
defaultThreshold: 1       # Default price change threshold (%)
symbolsFilePath: "config/symbols.txt" # Path to the symbols file

# Notification channels configuration
notificationChannels: 
  - "telegram"
  - "dingding"

# Telegram bot configuration
telegram:
  token: ""             # Telegram bot token
  chatId: ""            # Telegram chat ID

# DingTalk bot configuration
dingding:
  webhook: ""           # DingTalk webhook URL
  secret: ""            # DingTalk secret key

# Notification timezone
notificationTimezone: "Asia/Shanghai" # Timezone for notifications
```

**Configuration Parameters:**

* **`exchange`**:  The cryptocurrency exchange to monitor ("binance" or "okx").
* **`defaultTimeframe`**: The default timeframe for price monitoring (e.g., "1m", "5m", "1h", "1d").
* **`defaultThreshold`**: The default percentage threshold for price change alerts.
* **`symbolsFilePath`**: Path to the `symbols.txt` file containing symbols to monitor.
* **`notificationChannels`**: A list of notification channels to use (e.g., ["telegram", "dingding"]).
* **`telegram`**: Telegram bot configuration:
    * **`token`**: Telegram bot API token (required if "telegram" is in `notificationChannels`).
    * **`chatId`**: Telegram chat ID to send notifications to (required if "telegram" is in `notificationChannels`).
* **`dingding`**: DingTalk bot configuration:
    * **`webhook`**: DingTalk webhook URL (required if "dingding" is in `notificationChannels`).
    * **`secret`**: DingTalk secret key (required if DingTalk signature verification is enabled).
* **`notificationTimezone`**: Timezone for displaying notification times (e.g., "Asia/Shanghai", "America/New_York").

## Workflow

1. **Configuration Loading**:  `main.py` loads configuration from `config/config.yaml` using `loadConfig.py`.
2. **Exchange Initialization**:  `main.py` initializes the exchange client (Binance or OKX) based on the configuration using `exchanges/exchanges.py`.
3. **Symbol Loading**: `main.py` loads symbols to monitor from `config/symbols.txt` using `loadSymbolsFromFile.py` and matches them with supported symbols using `matchSymbols.py`.
4. **Price Monitoring**: `main.py` calls `monitorTopMovers.py` to monitor price movements for the loaded symbols.
5. **Price Change Detection**: `monitorTopMovers.py` fetches historical and current prices using `exchanges/exchanges.py`, calculates price changes, and identifies top movers exceeding the configured threshold.
6. **Notification Sending**: If top movers are detected, `main.py` calls `sendNotifications.py` to send notifications via configured channels (Telegram, DingTalk).
7. **Scheduled Execution**:  The application is intended to be run as a cron job to periodically monitor prices and send alerts.

## Customization and Extension

Developers can extend PriceSentry in several ways:

* **Adding Support for New Exchanges**:
    1. Implement a new exchange class in `exchanges/exchanges.py` that inherits from `ccxt.Exchange` and implements the required methods (`fetchPrice`, `getPriceMinutesAgo`, `getCurrentPrices`).
    2. Update `getExchange.py` to support the new exchange name.
    3. Add the new exchange name to the `exchange` configuration option in `config/config.yaml`.
* **Adding New Notification Channels**:
    1. Create a new notification module in the `notifications/` directory (e.g., `notifications/slack.py`).
    2. Implement a function to send notifications via the new channel in the new module.
    3. Update `sendNotifications.py` to include the new notification channel.
    4. Add the new channel name to the `notificationChannels` configuration option in `config/config.yaml`.
* **Customizing Monitoring Logic**:
    - Modify `utils/monitorTopMovers.py` to adjust the price change detection logic or add new monitoring criteria.

## Dependencies

Project dependencies are listed in `requirements.txt`:

```
ccxt>=4.1.80
PyYAML>=6.0.1
expiringdict>=1.2.1
pytz>=2024.1
```

Install dependencies using pip:

```bash
pip install -r requirements.txt
```

## Running the Application

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure `config/config.yaml`**:
   - Set up your exchange, notification channels, API keys, and other settings in `config/config.yaml`.
3. **Run `main.py`**:
   ```bash
   python main.py
   ```

## Setting up Cron Job for Automated Monitoring

To run PriceSentry periodically, set up a cron job:

1. **Edit crontab**:
   ```bash
   crontab -e
   ```
2. **Add a cron job entry (e.g., every 5 minutes)**:
   ```
   */5 * * * * cd /path/to/PriceSentry && /usr/bin/python3 main.py >> logs.txt 2>&1
   ```
   - Replace `/path/to/PriceSentry` with the actual path to your PriceSentry project directory.
   - Adjust the cron schedule as needed.

---

This documentation provides a comprehensive overview of the PriceSentry project for developers. For any further questions or issues, please refer to the project repository or contact the maintainers.