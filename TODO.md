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

## Milestone 1 — Core Knowledge Engine (next, pending approval)

- [ ] Schema + migrations for core tables
- [ ] Repository interfaces + SQLite implementations
- [ ] Engine API: knowledge object / relationship / provenance CRUD, versioning
- [ ] Unit tests for engine behavior

## Parked / needs user input

- Anthropic API key required before Milestone 3 (`ANTHROPIC_API_KEY`)
- Node.js required before Milestone 8 (frontend scaffold)
