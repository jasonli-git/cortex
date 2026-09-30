# Cortex — Roadmap

**V1 is complete** — all nine milestones shipped, each with passing tests, a live demo,
updated docs, and user review. **V2 is finishing work**: make the existing system
cheaper to run, reliable, and polished, then call it done. No new product surface.

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

## V1.5 Milestones — archived 2026-09-30

The Practice & Diagnosis direction (tutor loop, misconception detection) was dropped in
the 2026-09-30 rescope. Its full rationale is preserved at `git show 702bc09:ROADMAP.md`.

| M | Status | Deliverable |
|---|--------|-------------|
| 10 | ❌ dropped | **Practice loop** — tutoring, quizzes, and explain-back are out of scope |
| 11 | ❌ dropped | **UI revamp (study environment)** — superseded by M18, which polishes the existing product instead of re-aiming it |
| 12 | ❌ dropped | **Misconception detection** — depended on M10's practice data |
| 13 | ❌ dropped | **Material coverage (EPUB, OCR)** — format breadth for its own sake is out of scope |

## V2 Milestones — Finish

**Cost rule for all of V2:** reduce spend by making fewer, smaller, cached, and batched
calls — not by moving a stage to a weaker model. Extraction and dedup stay on the heavy
tier. A model change is allowed only when measured output quality holds.

| M | Status | Deliverable |
|---|--------|-------------|
| 14 | ⬜ planned | **Cleanup** — remove learning-evidence code (`learning_events`, recorder, call sites), archive V1.5 plan in ARCHITECTURE, CI running the test suite |
| 15 | ⬜ planned | **Cost visibility** — per-call token + cost capture (incl. cache reads/writes) persisted per stage, resource, and chat message; costs shown on Pipeline and resource pages; baseline measured on a fixed reference corpus |
| 16 | ⬜ planned | **Cost reduction, quality held** — prompt caching, single full-text pass for extraction + summary, extraction cache for unchanged chunks on reprocess, batched dedup confirmations, opt-in Message Batches ingestion, trimmed prompts/context; gated on a before/after quality check against the M15 baseline |
| 17 | ⬜ planned | **Reliability** — retry backoff, consistent error surfaces, simplified config, consolidated duplicate logic, provenance integrity checks |
| 18 | ⬜ planned | **UI polish** — navigation and hierarchy, visual consistency, empty/loading/error/processing states, readable graph, responsive layout |
| 19 | ⬜ planned | **Completion** — end-to-end demo script, refreshed screenshots, docs reflect the final product |

### M16 success gate

Measured on the M15 reference corpus: ingestion cost per document and chat cost per
message drop materially from baseline, while extraction output (object and relationship
counts, spot-checked provenance quotes) and chat citation accuracy do not regress.
Anything that saves money but fails the quality check is reverted.

---

## Explicitly not doing

Tutoring modes · quizzes · explain-back · mastery or confidence scoring · learner
models · prerequisite tracking · spaced repetition · automated study plans ·
continuous or autonomous ingestion · always-on AI features · new document formats
added only for breadth · course libraries · multi-user · cloud deployment ·
subscriptions · downgrading model tiers purely to save money

These are declined, not pending. Re-proposing one should require new evidence.

## Post-V2 (not scheduled)

- **Assistant platform API** — external assistants consuming the Core Knowledge Engine.
- **Desktop packaging (Tauri)** — plausible endpoint for personal use.
- **Additional providers** — Gemini, OpenAI, local via Ollama.
- **Cross-type entity reconciliation** — e.g. "Rome" typed place vs. organization;
  dedup deliberately will not merge across types.
- **Chunk overlap experiment** for retrieval.
