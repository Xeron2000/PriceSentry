import logging
from typing import List

from notifications.telegram import send_telegram_message, send_telegram_photo


def _resolve_telegram_targets(telegram_config: dict) -> List[str]:
    """Resolve Telegram recipients from config."""
    chat_ids: List[str] = []

    chat_id = telegram_config.get("chatId")
    if chat_id:
        chat_ids.append(str(chat_id))

    return chat_ids


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
                token = telegram_config.get("token")
                if not token:
                    logging.warning("Telegram notifications enabled but token missing")
                    continue

                chat_ids = _resolve_telegram_targets(telegram_config)
                if not chat_ids:
                    logging.warning("Telegram notifications enabled but no chatId configured")
                    continue

                for chat_id in chat_ids:
                    try:
                        if image_bytes is not None:
                            send_telegram_photo(
                                image_caption or "",
                                token,
                                chat_id,
                                image_bytes,
                            )
                        else:
                            send_telegram_message(
                                message,
                                token,
                                chat_id,
                            )
                    except Exception as exc:
                        logging.error(
                            "Failed to send Telegram notification to %s: %s",
                            chat_id,
                            exc,
                        )
            else:
                logging.warning(f"Unsupported notification channel: {channel}")
        except Exception as exc:
            logging.error(f"Failed to send message via {channel}: {exc}")
