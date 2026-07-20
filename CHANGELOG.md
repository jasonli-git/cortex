# Changelog

All notable changes to AI PKS. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Project documentation: SPEC.md (source of truth), ARCHITECTURE.md (design + decisions log),
  ROADMAP.md (milestones), TODO.md, CHANGELOG.md.
- **Milestone 0** — backend scaffold: uv-managed Python 3.12 project, FastAPI app factory
  with `/api/health`, environment-based settings (`PKS_*`), ruff + pytest tooling,
  passing smoke tests.
- **Milestone 1** — Core Knowledge Engine: SQLite schema + migration runner for the
  knowledge core (resources, chunks, knowledge objects, revision history, relationships,
  provenance); repository protocols with SQLite implementations; `KnowledgeEngine` API
  with automatic versioning, idempotent relationships, validated provenance, and
  resource/chunk management. 21 unit tests.
- **Milestone 2** — event-driven pipeline + resource intake: durable job queue with
  retries, pipeline registry (stages subscribe to events), background worker thread;
  PDF/Markdown/plaintext parsers with native-structure extraction; structure-aware
  chunking; upload + note APIs with SHA-256 dedup and per-resource pipeline status.
  29 new tests including end-to-end upload → ready.
- **Milestone 3** — AI extraction: provider abstraction (heavy/fast tiers) with an
  Anthropic structured-outputs implementation; extraction stages chained after chunking
  produce entities/concepts/events with quote-level provenance, typed relationships with
  confidence, and a per-document summary object; naive name/alias merging across
  resources; knowledge browse API. Verified live against the Anthropic API.
- **Milestone 4** — embeddings + hybrid search: local sentence-transformers embeddings
  behind an EmbeddingProvider abstraction; vector store (float32 BLOB + numpy cosine)
  and FTS5 keyword indexes maintained by a new `index` pipeline stage; hybrid search
  with reciprocal-rank fusion over knowledge objects and chunks; `GET /api/search`.
  Search works with or without an AI provider configured.
