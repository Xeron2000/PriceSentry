import logging
from typing import List, Optional

from notifications.telegram import send_telegram_message, send_telegram_photo
from utils.notification_history_store import NotificationHistoryStore
from utils.telegram_recipient_store import TelegramRecipientStore


_recipient_store = TelegramRecipientStore()
_history_store = NotificationHistoryStore()


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


def _resolve_display_name(chat_id: str) -> Optional[str]:
    try:
        candidate_id = int(chat_id)
    except (TypeError, ValueError):
        return None

    recipient = _recipient_store.get_by_user_id(candidate_id)
    if recipient and recipient.username:
        return f"@{recipient.username}"
    return None


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

                event_id = _history_store.record_event(
                    "telegram",
                    message if message else None,
                    image_bytes,
                    image_caption,
                )

                fallback_chat_id = telegram_config.get("chatId")

                for chat_id in chat_ids:
                    display_name = _resolve_display_name(chat_id)
                    if display_name is None and fallback_chat_id and str(fallback_chat_id) == chat_id:
                        display_name = f"配置 chatId ({chat_id})"

                    status = "success"
                    detail = None

                    try:
                        if image_bytes is not None:
                            success = send_telegram_photo(
                                image_caption or "",
                                token,
                                chat_id,
                                image_bytes,
                            )
                        else:
                            success = send_telegram_message(
                                message,
                                token,
                                chat_id,
                            )
                        if not success:
                            status = "failed"
                            if detail is None:
                                detail = "API 返回失败"
                    except Exception as exc:  # pragma: no cover - defensive guard
                        logging.error("Failed to send Telegram notification to %s: %s", chat_id, exc)
                        status = "failed"
                        detail = str(exc)
                    finally:
                        _history_store.record_delivery(
                            event_id,
                            chat_id,
                            display_name,
                            status,
                            detail,
                        )
            else:
                logging.warning(f"Unsupported notification channel: {channel}")
        except Exception as exc:
            logging.error(f"Failed to send message via {channel}: {exc}")
