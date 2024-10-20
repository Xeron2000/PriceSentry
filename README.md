## Project Overview

This script monitors trading pairs on Binance, retrieves those with significant price changes over a specified time period, and sends the results to a specified chat via a Telegram Bot.

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

Use Git to clone the project code (assuming the project code is hosted on GitHub):

```bash
git clone https://github.com/yourusername/yourproject.git
cd yourproject
```

### Install Required Libraries

Use pip to install the necessary Python libraries:

```bash
pip3 install requests
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

## Setting Environment Variables

For security reasons, it is recommended to store the Telegram Bot token and chat ID as environment variables. You can do this in the terminal using the following commands:

```bash
export TELEGRAM_TOKEN='your_telegram_bot_token'
export CHAT_ID='your_chat_id'
```

To make these environment variables effective every time you start the terminal, add them to the `~/.bashrc` file:

```bash
echo "export TELEGRAM_TOKEN='your_telegram_bot_token'" >> ~/.bashrc
echo "export CHAT_ID='your_chat_id'" >> ~/.bashrc
source ~/.bashrc
```

## Using the Script

### Running the Script

You can run the script from the command line, specifying the time range and the path to the file containing the trading pair symbols:

```bash
python3 binance_mover.py --timeframe 15m --symbols /path/to/symbols.txt
```

- The `--timeframe` parameter specifies the time range in the format `Xm` (minutes), `Xh` (hours), or `Xd` (days).
- The `--symbols` parameter specifies the file path containing trading pair symbols, with one symbol per line.

### Example

If you want to monitor the top 10 trading pairs with the highest gains and losses over the past 30 minutes, you can run the following command:

```bash
python3 binance_mover.py --timeframe 30m
```

## Setting Up Scheduled Script Execution

You can use `cron` to set up a scheduled task to run the monitoring script regularly.

### Edit `cron` Tasks

Open the `crontab` file:

```bash
crontab -e
```

At the end of the file, add the following line to run the script every hour:

```bash
0 * * * * /usr/bin/python3 /path/to/yourproject/binance_mover.py --timeframe 15m >> /path/to/yourproject/log.txt 2>&1
```

- Ensure you replace `/path/to/yourproject/binance_mover.py` with the actual path to your script.
- The log will be output to the `log.txt` file, which you can check for information about the execution status.

## Frequently Asked Questions

### Unable to Send Messages

Ensure that you have correctly set the Telegram Bot token and chat ID, and that the bot has sent a message to your chat.

### Failed to Retrieve Price Data

Check your network connection and ensure that the Binance API is available.

## License

MIT License. Please refer to the [LICENSE](LICENSE) file for more information.
