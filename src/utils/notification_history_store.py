"""Persistent storage for notification delivery history."""

from __future__ import annotations

import base64
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


DEFAULT_DB_PATH = Path("data/notification_history.db")


@dataclass(frozen=True)
class NotificationDelivery:
    id: int
    event_id: int
    target: str
    target_display: Optional[str]
    status: str
    detail: Optional[str]


@dataclass(frozen=True)
class NotificationEvent:
    id: int
    channel: str
    message: Optional[str]
    image_caption: Optional[str]
    created_at: float
    image_available: bool
    deliveries: List[NotificationDelivery]


class NotificationHistoryStore:
    """SQLite-backed storage for notification events and deliveries."""

    _SCHEMA_EVENTS = """
    CREATE TABLE IF NOT EXISTS notification_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT NOT NULL,
        message TEXT,
        image_base64 TEXT,
        image_caption TEXT,
        created_at REAL NOT NULL
    );
    """

    _SCHEMA_DELIVERIES = """
    CREATE TABLE IF NOT EXISTS notification_deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        target TEXT NOT NULL,
        target_display TEXT,
        status TEXT NOT NULL,
        detail TEXT,
        created_at REAL NOT NULL,
        FOREIGN KEY(event_id) REFERENCES notification_events(id) ON DELETE CASCADE
    );
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._ensure_schema()

    def record_event(
        self,
        channel: str,
        message: Optional[str],
        image_bytes: Optional[bytes],
        image_caption: Optional[str],
    ) -> int:
        image_base64: Optional[str] = None
        if image_bytes is not None:
            image_base64 = base64.b64encode(image_bytes).decode("ascii")

        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notification_events (channel, message, image_base64, image_caption, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (channel, message, image_base64, image_caption, time.time()),
            )
            event_id = int(cursor.lastrowid)
            conn.execute(
                "DELETE FROM notification_events WHERE id != ?",
                (event_id,),
            )
            conn.commit()
        return event_id

    def record_delivery(
        self,
        event_id: int,
        target: str,
        target_display: Optional[str],
        status: str,
        detail: Optional[str] = None,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO notification_deliveries (event_id, target, target_display, status, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, target, target_display, status, detail, time.time()),
            )
            conn.commit()

    def list_events(self, limit: int = 50) -> List[NotificationEvent]:
        with self._connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, channel, message, image_base64, image_caption, created_at
                FROM notification_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

            events: List[NotificationEvent] = []
            for row in rows:
                event_id = int(row["id"])
                deliveries_cursor = conn.execute(
                    """
                    SELECT id, target, target_display, status, detail
                    FROM notification_deliveries
                    WHERE event_id = ?
                    ORDER BY created_at ASC
                    """,
                    (event_id,),
                )
                deliveries = [
                    NotificationDelivery(
                        id=int(d_row["id"]),
                        event_id=event_id,
                        target=str(d_row["target"]),
                        target_display=(
                            str(d_row["target_display"]) if d_row["target_display"] is not None else None
                        ),
                        status=str(d_row["status"]),
                        detail=(str(d_row["detail"]) if d_row["detail"] is not None else None),
                    )
                    for d_row in deliveries_cursor.fetchall()
                ]

                events.append(
                    NotificationEvent(
                        id=event_id,
                        channel=str(row["channel"]),
                        message=str(row["message"]) if row["message"] is not None else None,
                        image_caption=(
                            str(row["image_caption"]) if row["image_caption"] is not None else None
                        ),
                        created_at=float(row["created_at"]),
                        image_available=row["image_base64"] is not None,
                        deliveries=deliveries,
                    )
                )

            return events

    def get_event_image(self, event_id: int) -> Optional[tuple[str, Optional[str]]]:
        with self._connection() as conn:
            cursor = conn.execute(
                """
                SELECT image_base64, image_caption
                FROM notification_events
                WHERE id = ?
                """,
                (event_id,),
            )
            row = cursor.fetchone()
            if not row or row["image_base64"] is None:
                return None
            return str(row["image_base64"]), (
                str(row["image_caption"]) if row["image_caption"] is not None else None
            )

    def _ensure_schema(self) -> None:
        if not self._db_path.parent.exists():
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(self._SCHEMA_EVENTS)
            conn.execute(self._SCHEMA_DELIVERIES)
            conn.commit()

    def _connection(self) -> sqlite3.Connection:
        self._lock.acquire()
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return _ConnectionWrapper(conn, self._lock)


class _ConnectionWrapper:
    def __init__(self, conn: sqlite3.Connection, lock: threading.RLock) -> None:
        self._conn = conn
        self._lock = lock

    def __getattr__(self, item):  # pragma: no cover - passthrough
        return getattr(self._conn, item)

    def __enter__(self):
        self._conn.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            return self._conn.__exit__(exc_type, exc, tb)
        finally:
            if self._lock._is_owned():  # type: ignore[attr-defined]
                self._lock.release()
