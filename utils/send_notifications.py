import logging

from notifications.dingding import send_dingding_message
from notifications.telegram import send_telegram_message, send_telegram_photo


def send_notifications(
    message,
    notificationChannels,
    telegram_config,
    dingding_config,
    image_bytes=None,
    image_caption=None,
    dingding_image_url=None,
):
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
                if image_bytes is not None:
                    # Prefer sending photo if available
                    sent = send_telegram_photo(
                        image_caption or message,
                        telegram_config["token"],
                        telegram_config["chatId"],
                        image_bytes,
                    )
                    if not sent:
                        # Fallback to text message
                        send_telegram_message(
                            message,
                            telegram_config["token"],
                            telegram_config["chatId"],
                        )
                else:
                    send_telegram_message(
                        message, telegram_config["token"], telegram_config["chatId"]
                    )
            elif channel == "dingding":
                # Append image URL if provided (DingDing text message)
                final_message = (
                    f"{message}\nChart: {dingding_image_url}"
                    if dingding_image_url
                    else message
                )
                send_dingding_message(
                    final_message,
                    dingding_config.get("webhook"),
                    dingding_config.get("secret"),
                )
            else:
                logging.warning(f"Unsupported notification channel: {channel}")
        except Exception as e:
            logging.error(f"Failed to send message via {channel}: {e}")
