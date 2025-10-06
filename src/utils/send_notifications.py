import logging

from notifications.telegram import send_telegram_photo


def send_notifications(
    message,
    notification_channels,
    telegram_config,
    image_bytes=None,
    image_caption=None,
):
    """Send notifications to configured channels."""
    for channel in notification_channels:
        try:
            if channel == "telegram":
                if image_bytes is not None:
                    _ = send_telegram_photo(
                        image_caption or "",
                        telegram_config["token"],
                        telegram_config["chatId"],
                        image_bytes,
                    )
            else:
                logging.warning(f"Unsupported notification channel: {channel}")
        except Exception as exc:
            logging.error(f"Failed to send message via {channel}: {exc}")
