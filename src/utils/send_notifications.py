import logging
from typing import List

from notifications.telegram import send_telegram_message, send_telegram_photo
from utils.telegram_recipient_store import TelegramRecipientStore


_recipient_store = TelegramRecipientStore()


def _resolve_telegram_targets(telegram_config: dict) -> List[str]:
    chat_ids: List[str] = []

    fallback = telegram_config.get("chatId")
    if fallback:
        chat_ids.append(str(fallback))

    recipients = _recipient_store.list_active()
    for recipient in recipients:
        if recipient.user_id is None:
            continue
        candidate = str(recipient.user_id)
        if candidate not in chat_ids:
            chat_ids.append(candidate)

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
                    logging.warning("Telegram notifications enabled but no recipients bound")
                    continue

                if image_bytes is not None:
                    for chat_id in chat_ids:
                        _ = send_telegram_photo(
                            image_caption or "",
                            token,
                            chat_id,
                            image_bytes,
                        )
                else:
                    for chat_id in chat_ids:
                        _ = send_telegram_message(
                            message,
                            token,
                            chat_id,
                        )
            else:
                logging.warning(f"Unsupported notification channel: {channel}")
        except Exception as exc:
            logging.error(f"Failed to send message via {channel}: {exc}")
