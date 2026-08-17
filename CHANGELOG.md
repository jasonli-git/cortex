# Changelog

All notable changes to Cortex. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] — V1 complete

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
- **Milestone 5** — dedup, merge, and graph: engine-level merge preserving history,
  provenance, and relationships (higher confidence wins on conflicts); dedupe pipeline
  stage with embedding-similarity candidates confirmed by the heavy-tier model before
  merging; cross-resource relation resolution; graph traversal endpoints
  (`/api/knowledge/graph`, `/api/knowledge/{id}/graph`); idempotent provenance.
- **Milestone 6** — chat with provenance: fast-tier RAG over hybrid-search retrieval;
  answers structured as segments labeled Cortex (validated, numbered citations with
  excerpts) or model knowledge, with unbacked Cortex claims downgraded; persisted
  conversations with history windowing; `/api/chat` + conversation management.
- **Milestone 7** — workspaces: reference-only contexts over knowledge (CRUD, polymorphic
  attach/detach, hydrated detail); upload/notes straight into a workspace; workspace-
  scoped retrieval for chat and search (resources + knowledge extracted from them).
- **Milestone 8** — React frontend (Vite + TypeScript + Tailwind): library with uploads,
  notes, and live pipeline progress; hybrid search; knowledge detail with evidence and
  history; cytoscape graph view; chat UI rendering Cortex-cited vs model-knowledge segments
  with citations; workspace management. Dev server proxies to the backend.
- **Milestone 9** — hardening: resource reprocessing with stable knowledge and
  provenance; global pipeline observability (`/api/jobs` + Pipeline page);
  learning-evidence groundwork (events recorded at intake and chat); README and
  ARCHITECTURE polish; frontend refinements.
