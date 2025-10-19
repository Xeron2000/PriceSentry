"""Persistent storage helpers for Telegram notification recipients."""

from __future__ import annotations

import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional


DEFAULT_DB_PATH = Path("data/telegram_recipients.db")


@dataclass(frozen=True)
class TelegramRecipient:
    """Represents a Telegram recipient binding status."""

    id: int
    username: str
    token: str
    user_id: Optional[int]
    status: str
    created_at: float
    updated_at: float


class TelegramRecipientStore:
    """Lightweight SQLite-backed store for Telegram recipients."""

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS telegram_recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        token TEXT NOT NULL UNIQUE,
        user_id INTEGER,
        status TEXT NOT NULL,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );
    """

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Public API

    def add_pending(self, username: str) -> str:
        """Insert a pending recipient and return its bind token."""

        username = username.strip().lower()
        if not username:
            raise ValueError("username must not be empty")

        token = self._generate_token()
        now = time.time()

        with self._locked_connection() as conn:
            conn.execute(
                """
                INSERT INTO telegram_recipients (username, token, status, created_at, updated_at)
                VALUES (?, ?, 'pending', ?, ?)
                """,
                (username, token, now, now),
            )
            conn.commit()

        return token

    def confirm_binding(
        self, token: str, user_id: int, username: Optional[str] = None
    ) -> str:
        """Confirm binding for a pending recipient.

        Returns:
            str: One of "not_found", "already_active", or "confirmed".
        """

        if not token:
            raise ValueError("token must not be empty")

        now = time.time()
        with self._locked_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, username, status FROM telegram_recipients WHERE token = ?
                """,
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                return "not_found"

            recipient_id, stored_username, status = row
            if status == "active":
                return "already_active"

            # Telegram usernames are case-insensitive; store them in lowercase
            next_username = (username or stored_username).strip().lower()
            conn.execute(
                """
                UPDATE telegram_recipients
                SET username = ?, user_id = ?, status = 'active', updated_at = ?
                WHERE id = ?
                """,
                (next_username, int(user_id), now, recipient_id),
            )
            conn.commit()
            return "confirmed"

    def list_all(self) -> List[TelegramRecipient]:
        """Return all recipients sorted by creation time."""

        with self._locked_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, username, token, user_id, status, created_at, updated_at
                FROM telegram_recipients
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
        return [self._row_to_recipient(row) for row in rows]

    def list_active(self) -> List[TelegramRecipient]:
        """Return only active recipients."""

        with self._locked_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, username, token, user_id, status, created_at, updated_at
                FROM telegram_recipients
                WHERE status = 'active'
                ORDER BY created_at ASC
                """
            )
            rows = cursor.fetchall()
        return [self._row_to_recipient(row) for row in rows]

    def delete(self, recipient_id: int) -> bool:
        """Remove a recipient by id."""

        with self._locked_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM telegram_recipients WHERE id = ?",
                (recipient_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_by_user_id(self, user_id: int) -> Optional[TelegramRecipient]:
        with self._locked_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, username, token, user_id, status, created_at, updated_at
                FROM telegram_recipients
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_recipient(row)

    # ------------------------------------------------------------------
    # Internal helpers

    def _ensure_schema(self) -> None:
        if not self._db_path.parent.exists():
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._locked_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(self._SCHEMA)
            conn.commit()

    @contextmanager
    def _locked_connection(self) -> Iterator[sqlite3.Connection]:
        self._lock.acquire()
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            self._lock.release()

    @staticmethod
    def _row_to_recipient(row: sqlite3.Row) -> TelegramRecipient:
        return TelegramRecipient(
            id=int(row["id"]),
            username=str(row["username"]),
            token=str(row["token"]),
            user_id=int(row["user_id"]) if row["user_id"] is not None else None,
            status=str(row["status"]),
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )

    @staticmethod
    def _generate_token() -> str:
        return secrets.token_urlsafe(16)
