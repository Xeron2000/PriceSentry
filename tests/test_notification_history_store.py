from pathlib import Path

from utils.notification_history_store import NotificationHistoryStore


def test_history_store_keeps_only_latest(tmp_path: Path) -> None:
    store = NotificationHistoryStore(tmp_path / "history.db")

    first_id = store.record_event("telegram", "hello", None, None)
    store.record_delivery(first_id, "1001", "@alice", "success", None)

    second_id = store.record_event("telegram", "world", None, None)

    events = store.list_events()
    assert len(events) == 1
    event = events[0]
    assert event.id == second_id
    assert event.message == "world"

    # ensure first event removed
    assert store.get_event_image(second_id) is None
