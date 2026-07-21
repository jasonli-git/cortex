-- Workspaces: contexts in which knowledge is used (spec: a workspace never
-- owns knowledge — it references it; the same object can appear in many
-- workspaces, and deleting a workspace deletes only the references).

CREATE TABLE workspaces (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- Polymorphic references; object_id intentionally has no foreign key.
-- Conversation refs are validated at the API layer (the conversations table
-- belongs to the chat module); stale refs are skipped and pruned lazily.
CREATE TABLE workspace_refs (
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    object_type  TEXT NOT NULL
                 CHECK (object_type IN ('resource', 'knowledge_object', 'conversation')),
    object_id    TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    PRIMARY KEY (workspace_id, object_type, object_id)
);

CREATE INDEX idx_wsrefs_object ON workspace_refs(object_type, object_id);
