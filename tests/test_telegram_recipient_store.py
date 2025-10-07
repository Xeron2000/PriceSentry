import sqlite3
from pathlib import Path

import pytest

from utils.telegram_recipient_store import TelegramRecipientStore


@pytest.fixture()
def store(tmp_path: Path) -> TelegramRecipientStore:
    db_path = tmp_path / "recipients.db"
    return TelegramRecipientStore(db_path)


def test_add_pending_creates_token_and_persists(store: TelegramRecipientStore) -> None:
    token = store.add_pending("alice")
    assert isinstance(token, str) and len(token) > 10

    recipients = store.list_all()
    assert len(recipients) == 1
    recipient = recipients[0]
    assert recipient.username == "alice"
    assert recipient.status == "pending"
    assert recipient.token == token
    assert recipient.user_id is None


def test_confirm_binding_updates_status(store: TelegramRecipientStore) -> None:
    token = store.add_pending("bob")
    assert store.confirm_binding(token, 12345, "bob") == "confirmed"

    active = store.list_active()
    assert len(active) == 1
    recipient = active[0]
    assert recipient.username == "bob"
    assert recipient.user_id == 12345
    assert recipient.status == "active"


def test_confirm_binding_invalid_token_returns_false(store: TelegramRecipientStore) -> None:
    assert store.confirm_binding("missing", 1) == "not_found"


def test_delete_recipient(store: TelegramRecipientStore) -> None:
    token = store.add_pending("charlie")
    store.confirm_binding(token, 11111)

    recipient_id = store.list_all()[0].id
    assert store.delete(recipient_id) is True
    assert store.list_all() == []


def test_confirm_binding_twice_reports_already_active(store: TelegramRecipientStore) -> None:
    token = store.add_pending("diana")
    store.confirm_binding(token, 999)
    assert store.confirm_binding(token, 999) == "already_active"


def test_get_by_user_id_returns_recipient(store: TelegramRecipientStore) -> None:
    token = store.add_pending("eric")
    store.confirm_binding(token, 4242, "eric")

    recipient = store.get_by_user_id(4242)
    assert recipient is not None
    assert recipient.username == "eric"

    assert store.get_by_user_id(9999) is None


def test_store_rejects_empty_username(store: TelegramRecipientStore) -> None:
    with pytest.raises(ValueError):
        store.add_pending("   ")


def test_database_schema_reused(store: TelegramRecipientStore) -> None:
    # Ensure schema creation is idempotent & handled gracefully
    TelegramRecipientStore(store._db_path)
    with sqlite3.connect(store._db_path) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='telegram_recipients'"
        )
        assert cursor.fetchone() is not None
