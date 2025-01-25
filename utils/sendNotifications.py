import logging
from notifications.telegram import sendTelegramMessage
from notifications.dingding import sendDingDingMessage

def sendNotifications(message, notificationChannels, telegram_config, dingding_config):
    """
    Send a message to each of the specified notification channels.

    Args:
        message (str): The message to be sent
        notificationChannels (list[str]): The list of channels to send to
        telegram_config (dict): The configuration of the Telegram bot (token, chatId)
        dingding_config (dict): The configuration of the DingDing robot (webhook, secret)

    Returns:
        None
    """
    for channel in notificationChannels:
        try:
            if channel == 'telegram':
                sendTelegramMessage(
                    message, telegram_config['token'], telegram_config['chatId']
                )
            elif channel == 'dingding':
                sendDingDingMessage(
                    message, dingding_config['webhook'], dingding_config['secret']
                )
            else:
                logging.warning(f"Unsupported notification channel: {channel}")
        except Exception as e:
            logging.error(f"Failed to send message via {channel}: {e}")
