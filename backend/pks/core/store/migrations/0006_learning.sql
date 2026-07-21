-- Learning-evidence groundwork (spec: understanding is represented as
-- evidence-based confidence, "not required for Version 1").
--
-- V1 only accumulates evidence at natural interaction points; the confidence
-- model that interprets it is future work. Kinds cover the spec's examples;
-- extending the list is a migration.

CREATE TABLE learning_events (
    id           TEXT PRIMARY KEY,
    kind         TEXT NOT NULL CHECK (kind IN (
                     'resource_ingested',
                     'note_written',
                     'question_asked',
                     'knowledge_viewed',
                     'search_performed'
                 )),
    subject_type TEXT CHECK (subject_type IN ('resource', 'knowledge_object', 'conversation')),
    subject_id   TEXT,
    detail       TEXT NOT NULL DEFAULT '{}',
    created_at   TEXT NOT NULL
);

CREATE INDEX idx_learning_kind ON learning_events(kind, created_at);
CREATE INDEX idx_learning_subject ON learning_events(subject_type, subject_id);
