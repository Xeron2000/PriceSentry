import logging

from notifications.dingding import send_dingding_message, send_dingding_photo
from notifications.telegram import send_telegram_photo


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
                # Only send a single photo. No text messages for Telegram.
                if image_bytes is not None:
                    _ = send_telegram_photo(
                        image_caption or "",
                        telegram_config["token"],
                        telegram_config["chatId"],
                        image_bytes,
                    )
                # If no image is provided, do not send Telegram text (as requested)
            elif channel == "dingding":
                # Send photo if image_bytes and image_url are provided
                if image_bytes is not None and dingding_image_url is not None:
                    # Send photo with caption using markdown format
                    _ = send_dingding_photo(
                        image_caption or "",
                        dingding_config.get("webhook"),
                        dingding_config.get("secret"),
                        image_bytes,
                        dingding_image_url,
                    )
                else:
                    # Send text message with image URL if provided
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
