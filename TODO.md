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

## Milestone 4 — Embeddings + hybrid search (next, pending approval)

- [ ] EmbeddingProvider abstraction + local sentence-transformers implementation
- [ ] sqlite-vec vector index + embed pipeline stage
- [ ] FTS5 keyword index over chunks and knowledge objects
- [ ] Hybrid search service + API endpoint

## Parked / needs user input

- Anthropic API key required before Milestone 3 (`ANTHROPIC_API_KEY`)
- Node.js required before Milestone 8 (frontend scaffold)
