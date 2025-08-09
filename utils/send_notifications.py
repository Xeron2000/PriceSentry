import logging

from notifications.dingding import send_dingding_message
from notifications.telegram import send_telegram_message


def send_notifications(message, notificationChannels, telegram_config, dingding_config):
    """
    Send a message to each of the specified notification channels.

    Args:
        message (str): The message to be sent
        notificationChannels (list[str]): The list of channels to send to
        telegram_config (dict): The configuration of the Telegram bot (token, chatId)
        dingding_config (dict): The configuration of the DingDing robot (webhook,
            secret)

    Returns:
        None
    """
    for channel in notificationChannels:
        try:
            if channel == "telegram":
                send_telegram_message(
                    message, telegram_config["token"], telegram_config["chatId"]
                )
            elif channel == "dingding":
                send_dingding_message(
                    message, dingding_config["webhook"], dingding_config["secret"]
                )
            else:
                logging.warning(f"Unsupported notification channel: {channel}")
        except Exception as e:
            logging.error(f"Failed to send message via {channel}: {e}")
