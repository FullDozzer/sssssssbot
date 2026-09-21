import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id     INTEGER PRIMARY KEY,
    banned INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS links (
    admin_msg_id INTEGER PRIMARY KEY,
    user_id      INTEGER NOT NULL,
    user_msg_id  INTEGER NOT NULL
);
"""


class Database:
    """SQLite storage: banned users and message links (admin chat -> user chat)."""

    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    # --- users ---

    def add_user(self, user_id: int) -> None:
        self._conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))

    def is_banned(self, user_id: int) -> bool:
        row = self._conn.execute(
            "SELECT banned FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return bool(row and row[0])

    def set_banned(self, user_id: int, banned: bool) -> None:
        self._conn.execute(
            "INSERT INTO users (id, banned) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET banned = excluded.banned",
            (user_id, int(banned)),
        )

    # --- links ---

    def link(self, admin_msg_id: int, user_id: int, user_msg_id: int) -> None:
        """Remember which user (and which of their messages) an admin-chat message belongs to."""
        self._conn.execute(
            "INSERT OR REPLACE INTO links (admin_msg_id, user_id, user_msg_id) VALUES (?, ?, ?)",
            (admin_msg_id, user_id, user_msg_id),
        )

    def lookup(self, admin_msg_id: int) -> tuple[int, int] | None:
        row = self._conn.execute(
            "SELECT user_id, user_msg_id FROM links WHERE admin_msg_id = ?",
            (admin_msg_id,),
        ).fetchone()
        return (row[0], row[1]) if row else None
