-- Search infrastructure: vector embeddings + full-text indexes.
--
-- Embeddings are float32 BLOBs compared in the search module (linear scan —
-- fine at personal scale; the EmbeddingIndex class is the seam where
-- sqlite-vec or pgvector would slot in).
--
-- The FTS tables are maintained by the index pipeline stage, not triggers,
-- so indexing stays an explicit, retryable stage like everything else.

CREATE TABLE embeddings (
    owner_type  TEXT NOT NULL CHECK (owner_type IN ('chunk', 'knowledge_object')),
    owner_id    TEXT NOT NULL,
    resource_id TEXT,           -- set for chunk owners; enables cleanup on re-ingest
    model       TEXT NOT NULL,
    text_hash   TEXT NOT NULL,  -- sha256 of the embedded text; skip re-embedding unchanged
    dim         INTEGER NOT NULL,
    vector      BLOB NOT NULL,
    created_at  TEXT NOT NULL,
    PRIMARY KEY (owner_type, owner_id)
);

CREATE INDEX idx_embeddings_resource ON embeddings(resource_id);

CREATE VIRTUAL TABLE chunks_fts USING fts5(
    text,
    chunk_id UNINDEXED,
    resource_id UNINDEXED
);

CREATE VIRTUAL TABLE ko_fts USING fts5(
    name,
    aliases,
    description,
    ko_id UNINDEXED
);
