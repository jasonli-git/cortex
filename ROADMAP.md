# Cortex — Roadmap

**V1 is complete** — all nine milestones shipped. Each milestone ended with passing
tests, a live demo, updated docs, and user review.

## V1 Milestones

| M | Status | Deliverable |
|---|--------|-------------|
| 0 | ✅ done | **Scaffolding** — repo layout, tooling (uv, ruff, pytest), config, empty FastAPI app with health check, project docs |
| 1 | ✅ done | **Core Knowledge Engine** — schema, migrations, repositories, engine API (CRUD for knowledge objects / relationships / provenance, versioning), unit tests |
| 2 | ✅ done | **Event system + resource intake** — durable jobs, event bus, upload API, PDF/MD/TXT parsers, structure-aware chunking (no AI yet) |
| 3 | ✅ done | **AI extraction** — provider abstraction, structure/summary/entity/concept stages writing knowledge objects with provenance |
| 4 | ✅ done | **Embeddings + hybrid search** — local embeddings, sqlite-vec, FTS5, combined ranking, search API |
| 5 | ✅ done | **Relationships + dedup + graph API** — relationship builder stage, merge-on-ingest, graph traversal endpoints |
| 6 | ✅ done | **Chat with provenance** — RAG service, fast-model conversation, per-claim source labels (Cortex vs. model) |
| 7 | ✅ done | **Workspaces + notes** — workspace CRUD/refs, note-as-resource fast path through the pipeline |
| 8 | ✅ done | **Frontend** — library, upload with pipeline progress, search, knowledge-object detail with provenance, graph view, chat, workspaces |
| 9 | ✅ done | **Hardening** — reprocessing, pipeline observability UI, docs polish, learning-evidence schema groundwork |

## Post-V1 (not scheduled)

- EPUB / web page (URL) / DOCX parsers; OCR for scanned PDFs
- Learning analytics: evidence-based confidence model
- Additional AI providers (OpenAI, local via Ollama); Voyage embeddings
- Desktop packaging (Tauri) and/or hosted deployment (Postgres + auth)
- Assistant platform API: external assistants consuming the Core Knowledge Engine
