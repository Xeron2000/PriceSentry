from pathlib import Path
from typing import List, Tuple

import pytest

from utils.telegram_recipient_store import TelegramRecipientStore


class DummyHistoryStore:
    def __init__(self) -> None:
        self.events = []

    def record_event(self, channel, message, image_bytes, image_caption):
        event_id = len(self.events) + 1
        self.events.append(
            {
                "id": event_id,
                "channel": channel,
                "message": message,
                "image_bytes": image_bytes,
                "image_caption": image_caption,
                "deliveries": [],
            }
        )
        return event_id

    def record_delivery(self, event_id, target, target_display, status, detail):
        self.events[event_id - 1]["deliveries"].append(
            {
                "target": target,
                "target_display": target_display,
                "status": status,
                "detail": detail,
            }
        )


@pytest.fixture()
def recipient_store(tmp_path: Path) -> TelegramRecipientStore:
    return TelegramRecipientStore(tmp_path / "recipients.db")


def test_send_notifications_to_active_recipients(monkeypatch, recipient_store):
    import utils.send_notifications as sns

    token = recipient_store.add_pending("alice")
    recipient_store.confirm_binding(token, 1001, "alice")

    monkeypatch.setattr(sns, "_recipient_store", recipient_store, raising=False)
    history = DummyHistoryStore()
    monkeypatch.setattr(sns, "_history_store", history, raising=False)

    sent: List[Tuple[str, str]] = []

    def fake_send_message(message, token, chat_id):
        sent.append(("msg", chat_id, message))
        return True

    monkeypatch.setattr(sns, "send_telegram_message", fake_send_message)

    sns.send_notifications(
        "Hello",
        ["telegram"],
        {"token": "dummy-token"},
    )

    assert sent == [("msg", "1001", "Hello")]
    assert len(history.events) == 1
    event = history.events[0]
    assert event["channel"] == "telegram"
    assert event["message"] == "Hello"
    assert event["image_bytes"] is None
    assert event["deliveries"] == [
        {
            "target": "1001",
            "target_display": "@alice",
            "status": "success",
            "detail": None,
        }
    ]


def test_send_notifications_fallback_chat_id(monkeypatch, tmp_path):
    import utils.send_notifications as sns

    monkeypatch.setattr(
        sns,
        "_recipient_store",
        TelegramRecipientStore(tmp_path / "fallback.db"),
        raising=False,
    )
    history = DummyHistoryStore()
    monkeypatch.setattr(sns, "_history_store", history, raising=False)

    sent: List[Tuple[str, str]] = []

    def fake_send_message(message, token, chat_id):
        sent.append(("msg", chat_id, message))
        return True

    monkeypatch.setattr(sns, "send_telegram_message", fake_send_message)

    sns.send_notifications(
        "Hello",
        ["telegram"],
        {"token": "dummy-token", "chatId": "fallback"},
    )

    assert sent == [("msg", "fallback", "Hello")]
    assert len(history.events) == 1
    delivery = history.events[0]["deliveries"][0]
    assert delivery["target"] == "fallback"
    assert delivery["target_display"] == "配置 chatId (fallback)"
    assert delivery["status"] == "success"


def test_send_notifications_photo(monkeypatch, recipient_store):
    import utils.send_notifications as sns

    token = recipient_store.add_pending("bob")
    recipient_store.confirm_binding(token, 2002, "bob")
    monkeypatch.setattr(sns, "_recipient_store", recipient_store, raising=False)
    history = DummyHistoryStore()
    monkeypatch.setattr(sns, "_history_store", history, raising=False)

    photos: List[Tuple[str, bytes]] = []

    def fake_send_photo(caption, token, chat_id, image_bytes):
        photos.append((chat_id, image_bytes))
        return True

    monkeypatch.setattr(sns, "send_telegram_photo", fake_send_photo)

    sns.send_notifications(
        "Hello",
        ["telegram"],
        {"token": "dummy-token"},
        image_bytes=b"bytes",
        image_caption="caption",
    )

    assert photos == [("2002", b"bytes")]
    event = history.events[0]
    assert event["image_bytes"] == b"bytes"
    assert event["image_caption"] == "caption"
    assert event["deliveries"][0]["target_display"] == "@bob"
