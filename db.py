# pyre-ignore-all-errors
import asyncio  # type: ignore  # pyre-ignore
from dataclasses import dataclass  # type: ignore  # pyre-ignore
from datetime import datetime, timezone  # type: ignore  # pyre-ignore
from typing import Any, Iterable, List, Optional, Sequence  # type: ignore  # pyre-ignore

import aiosqlite  # type: ignore  # pyre-ignore


@dataclass(frozen=True, slots=True)
class MessageRow:
    created_at: str
    role: str
    content: str


class ConversationStore:
    def __init__(self, sqlite_path: str):
        self._sqlite_path = sqlite_path
        self._conn: Optional[aiosqlite.Connection] = None  # type: ignore  # pyre-ignore
        self._lock = asyncio.Lock()

    async def open(self) -> None:  # type: ignore  # pyre-ignore
        self._conn = await aiosqlite.connect(self._sqlite_path)
        self._conn.row_factory = aiosqlite.Row  # type: ignore  # pyre-ignore
        await self._conn.execute("PRAGMA journal_mode=WAL;")  # type: ignore  # pyre-ignore
        await self._conn.execute("PRAGMA synchronous=NORMAL;")  # type: ignore  # pyre-ignore
        await self._conn.execute("PRAGMA foreign_keys=ON;")  # type: ignore  # pyre-ignore
        await self._conn.commit()  # type: ignore  # pyre-ignore
        await self._ensure_schema()

    async def close(self) -> None:  # type: ignore  # pyre-ignore
        if self._conn is None:
            return
        await self._conn.close()  # type: ignore  # pyre-ignore
        self._conn = None

    async def _ensure_schema(self) -> None:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        await self._conn.executescript(  # type: ignore  # pyre-ignore
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_user_chat_id ON messages(user_id, chat_id, id);

            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                personality TEXT NOT NULL
            );
            """
        )
        await self._conn.commit()  # type: ignore  # pyre-ignore

    @staticmethod
    def _now_iso_utc() -> str:  # type: ignore  # pyre-ignore
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    async def add_message(self, *, user_id: int, chat_id: int, role: str, content: str) -> None:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        created_at = self._now_iso_utc()
        async with self._lock:
            await self._conn.execute(  # type: ignore  # pyre-ignore
                "INSERT INTO messages(user_id, chat_id, role, content, created_at) VALUES(?,?,?,?,?)",
                (user_id, chat_id, role, content, created_at),
            )
            await self._conn.commit()  # type: ignore  # pyre-ignore

    async def clear_history(self, *, user_id: int, chat_id: int) -> None:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(  # type: ignore  # pyre-ignore
                "DELETE FROM messages WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            await self._conn.commit()  # type: ignore  # pyre-ignore

    async def clear_user_history(self, *, user_id: int) -> None:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))  # type: ignore  # pyre-ignore
            await self._conn.commit()  # type: ignore  # pyre-ignore

    async def get_recent_messages(
        self, *, user_id: int, chat_id: int, limit: int
    ) -> List[dict[str, str]]:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        async with self._lock:
            cur = await self._conn.execute(  # type: ignore  # pyre-ignore
                """
                SELECT role, content
                FROM messages
                WHERE user_id = ? AND chat_id = ? AND role IN ('user','assistant')
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, chat_id, limit),
            )
            rows = await cur.fetchall()
        rows.reverse()
        return [{"role": r["role"], "content": r["content"]} for r in rows]  # type: ignore  # pyre-ignore

    async def list_user_ids(self) -> List[int]:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        async with self._lock:
            cur = await self._conn.execute("SELECT DISTINCT user_id FROM messages ORDER BY user_id ASC")  # type: ignore  # pyre-ignore
            rows = await cur.fetchall()
        return [int(r["user_id"]) for r in rows]

    async def get_personality(self, *, user_id: int) -> Optional[str]:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        async with self._lock:
            cur = await self._conn.execute(  # type: ignore  # pyre-ignore
                "SELECT personality FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            row = await cur.fetchone()
            return row["personality"] if row else None  # type: ignore  # pyre-ignore

    async def set_personality(self, *, user_id: int, personality: str) -> None:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(  # type: ignore  # pyre-ignore
                """
                INSERT INTO user_settings (user_id, personality)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET personality=excluded.personality
                """,
                (user_id, personality)
            )
            await self._conn.commit()  # type: ignore  # pyre-ignore

    async def get_recent_messages_all_chats(self, *, user_id: int, limit: int) -> List[dict[str, str]]:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        async with self._lock:
            cur = await self._conn.execute(  # type: ignore  # pyre-ignore
                """
                SELECT role, content
                FROM messages
                WHERE user_id = ? AND role IN ('user','assistant')
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cur.fetchall()
        rows.reverse()
        return [{"role": r["role"], "content": r["content"]} for r in rows]  # type: ignore  # pyre-ignore

    async def get_full_history(self, *, user_id: int, chat_id: int) -> List[MessageRow]:  # type: ignore  # pyre-ignore
        assert self._conn is not None
        async with self._lock:
            cur = await self._conn.execute(  # type: ignore  # pyre-ignore
                """
                SELECT created_at, role, content
                FROM messages
                WHERE user_id = ? AND chat_id = ?
                ORDER BY id ASC
                """,
                (user_id, chat_id),
            )
            rows = await cur.fetchall()
        return [MessageRow(created_at=r["created_at"], role=r["role"], content=r["content"]) for r in rows]

    async def export_history_text(self, *, user_id: int, chat_id: int) -> str:  # type: ignore  # pyre-ignore
        rows = await self.get_full_history(user_id=user_id, chat_id=chat_id)
        if not rows:
            return "No conversation history found."
        parts: list[str] = []  # type: ignore  # pyre-ignore
        for r in rows:
            role = "YOU" if r.role == "user" else ("NOVA" if r.role == "assistant" else r.role.upper())
            parts.append(f"[{r.created_at}] {role}:\n{r.content}\n")  # type: ignore  # pyre-ignore
        return "\n".join(parts).strip() + "\n"


