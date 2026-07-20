-- Conversations with the accumulated knowledge (chat module).
--
-- workspace_id is a soft reference: the workspaces table arrives in the next
-- migration (Milestone 7), and SQLite cannot add a foreign key to an existing
-- table; the API layer validates it instead.

CREATE TABLE conversations (
    id           TEXT PRIMARY KEY,
    workspace_id TEXT,
    title        TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    segments        TEXT NOT NULL DEFAULT '[]',
    citations       TEXT NOT NULL DEFAULT '[]',
    created_at      TEXT NOT NULL
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
