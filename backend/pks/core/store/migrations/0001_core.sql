-- Core Knowledge Engine schema.
-- Knowledge objects are the primary entities; resources are evidence linked
-- back via provenance. See ARCHITECTURE.md for the schema overview.

CREATE TABLE resources (
    id            TEXT PRIMARY KEY,
    type          TEXT NOT NULL CHECK (type IN ('pdf', 'markdown', 'text', 'note')),
    title         TEXT NOT NULL,
    path          TEXT,
    content_hash  TEXT,
    status        TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
    relationship  TEXT NOT NULL DEFAULT 'reference'
                  CHECK (relationship IN ('active_learning', 'reference')),
    error         TEXT,
    metadata      TEXT NOT NULL DEFAULT '{}',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE resource_chunks (
    id             TEXT PRIMARY KEY,
    resource_id    TEXT NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    ordinal        INTEGER NOT NULL,
    structure_path TEXT,
    text           TEXT NOT NULL,
    token_count    INTEGER,
    UNIQUE (resource_id, ordinal)
);

CREATE TABLE knowledge_objects (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL
                CHECK (type IN ('concept', 'person', 'organization', 'place', 'event', 'summary')),
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    aliases     TEXT NOT NULL DEFAULT '[]',
    metadata    TEXT NOT NULL DEFAULT '{}',
    version     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX idx_ko_type ON knowledge_objects(type);
CREATE INDEX idx_ko_name ON knowledge_objects(name);

-- Revision history. Deliberately no foreign key: history is an audit log and
-- must survive deletion of the knowledge object it describes.
CREATE TABLE ko_versions (
    id                  TEXT PRIMARY KEY,
    knowledge_object_id TEXT NOT NULL,
    version             INTEGER NOT NULL,
    operation           TEXT NOT NULL CHECK (operation IN ('created', 'updated', 'deleted')),
    snapshot            TEXT NOT NULL,
    changed_by          TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    UNIQUE (knowledge_object_id, version, operation)
);

CREATE INDEX idx_kover_ko ON ko_versions(knowledge_object_id);

CREATE TABLE relationships (
    id         TEXT PRIMARY KEY,
    from_id    TEXT NOT NULL REFERENCES knowledge_objects(id) ON DELETE CASCADE,
    to_id      TEXT NOT NULL REFERENCES knowledge_objects(id) ON DELETE CASCADE,
    type       TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0.0 AND 1.0),
    created_by TEXT NOT NULL,
    metadata   TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (from_id, to_id, type),
    CHECK (from_id <> to_id)
);

CREATE INDEX idx_rel_from ON relationships(from_id);
CREATE INDEX idx_rel_to ON relationships(to_id);

-- Evidence links. Exactly one of knowledge_object_id / relationship_id is set.
CREATE TABLE provenance (
    id                  TEXT PRIMARY KEY,
    knowledge_object_id TEXT REFERENCES knowledge_objects(id) ON DELETE CASCADE,
    relationship_id     TEXT REFERENCES relationships(id) ON DELETE CASCADE,
    resource_id         TEXT NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    chunk_id            TEXT REFERENCES resource_chunks(id) ON DELETE SET NULL,
    quote               TEXT,
    created_at          TEXT NOT NULL,
    CHECK ((knowledge_object_id IS NULL) <> (relationship_id IS NULL))
);

CREATE INDEX idx_prov_ko ON provenance(knowledge_object_id);
CREATE INDEX idx_prov_rel ON provenance(relationship_id);
CREATE INDEX idx_prov_resource ON provenance(resource_id);
