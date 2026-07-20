# AI PKS — TODO

Working list for the current milestone. Longer-horizon items live in [ROADMAP.md](ROADMAP.md).

## Milestone 0 — Scaffolding

- [x] Install tooling (uv)
- [x] Project docs: SPEC.md, ARCHITECTURE.md, ROADMAP.md, TODO.md, CHANGELOG.md
- [x] Backend scaffold: pyproject (uv), ruff + pytest config
- [x] `pks` package skeleton with config loading
- [x] FastAPI app factory + `/api/health` endpoint
- [x] Smoke tests passing (`uv run pytest`)
- [x] Update .gitignore for Python/Node artifacts

## Milestone 1 — Core Knowledge Engine

- [x] Schema + migrations for core tables
- [x] Repository interfaces + SQLite implementations
- [x] Engine API: knowledge object / relationship / provenance CRUD, versioning
- [x] Unit tests for engine behavior

## Milestone 2 — Event system + resource intake

- [x] Durable job queue (jobs table + migration) and worker thread
- [x] Event bus with pipeline-stage subscription
- [x] Resource upload API (file + note), on-disk resource store
- [x] Parsers: PDF, Markdown, plaintext
- [x] Structure-aware chunking (no AI yet)
- [x] Pipeline status visible via API

## Milestone 3 — AI extraction

- [x] CompletionProvider abstraction + Anthropic implementation
- [x] Structured-output extraction stages: summaries, entities/concepts/events, relations
- [x] Extraction writes knowledge objects with provenance via the engine
- [x] ANTHROPIC_API_KEY configured in backend/.env (gitignored); verified live
- Note: LLM structure *refinement* (improving "Page N" paths on outline-less PDFs)
  deferred — parsers already provide native structure; revisit in Milestone 9

## Milestone 4 — Embeddings + hybrid search

- [x] EmbeddingProvider abstraction + local sentence-transformers implementation
- [x] Vector index (float32 BLOB + numpy; sqlite-vec deferred — see ARCHITECTURE #3)
- [x] FTS5 keyword index over chunks and knowledge objects
- [x] Hybrid search service (RRF fusion) + API endpoint

## Milestone 5 — Relationships + dedup + graph API

- [x] Embedding-based duplicate detection with LLM-confirmed merge (dedupe stage)
- [x] Engine merge operation (relationships/provenance/aliases transfer, history kept)
- [x] Relationship resolver falls back to the whole knowledge base (cross-resource links)
- [x] Graph traversal API: /api/knowledge/graph and /api/knowledge/{id}/graph

## Milestone 6 — Chat with provenance

- [x] RAG chat service on the fast tier using hybrid search retrieval
- [x] Per-segment source labels: PKS (validated citations) vs. model knowledge
- [x] Conversations/messages persistence (migration 0004) + API
- [x] Conversation context window management (recent turns)
- Note: fast-tier (Haiku) grounding is imperfect — a cited claim can still misread
  its source. Citations make this checkable; consider a heavy-tier chat option or
  a verification pass post-V1.

## Milestone 7 — Workspaces + notes (next, pending approval)

- [ ] Workspaces table (migration) + engine/API CRUD
- [ ] Workspace refs: attach/detach resources, knowledge objects, conversations
- [ ] Notes already ingest via /api/resources/notes — wire into workspace flow
- [ ] Optional workspace scoping for chat retrieval

## Parked / needs user input

- Anthropic API key required before Milestone 3 (`ANTHROPIC_API_KEY`)
- Node.js required before Milestone 8 (frontend scaffold)
