## Project Overview

TradePulse monitors cryptocurrency trading pairs on Binance, tracks price movements over a specified time period, and sends alerts for significant price changes directly to a Telegram chat. It allows you to either monitor the top gainers and losers from Binance's market or specify custom trading pairs to monitor. You can define the monitoring frequency and the minimum percentage change required to trigger an alert, making it a flexible solution for active traders.

## System Requirements

- Python 3.6 or higher
- pip (Python package manager)

## Installation Steps

### Install Python and pip

Open the terminal and run the following commands:

```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Clone the Project Code

Use Git to clone the project code:

```bash
git clone https://github.com/Xeron2000/TradePulse.git
cd TradePulse
```

### Install Required Libraries

Use pip to install the necessary Python libraries:

```bash
pip install -r requirements.txt
```

## Setting Up the Telegram Bot

### Create a Telegram Bot

1. Open the Telegram app.
2. Search for `@BotFather` and send the `/start` command.
3. Send the `/newbot` command and follow the prompts to set up your bot's name and username.
4. Once created, you will receive an access token (TOKEN) for your bot.

### Get Chat ID

1. Send a message to your newly created bot.
2. In your browser, visit the following URL, replacing `<TELEGRAM_TOKEN>` with your bot's token:

```
https://api.telegram.org/bot<TELEGRAM_TOKEN>/getUpdates
```

3. Locate the message you sent and record the `chat_id`.

## Setting Up the .env File

Create a .env file in the root directory of the project.
Add the following lines to the .env file:

```bash
TELEGRAM_TOKEN='your_telegram_bot_token'
CHAT_ID='your_chat_id'
```

## Using the Script

### Running the Script

You can run the script from the command line, specifying the time range and optionally the path to a file containing the trading pair symbols. If no symbols file is provided, the script will monitor the top gainers and losers.

#### Monitor Top Gainers and Losers (Default Behavior)

If you want to monitor the top 10 gainers and losers over a specified time frame, use the following command:

```bash
python3 main.py --timeframe 15m --start 0 --end 10 --threshold 2.0
```

- The `--timeframe` parameter specifies the time range in the format `Xm` (minutes), `Xh` (hours), or `Xd` (days).
- The `--start` and `--end` parameters specify the rank range for gainers and losers (default: 0 to 10).
- The `--threshold` parameter specifies the minimum percentage change to display (default: 2%).

#### Monitor Custom Symbols

If you want to monitor specific symbols from a file, use the --symbols parameter, which points to a file with one symbol per line:

```bash
python3 main.py --timeframe 1h --symbols /path/to/custom_symbols.txt --threshold 5.0
```

- The --symbols parameter specifies the file path containing trading pair symbols, with one symbol per line.

## Setting Up Scheduled Script Execution

You can use `cron` to set up a scheduled task to run the monitoring script regularly.

### Edit `cron` Tasks

Open the `crontab` file:

```bash
crontab -e
```

At the end of the file, add the following line to run the script every 15 minutes:

```bash
*/15 * * * * /usr/bin/python3 /path/to/yourproject/main.py >> /path/to/yourproject/log.txt 2>&1
```

- Ensure you replace `/path/to/yourproject/main.py` with the actual path to your script.
- The log will be output to the `log.txt` file, which you can check for information about the execution status.

## Frequently Asked Questions

### Unable to Send Messages

Ensure that you have correctly set the Telegram Bot token and chat ID, and that the bot has sent a message to your chat.

### Failed to Retrieve Price Data

Check your network connection and ensure that the Binance API is available.

## License

MIT License. Please refer to the [LICENSE](LICENSE) file for more information.
