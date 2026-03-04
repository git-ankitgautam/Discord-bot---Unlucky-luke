import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

DEFAULT_WELCOME_DM_TEMPLATE = "Welcome to {server}, {user_mention}! Please read the rules and have fun."
DEFAULT_JOIN_TEMPLATE = "{user_mention} has joined the server."


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ModerationStore:
    def __init__(self, db_path: str = "bot_data.sqlite3") -> None:
        self.db_path = Path(db_path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    entry_channel_id INTEGER NULL,
                    welcome_dm_enabled INTEGER NOT NULL DEFAULT 1,
                    welcome_dm_template TEXT NOT NULL,
                    join_template TEXT NOT NULL,
                    warn_threshold INTEGER NOT NULL DEFAULT 3,
                    timeout_minutes INTEGER NOT NULL DEFAULT 10,
                    warning_expiry_days INTEGER NOT NULL DEFAULT 7,
                    exemption_mode TEXT NOT NULL DEFAULT 'admins_mods',
                    exempt_role_id INTEGER NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS warning_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_warning_events_guild_user_created
                ON warning_events(guild_id, user_id, created_at)
                """
            )
            conn.commit()

    def ensure_guild_settings(self, guild_id: int) -> sqlite3.Row:
        now = utcnow_iso()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO guild_settings (
                    guild_id,
                    welcome_dm_template,
                    join_template,
                    updated_at
                ) VALUES (?, ?, ?, ?)
                """,
                (guild_id, DEFAULT_WELCOME_DM_TEMPLATE, DEFAULT_JOIN_TEMPLATE, now),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ).fetchone()
            if row is None:
                raise RuntimeError("Unable to load guild settings")
            return row

    def get_guild_settings(self, guild_id: int) -> sqlite3.Row:
        return self.ensure_guild_settings(guild_id)

    def update_guild_settings(self, guild_id: int, **fields) -> sqlite3.Row:
        if not fields:
            return self.ensure_guild_settings(guild_id)

        self.ensure_guild_settings(guild_id)

        columns = []
        values = []
        for key, value in fields.items():
            columns.append(f"{key} = ?")
            values.append(value)
        columns.append("updated_at = ?")
        values.append(utcnow_iso())
        values.append(guild_id)

        query = f"UPDATE guild_settings SET {', '.join(columns)} WHERE guild_id = ?"
        with self._connection() as conn:
            conn.execute(query, values)
            conn.commit()
            row = conn.execute(
                "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ).fetchone()
            if row is None:
                raise RuntimeError("Unable to load updated guild settings")
            return row

    def add_warning(
        self,
        guild_id: int,
        user_id: int,
        message_id: int,
        channel_id: int,
        reason: str,
        created_at: Optional[str] = None,
    ) -> None:
        timestamp = created_at or utcnow_iso()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO warning_events (
                    guild_id,
                    user_id,
                    message_id,
                    channel_id,
                    reason,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (guild_id, user_id, message_id, channel_id, reason, timestamp),
            )
            conn.commit()

    def count_active_warnings(
        self,
        guild_id: int,
        user_id: int,
        expiry_days: int,
        now: Optional[datetime] = None,
    ) -> int:
        ref = now or datetime.now(timezone.utc)
        cutoff = (ref - timedelta(days=expiry_days)).isoformat()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS warning_count
                FROM warning_events
                WHERE guild_id = ? AND user_id = ? AND created_at >= ?
                """,
                (guild_id, user_id, cutoff),
            ).fetchone()
            return int(row["warning_count"]) if row else 0

    def latest_warning_time(self, guild_id: int, user_id: int) -> Optional[str]:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT created_at
                FROM warning_events
                WHERE guild_id = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (guild_id, user_id),
            ).fetchone()
            if row is None:
                return None
            return str(row["created_at"])

    def clear_warnings(self, guild_id: int, user_id: int) -> int:
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM warning_events WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )
            conn.commit()
            return int(cursor.rowcount)


def render_member_template(template: str, user_mention: str, user_name: str, server_name: str) -> str:
    return template.format(
        user_mention=user_mention,
        user_name=user_name,
        server=server_name,
    )
