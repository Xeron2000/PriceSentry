## PriceSentry

### Project Overview

PriceSentry is an open-source tool designed to monitor the price movements of cryptocurrency trading pairs and send alerts when significant price changes occur. Users can choose to monitor the top gainers and losers in the market or specify custom trading pairs to track. The tool allows users to set the monitoring frequency and define the minimum percentage change required to trigger an alert. With its high extensibility, it will support additional exchanges and notification channels in the future, making it suitable for a variety of trader needs. Contributions to the code are welcome, and we encourage participation in the development and improvement of the project.

### Table of Contents

1. [Project Overview](#project-overview)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
   - [Install Python and pip](#install-python-and-pip)
   - [Clone the Project Code](#clone-the-project-code)
   - [Install Required Libraries](#install-required-libraries)
4. [Setting Up the Telegram Bot](#setting-up-the-telegram-bot)
   - [Create a Telegram Bot](#create-a-telegram-bot)
   - [Get Chat ID](#get-chat-id)
5. [Setting Up the DingDing Robot](#setting-up-the-dingding-robot)
   - [Create a Group and Add the Robot](#create-a-group-and-add-the-robot)
   - [Get the Webhook URL](#get-the-webhook-url)
   - [Enable Signature](#enable-signature)
6. [Example Configuration File](#example-configuration-file)
7. [Setting Up Scheduled Script Execution](#setting-up-scheduled-script-execution)
8. [Frequently Asked Questions](#frequently-asked-questions)
9. [License](#license)

### System Requirements

- Python 3.6 or higher
- pip

### Installation Steps

#### Install Python and pip

Open the terminal and run the following commands:

```bash
sudo apt update
sudo apt install python3 python3-pip
```

#### Clone the Project Code

Use Git to clone the project code:

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
```

#### Install Required Libraries

Use pip to install the necessary Python libraries:

```bash
pip install -r requirements.txt
```

### Setting Up the Telegram Bot

#### Create a Telegram Bot

1. Open the Telegram app.
2. Search for `@BotFather` and send the `/start` command.
3. Send the `/newbot` command and follow the prompts to set up your bot's name and username.
4. Once created, you will receive an access token (TOKEN) for your bot.

#### Get Chat ID

1. Send a message to your newly created bot.
2. In your browser, visit the following URL, replacing `<TELEGRAM_TOKEN>` with your bot's token:

```
https://api.telegram.org/bot<TELEGRAM_TOKEN>/getUpdates
```

3. Locate the message you sent and record the `chat_id`.

### Setting Up the DingDing Robot

#### Create a Group and Add the Robot

1. Create or select a group in DingDing.
2. Click Group Settings > Group Robot > Add Robot > Custom Robot.
3. Set the robot's name and choose the desired security settings.

#### Get the Webhook URL

- After adding the robot, retrieve the Webhook URL, e.g.:
  ```
  https://oapi.dingtalk.com/robot/send?access_token=your_access_token
  ```

#### Enable Signature

- Enable signature verification in the security settings and note down the generated **secret** key.

### Example Configuration File

```yaml
# Configuration for the exchange and default behavior
# The name of the exchange to connect to.
exchange: "binance"  # Example: "binance"

# The default timeframe (frequency of data retrieval).
# Possible values: "1m", "5m", "15m", "1h", "1d".
defaultTimeframe: "5m"  # Example: "5m"

# The default starting position of the price change ranking range.
defaultStart: 1  # Example: 1

# The default ending position of the price change ranking range.
defaultEnd: 10  # Example: 10

# The default price change threshold. Only pairs exceeding this value will be notified.
defaultThreshold: 1  # Example: 1

# The file path containing trading pair symbols. If empty, pairs will be auto-retrieved.
symbolsFilePath: "config/symbols.txt"  # Example: "config/symbols.txt"

# Notification channels and configuration
# The channels for receiving notifications. Currently supports Telegram and DingDing.
notificationChannels: 
  - "telegram"
  - "dingding"

# Telegram bot configuration
# The token used to connect to the Telegram bot.
telegram:
  token: ""  # Example: "your_telegram_bot_token"
  
  # The Telegram chat ID where notifications will be sent.
  chatId: ""  # Example: "your_chat_id"

# DingDing robot configuration
# The DingDing robot webhook URL for sending notifications.
dingding:
  webhook: ""  # Example: "https://oapi.dingtalk.com/robot/send?access_token=your_access_token"
  
  # The DingDing robot secret used to generate the signature for secure notifications.
  secret: ""  # Example: "your_sign_secret"

```

### Setting Up Scheduled Script Execution

You can use `cron` to set up a scheduled task to run the monitoring script regularly.

#### Edit `cron` Tasks

Open the `crontab` file:

```bash
crontab -e
```

At the end of the file, add the following line to run the script every 5 minutes:

```bash
*/5 * * * * /usr/bin/python3 /path/to/yourproject/main.py >> /path/to/yourproject/log.txt 2>&1
```

- Ensure you replace `/path/to/yourproject/main.py` with the actual path to your script.
- The log will be output to the `log.txt` file, which you can check for information about the execution status.

### Frequently Asked Questions

#### Unable to Send Messages

Ensure that you have correctly set the Telegram Bot token and chat ID, and that the bot has sent a message to your chat.

#### Failed to Retrieve Price Data

Check your network connection and ensure that the Binance API is available.

### License

MIT License. Please refer to the [LICENSE](LICENSE) file for more information.