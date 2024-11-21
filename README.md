## Project Overview

TradePulse is an open-source tool designed to monitor the price movements of cryptocurrency trading pairs and send alerts when significant price changes occur. Users can choose to monitor the top gainers and losers in the market or specify custom trading pairs to track. The tool allows users to set the monitoring frequency and define the minimum percentage change required to trigger an alert. With its high extensibility, it will support additional exchanges and notification channels in the future, making it suitable for a variety of trader needs. Contributions to the code are welcome, and we encourage participation in the development and improvement of the project.

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

### Configuration Fields and Descriptions

1. **telegramToken**  
   The token used to connect to the Telegram bot.  
   Example: `"telegramToken": "your_telegram_bot_token"`

2. **chatId**  
   The Telegram chat ID where notifications will be sent.  
   Example: `"chatId": "your_chat_id"`

3. **defaultTimeframe**  
   The default timeframe (frequency of data retrieval).  
   Example: `"defaultTimeframe": "5m"`  
   Possible values: `"1m"`, `"5m"`, `"15m"`, `"1h"`, `"1d"`

4. **defaultStart**  
   The default starting position of the price change ranking range.  
   Example: `"defaultStart": 1`

5. **defaultEnd**  
   The default ending position of the price change ranking range.  
   Example: `"defaultEnd": 10`

6. **defaultThreshold**  
   The default price change threshold, only pairs that exceed this value will be notified.  
   Example: `"defaultThreshold": 1`

7. **exchange**  
   The name of the exchange to connect to.  
   Example: `"exchange": "binance"`

8. **notificationChannels**  
   The channels for receiving notifications, currently only supports Telegram.  
   Example: `"notificationChannels": ["telegram"]`

9. **symbolsFilePath**  
   The file path that contains the trading pair symbols. If empty, pairs will be automatically retrieved based on the `defaultStart` and `defaultEnd` ranking range, defaulting to the top 10 pairs by price change.  
   Example: `"symbolsFilePath": "config/symbols.txt"`

### Example Configuration File

```json
{
  "telegramToken": "your_telegram_bot_token",
  "chatId": "your_chat_id",
  "defaultTimeframe": "5m",
  "defaultStart": 1,
  "defaultEnd": 10,
  "defaultThreshold": 1,
  "exchange": "binance", 
  "notificationChannels": ["telegram"], 
  "symbolsFilePath": "config/symbols.txt"
}
```

## Setting Up Scheduled Script Execution

You can use `cron` to set up a scheduled task to run the monitoring script regularly.

### Edit `cron` Tasks

Open the `crontab` file:

```bash
crontab -e
```

At the end of the file, add the following line to run the script every 15 minutes:

```bash
*/5 * * * * /usr/bin/python3 /path/to/yourproject/main.py >> /path/to/yourproject/log.txt 2>&1
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
