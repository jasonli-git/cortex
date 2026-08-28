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

---

# V2 — Interactive Learning

**Thesis shift.** V1 asked *"help me organize what I know."* That question is well served
by NotebookLM and Gemini Notebook, and competing there is a feature race Cortex cannot win.
V2 asks a question those tools do not answer:

> **Cortex maintains an evidence-backed model of what *you* understand, built from the
> material *you* give it, and teaches you from it.**

NotebookLM is an *extraction* tool — excellent at "summarize this," with no memory of you.
Khanmigo models the learner, but only against Khan Academy's own curriculum. The gap is a
learner model over your own material, and it is an engineering problem rather than a
content-licensing one — which is precisely where V1's machinery becomes an asset:

| V1 component | V2 purpose |
|---|---|
| Provenance (quote-level) | The tutor is grounded and cannot invent curriculum; every claim traces to a chunk |
| Typed relationship graph | Prerequisite structure; concept-level weak-spot detection |
| `ko_versions` revision history | The same append-only-evidence pattern, applied to learner state |
| Hybrid search | Retrieval keeps tutoring context small — a quality *and* cost lever |
| `learning_events` (migration 0006) | Activity log; V2 adds a parallel understanding log |

**Design principle:** the learner model is provenance applied to the learner. Understanding
is never stored as a score — it is derived from append-only evidence and can always be
recomputed and explained.

## V2 Milestones

| M | Status | Deliverable |
|---|--------|-------------|
| 10 | ⬜ next | **Tutor loop** — migration 0007 (`study_sessions`, `understanding_events`, `understanding_state`); `pks/tutor/` with three modes (teach / quiz / explain-back); `assessment` block added to the chat output contract; session summary carry-forward; study view in the frontend; fast tier moved to `claude-sonnet-5` |
| 11 | ⬜ | **Learner model** — confidence estimator over `understanding_events` (rebuildable, no migration to change); `prerequisite_of` relationship type + extraction; weak-spot detection via graph traversal; `due_at` spaced-review queue; "why does Cortex think I know this?" panel; graph nodes colored by confidence |
| 12 | ⬜ | **Cost & grounding instrumentation** — per-turn token/cost logging; prompt caching on the stable session prefix; grounding eval (~30 tutor turns with known-correct citations) measuring mis-citation rate across model tiers |
| 13 | ⬜ gated | **Material coverage** — EPUB parser, OCR for scanned PDFs, Gemini provider. *Gated on M10's exit criterion.* |

### M10 exit criterion

**Dogfood before expanding.** M10 is not "done" when it ships — it is done when the author
has used it for two weeks on the already-ingested economics textbook and can answer:

> *Is talking to my material meaningfully better than reading it?*

M13 and everything past it stay unscheduled until that question has a yes. This gate exists
specifically to prevent building a course platform, a subscription, or a deployment for a
learning experience that has not been shown to work.

### Notes on model tiers

The fast tier moves to `claude-sonnet-5` in M10 for one documented reason: the M6 note in
[TODO.md](TODO.md) records that Haiku's grounding is imperfect — a cited claim can misread
its source. In a knowledge tool that is a citation defect; in a tutor it means confidently
teaching something false, in the exact mode (explain-back grading) where the product's value
lives. Ingestion stays on the heavy tier — it runs once per resource and bad extraction
poisons everything downstream permanently.

Provider cost is deliberately **not** a V2 design input. At single-user scale the spread
between the cheapest and most expensive credible model is a few dollars a month. M12 exists
to replace that estimate with measurement before any provider decision is made.

---

## Parked (not scheduled)

Items here are deliberately unscheduled, not forgotten.

- **Assistant platform API** — external assistants consuming the Core Knowledge Engine.
  Serves the knowledge-infrastructure thesis rather than the learning one; parked pending
  a reason to pursue both.
- **Desktop packaging (Tauri)** — plausible endpoint for personal use; nothing depends on it.
- **Hosted deployment (Postgres + auth)** — implies a commercial product. Not decidable
  before M10's exit criterion; deliberately deferred rather than designed around.
- **Remaining parsers** — DOCX, web page (URL). EPUB and OCR moved to M13 as the two that
  serve the learning audience.
- **Remaining providers** — OpenAI, local via Ollama, Voyage embeddings. Gemini moved to M13.
- **Cross-type entity reconciliation** — e.g. "Rome" typed place vs. organization across
  runs; dedup deliberately will not merge across types.
- **Retry backoff for pipeline jobs; chunk overlap experiment for retrieval.**

**Removed:** per-stage resource usage capture (RAM / CPU / storage). Superseded by M12's
token and cost telemetry, which measures the number that actually drives decisions.
