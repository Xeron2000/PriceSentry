from pathlib import Path
from typing import List, Tuple

import pytest

from utils.telegram_recipient_store import TelegramRecipientStore


@pytest.fixture()
def recipient_store(tmp_path: Path) -> TelegramRecipientStore:
    return TelegramRecipientStore(tmp_path / "recipients.db")


def test_send_notifications_to_active_recipients(monkeypatch, recipient_store):
    import utils.send_notifications as sns

    token = recipient_store.add_pending("alice")
    recipient_store.confirm_binding(token, 1001, "alice")

    monkeypatch.setattr(sns, "_recipient_store", recipient_store, raising=False)

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


def test_send_notifications_fallback_chat_id(monkeypatch, tmp_path):
    import utils.send_notifications as sns

    monkeypatch.setattr(
        sns,
        "_recipient_store",
        TelegramRecipientStore(tmp_path / "fallback.db"),
        raising=False,
    )

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


def test_send_notifications_photo(monkeypatch, recipient_store):
    import utils.send_notifications as sns

    token = recipient_store.add_pending("bob")
    recipient_store.confirm_binding(token, 2002, "bob")
    monkeypatch.setattr(sns, "_recipient_store", recipient_store, raising=False)

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
