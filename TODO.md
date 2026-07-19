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

## Milestone 2 — Event system + resource intake (next, pending approval)

- [ ] Durable job queue (jobs table + migration) and async worker
- [ ] Event bus with pipeline-stage subscription
- [ ] Resource upload API (file + note), on-disk resource store
- [ ] Parsers: PDF, Markdown, plaintext
- [ ] Structure-aware chunking (no AI yet)
- [ ] Pipeline status visible via API

## Parked / needs user input

- Anthropic API key required before Milestone 3 (`ANTHROPIC_API_KEY`)
- Node.js required before Milestone 8 (frontend scaffold)
