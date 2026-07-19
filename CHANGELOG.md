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
