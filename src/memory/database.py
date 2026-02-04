from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiosqlite


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
  discord_id TEXT PRIMARY KEY,
  username TEXT,
  display_name TEXT,
  first_seen DATETIME,
  last_seen DATETIME,
  message_count INTEGER NOT NULL DEFAULT 0,
  voice_minutes REAL NOT NULL DEFAULT 0,
  relationship_score INTEGER NOT NULL DEFAULT 50,
  personality_notes TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  discord_id TEXT NOT NULL,
  channel_id TEXT,
  message_id TEXT,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (discord_id) REFERENCES users(discord_id)
);

CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  discord_id TEXT NOT NULL,
  memory_type TEXT NOT NULL,
  content TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.8,
  source_message_id TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_accessed DATETIME,
  access_count INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (discord_id) REFERENCES users(discord_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_unique
  ON memories(discord_id, memory_type, content);
"""


@dataclass(frozen=True)
class ConversationRow:
    role: str
    content: str


class Database:
    def __init__(self, *, path: Path):
        self._path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(str(self._path))
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA_SQL)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    def _require_conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Database not connected")
        return self._conn

    async def touch_user(self, *, discord_id: str, username: str, display_name: str) -> int:
        conn = self._require_conn()
        await conn.execute(
            """
            INSERT INTO users(discord_id, username, display_name, first_seen, last_seen, message_count)
            VALUES(?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(discord_id) DO UPDATE SET
              username=excluded.username,
              display_name=excluded.display_name,
              last_seen=CURRENT_TIMESTAMP,
              message_count=users.message_count + 1
            """,
            (discord_id, username, display_name),
        )
        await conn.commit()
        async with conn.execute(
            "SELECT message_count FROM users WHERE discord_id = ?",
            (discord_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return int(row["message_count"]) if row else 0

    async def add_conversation(
        self,
        *,
        discord_id: str,
        channel_id: str | None,
        message_id: str | None,
        role: str,
        content: str,
    ) -> None:
        conn = self._require_conn()
        await conn.execute(
            """
            INSERT INTO conversations(discord_id, channel_id, message_id, role, content)
            VALUES(?, ?, ?, ?, ?)
            """,
            (discord_id, channel_id, message_id, role, content),
        )
        await conn.commit()

    async def get_recent_conversation(self, *, discord_id: str, limit: int) -> list[ConversationRow]:
        conn = self._require_conn()
        async with conn.execute(
            """
            SELECT role, content
            FROM conversations
            WHERE discord_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (discord_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        rows = list(reversed(rows))
        return [ConversationRow(role=r["role"], content=r["content"]) for r in rows]

    async def add_memory(
        self,
        *,
        discord_id: str,
        memory_type: str,
        content: str,
        confidence: float,
        source_message_id: str | None,
    ) -> None:
        conn = self._require_conn()
        await conn.execute(
            """
            INSERT OR IGNORE INTO memories(discord_id, memory_type, content, confidence, source_message_id)
            VALUES(?, ?, ?, ?, ?)
            """,
            (discord_id, memory_type, content, confidence, source_message_id),
        )
        await conn.commit()

    async def list_memories(self, *, discord_id: str, limit: int) -> list[dict[str, Any]]:
        conn = self._require_conn()
        async with conn.execute(
            """
            SELECT id, memory_type, content, confidence, created_at
            FROM memories
            WHERE discord_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (discord_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]
