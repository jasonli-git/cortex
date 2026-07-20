"""Persistence for conversations and messages (module-local data access)."""

from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from pks.chat.models import Conversation, Message, MessageRole
from pks.core.store.db import utcnow
from pks.core.store.sqlite import SqliteStore


def _row_to_conversation(row: sqlite3.Row) -> Conversation:
    return Conversation(
        id=row["id"],
        workspace_id=row["workspace_id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_message(row: sqlite3.Row) -> Message:
    return Message(
        id=row["id"],
        conversation_id=row["conversation_id"],
        role=row["role"],
        content=row["content"],
        segments=json.loads(row["segments"]),
        citations=json.loads(row["citations"]),
        created_at=row["created_at"],
    )


class ChatStore:
    def __init__(self, store: SqliteStore):
        self._conn = store.connection

    def create_conversation(
        self, *, title: str, workspace_id: str | None = None
    ) -> Conversation:
        now = utcnow()
        conversation = Conversation(
            id=uuid4().hex,
            workspace_id=workspace_id,
            title=title,
            created_at=now,
            updated_at=now,
        )
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO conversations (id, workspace_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conversation.id,
                    conversation.workspace_id,
                    conversation.title,
                    conversation.created_at,
                    conversation.updated_at,
                ),
            )
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        row = self._conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        return _row_to_conversation(row) if row else None

    def list_conversations(self) -> list[Conversation]:
        rows = self._conn.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
        return [_row_to_conversation(row) for row in rows]

    def delete_conversation(self, conversation_id: str) -> bool:
        with self._conn:
            cur = self._conn.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
        return cur.rowcount > 0

    def touch_conversation(self, conversation_id: str) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (utcnow(), conversation_id),
            )

    def add_message(self, message: Message) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO messages
                    (id, conversation_id, role, content, segments, citations, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.conversation_id,
                    message.role,
                    message.content,
                    json.dumps([s.model_dump() for s in message.segments]),
                    json.dumps([c.model_dump() for c in message.citations]),
                    message.created_at,
                ),
            )

    def list_messages(self, conversation_id: str) -> list[Message]:
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at, id",
            (conversation_id,),
        )
        return [_row_to_message(row) for row in rows]


def new_message(
    conversation_id: str,
    role: MessageRole,
    content: str,
    *,
    segments: list | None = None,
    citations: list | None = None,
) -> Message:
    return Message(
        id=uuid4().hex,
        conversation_id=conversation_id,
        role=role,
        content=content,
        segments=segments or [],
        citations=citations or [],
        created_at=utcnow(),
    )
