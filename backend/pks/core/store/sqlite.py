"""SQLite implementation of the storage protocols (V1 backend)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from pks.core.models import (
    KnowledgeObject,
    KnowledgeObjectType,
    KnowledgeObjectVersion,
    Provenance,
    Relationship,
    Resource,
    ResourceChunk,
)
from pks.core.store import db


def _row_to_ko(row: sqlite3.Row) -> KnowledgeObject:
    return KnowledgeObject(
        id=row["id"],
        type=row["type"],
        name=row["name"],
        description=row["description"],
        aliases=json.loads(row["aliases"]),
        metadata=json.loads(row["metadata"]),
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_relationship(row: sqlite3.Row) -> Relationship:
    return Relationship(
        id=row["id"],
        from_id=row["from_id"],
        to_id=row["to_id"],
        type=row["type"],
        confidence=row["confidence"],
        created_by=row["created_by"],
        metadata=json.loads(row["metadata"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_resource(row: sqlite3.Row) -> Resource:
    return Resource(
        id=row["id"],
        type=row["type"],
        title=row["title"],
        path=row["path"],
        content_hash=row["content_hash"],
        status=row["status"],
        relationship=row["relationship"],
        error=row["error"],
        metadata=json.loads(row["metadata"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class SqliteKnowledgeObjectRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def insert(self, ko: KnowledgeObject) -> None:
        self._conn.execute(
            """
            INSERT INTO knowledge_objects
                (id, type, name, description, aliases, metadata, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ko.id,
                ko.type,
                ko.name,
                ko.description,
                json.dumps(ko.aliases),
                json.dumps(ko.metadata),
                ko.version,
                ko.created_at,
                ko.updated_at,
            ),
        )

    def get(self, ko_id: str) -> KnowledgeObject | None:
        row = self._conn.execute(
            "SELECT * FROM knowledge_objects WHERE id = ?", (ko_id,)
        ).fetchone()
        return _row_to_ko(row) if row else None

    def list(
        self,
        *,
        type: KnowledgeObjectType | None = None,
        name_contains: str | None = None,
    ) -> list[KnowledgeObject]:
        sql = "SELECT * FROM knowledge_objects"
        clauses: list[str] = []
        params: list[object] = []
        if type is not None:
            clauses.append("type = ?")
            params.append(type)
        if name_contains:
            # Simple substring match over name and aliases; proper full-text
            # search arrives with the search module (Milestone 4).
            clauses.append("(name LIKE ? OR aliases LIKE ?)")
            pattern = f"%{name_contains}%"
            params.extend([pattern, pattern])
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY name"
        return [_row_to_ko(row) for row in self._conn.execute(sql, params)]

    def update(self, ko: KnowledgeObject) -> None:
        self._conn.execute(
            """
            UPDATE knowledge_objects
            SET type = ?, name = ?, description = ?, aliases = ?, metadata = ?,
                version = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                ko.type,
                ko.name,
                ko.description,
                json.dumps(ko.aliases),
                json.dumps(ko.metadata),
                ko.version,
                ko.updated_at,
                ko.id,
            ),
        )

    def delete(self, ko_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM knowledge_objects WHERE id = ?", (ko_id,))
        return cur.rowcount > 0

    def insert_version(self, version: KnowledgeObjectVersion) -> None:
        self._conn.execute(
            """
            INSERT INTO ko_versions
                (id, knowledge_object_id, version, operation, snapshot, changed_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version.id,
                version.knowledge_object_id,
                version.version,
                version.operation,
                json.dumps(version.snapshot),
                version.changed_by,
                version.created_at,
            ),
        )

    def list_versions(self, ko_id: str) -> list[KnowledgeObjectVersion]:
        rows = self._conn.execute(
            """
            SELECT * FROM ko_versions WHERE knowledge_object_id = ?
            ORDER BY version, created_at
            """,
            (ko_id,),
        )
        return [
            KnowledgeObjectVersion(
                id=row["id"],
                knowledge_object_id=row["knowledge_object_id"],
                version=row["version"],
                operation=row["operation"],
                snapshot=json.loads(row["snapshot"]),
                changed_by=row["changed_by"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class SqliteRelationshipRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def upsert(self, rel: Relationship) -> Relationship:
        self._conn.execute(
            """
            INSERT INTO relationships
                (id, from_id, to_id, type, confidence, created_by, metadata,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (from_id, to_id, type) DO UPDATE SET
                confidence = excluded.confidence,
                metadata = excluded.metadata,
                updated_at = excluded.updated_at
            """,
            (
                rel.id,
                rel.from_id,
                rel.to_id,
                rel.type,
                rel.confidence,
                rel.created_by,
                json.dumps(rel.metadata),
                rel.created_at,
                rel.updated_at,
            ),
        )
        row = self._conn.execute(
            "SELECT * FROM relationships WHERE from_id = ? AND to_id = ? AND type = ?",
            (rel.from_id, rel.to_id, rel.type),
        ).fetchone()
        return _row_to_relationship(row)

    def get(self, rel_id: str) -> Relationship | None:
        row = self._conn.execute(
            "SELECT * FROM relationships WHERE id = ?", (rel_id,)
        ).fetchone()
        return _row_to_relationship(row) if row else None

    def delete(self, rel_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM relationships WHERE id = ?", (rel_id,))
        return cur.rowcount > 0

    def list_for(self, ko_id: str) -> list[Relationship]:
        rows = self._conn.execute(
            """
            SELECT * FROM relationships WHERE from_id = ? OR to_id = ?
            ORDER BY type, created_at
            """,
            (ko_id, ko_id),
        )
        return [_row_to_relationship(row) for row in rows]


class SqliteProvenanceRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def insert(self, prov: Provenance) -> None:
        self._conn.execute(
            """
            INSERT INTO provenance
                (id, knowledge_object_id, relationship_id, resource_id, chunk_id,
                 quote, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prov.id,
                prov.knowledge_object_id,
                prov.relationship_id,
                prov.resource_id,
                prov.chunk_id,
                prov.quote,
                prov.created_at,
            ),
        )

    def _list(self, column: str, value: str) -> list[Provenance]:
        rows = self._conn.execute(
            f"SELECT * FROM provenance WHERE {column} = ? ORDER BY created_at",  # noqa: S608
            (value,),
        )
        return [
            Provenance(
                id=row["id"],
                knowledge_object_id=row["knowledge_object_id"],
                relationship_id=row["relationship_id"],
                resource_id=row["resource_id"],
                chunk_id=row["chunk_id"],
                quote=row["quote"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def list_for_knowledge_object(self, ko_id: str) -> list[Provenance]:
        return self._list("knowledge_object_id", ko_id)

    def list_for_relationship(self, rel_id: str) -> list[Provenance]:
        return self._list("relationship_id", rel_id)


class SqliteResourceRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def insert(self, resource: Resource) -> None:
        self._conn.execute(
            """
            INSERT INTO resources
                (id, type, title, path, content_hash, status, relationship, error,
                 metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resource.id,
                resource.type,
                resource.title,
                resource.path,
                resource.content_hash,
                resource.status,
                resource.relationship,
                resource.error,
                json.dumps(resource.metadata),
                resource.created_at,
                resource.updated_at,
            ),
        )

    def get(self, resource_id: str) -> Resource | None:
        row = self._conn.execute(
            "SELECT * FROM resources WHERE id = ?", (resource_id,)
        ).fetchone()
        return _row_to_resource(row) if row else None

    def get_by_hash(self, content_hash: str) -> Resource | None:
        row = self._conn.execute(
            "SELECT * FROM resources WHERE content_hash = ? LIMIT 1", (content_hash,)
        ).fetchone()
        return _row_to_resource(row) if row else None

    def list(self) -> list[Resource]:
        rows = self._conn.execute("SELECT * FROM resources ORDER BY created_at")
        return [_row_to_resource(row) for row in rows]

    def update(self, resource: Resource) -> None:
        self._conn.execute(
            """
            UPDATE resources
            SET type = ?, title = ?, path = ?, content_hash = ?, status = ?,
                relationship = ?, error = ?, metadata = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                resource.type,
                resource.title,
                resource.path,
                resource.content_hash,
                resource.status,
                resource.relationship,
                resource.error,
                json.dumps(resource.metadata),
                resource.updated_at,
                resource.id,
            ),
        )

    def replace_chunks(self, resource_id: str, chunks: list[ResourceChunk]) -> None:
        self._conn.execute(
            "DELETE FROM resource_chunks WHERE resource_id = ?", (resource_id,)
        )
        self._conn.executemany(
            """
            INSERT INTO resource_chunks
                (id, resource_id, ordinal, structure_path, text, token_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (c.id, c.resource_id, c.ordinal, c.structure_path, c.text, c.token_count)
                for c in chunks
            ],
        )

    def list_chunks(self, resource_id: str) -> list[ResourceChunk]:
        rows = self._conn.execute(
            "SELECT * FROM resource_chunks WHERE resource_id = ? ORDER BY ordinal",
            (resource_id,),
        )
        return [
            ResourceChunk(
                id=row["id"],
                resource_id=row["resource_id"],
                ordinal=row["ordinal"],
                structure_path=row["structure_path"],
                text=row["text"],
                token_count=row["token_count"],
            )
            for row in rows
        ]

    def get_chunk(self, chunk_id: str) -> ResourceChunk | None:
        row = self._conn.execute(
            "SELECT * FROM resource_chunks WHERE id = ?", (chunk_id,)
        ).fetchone()
        if row is None:
            return None
        return ResourceChunk(
            id=row["id"],
            resource_id=row["resource_id"],
            ordinal=row["ordinal"],
            structure_path=row["structure_path"],
            text=row["text"],
            token_count=row["token_count"],
        )


class SqliteStore:
    """Bundles the SQLite repositories over one connection.

    Migrations are applied on construction, so opening a store always yields a
    ready database.
    """

    def __init__(self, db_path: Path | str):
        self._conn = db.connect(db_path)
        db.migrate(self._conn)
        self.knowledge_objects = SqliteKnowledgeObjectRepository(self._conn)
        self.relationships = SqliteRelationshipRepository(self._conn)
        self.provenance = SqliteProvenanceRepository(self._conn)
        self.resources = SqliteResourceRepository(self._conn)

    @property
    def connection(self) -> sqlite3.Connection:
        """The underlying connection, for module-local data access (e.g. the job queue).

        The schema itself stays centrally owned by core migrations.
        """
        return self._conn

    @contextmanager
    def transaction(self):
        try:
            yield
        except BaseException:
            self._conn.rollback()
            raise
        else:
            self._conn.commit()

    def close(self) -> None:
        self._conn.close()
