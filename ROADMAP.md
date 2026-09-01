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

# V1.5 — Practice & Diagnosis

**Scope note.** An earlier draft of this section proposed a full "V2 — Interactive
Learning" platform: a tutor loop, a learner model with confidence scores and a
prerequisite graph, cost instrumentation, and eventually a curated course library.
That plan was cut deliberately. Two questions shrank it:

1. **Can ChatGPT already do this?** For conversational tutoring over a textbook —
   largely yes, and increasingly so. "AI tutor that talks through your material" is
   not a defensible thing to build.
2. **What is retrieval actually for here?** A textbook fits in a modern context
   window. If RAG's job is "make the book fit," it is plumbing that gets cheaper to
   replace every year.

What survives both questions is narrower and more interesting.

## The bet

Cortex is not a tutor. It is a **practice partner that diagnoses how you are wrong.**

Not *"you scored 54% on elasticity"* — a number that is easy to fake and hard to
trust. Instead:

> **"You consistently treat percentage change as absolute change."**

That is a diagnosis rather than a score, and it is what good human tutors actually
provide: noticing the specific broken mental model once, instead of re-explaining
the surface repeatedly.

## Why retrieval survives here

Retrieval becomes obsolete when a corpus **fits** in context, is **static**, and is
**queried by a typed question**. A textbook fails on all three. The user's own
accumulated record of being wrong fails none of them:

- **It never fits.** It grows without bound for as long as the system is used.
- **Summarizing it destroys the signal.** "Struggled with elasticity" discards the
  thing that matters — *how* they were wrong, and that it recurred.
- **It is not queried by a question.** It is queried by concept, by error shape, and
  by time — never by a sentence someone typed.
- **It exists nowhere else.** Not in any model's weights, not in any textbook.

Finding a pattern across months of mistakes on topics that do not look related is
work no context window can absorb. That is the one job in this product where
retrieval is the product rather than the plumbing.

## V1.5 Milestones

| M | Status | Deliverable |
|---|--------|-------------|
| 10 | ⬜ next | **Practice loop** — migration 0007 (`practice_sessions`, `practice_attempts`); quiz and explain-back modes in `pks/tutor/`; every attempt stored with the learner's full answer text and the source passage it was graded against; assessment added to the chat output contract; fast tier moved to `claude-sonnet-5` |
| 11 | ⬜ | **UI revamp** — move the interface from generic dashboard to study environment: reading-first typography, material centered rather than sidebarred, deliberate palette and dark mode, task-organized navigation |
| 12 | ⬜ gated | **Misconception detection** — embed stored attempts, cluster them into candidate misconceptions, surface each pattern *only* alongside the specific instances that support it |
| 13 | ⬜ | **Material coverage** — EPUB parser, OCR for scanned PDFs |

### Why the UI milestone sits in the middle

M12 needs weeks of accumulated mistakes before it can find anything. Rather than
wait idle, the UI work runs during that window — and it banks a guaranteed
improvement before the uncertain one is attempted. If M12 produces nothing, V1.5
still shipped a materially better product.

### M10 success gate

Two weeks of the author's own use, **with ChatGPT plus the same textbook as the
control condition.** Measure retention after seven days, and adherence — whether
returning to it required force.

M12 additionally requires enough real error data to cluster. If a month of use
produces no recurring pattern worth surfacing, M12 ships as nothing and the line of
work stops there. One milestone lost, not a quarter.

### Design constraints

- **No mastery percentages.** Confidence scores derived from sparse conversational
  evidence are theatre. Show the instances, not a number.
- **Never assert a pattern without its evidence.** A wrong diagnosis about someone's
  own thinking is worse than silence. Below threshold, the feature says nothing.
- **Degrade to nothing, gracefully.** M12 must be invisible rather than wrong when
  data is thin.

### Notes on model tiers

The fast tier moves to `claude-sonnet-5` in M10 for one documented reason: the M6
note in [TODO.md](TODO.md) records that Haiku's grounding is imperfect — a cited
claim can misread its source. Grading a learner's answer against a source passage is
exactly where that defect does real damage. Ingestion stays on the heavy tier.

Provider cost is deliberately not a design input. At single-user scale the spread
between the cheapest and most expensive credible model is a few dollars a month.

---

## Explicitly not doing

Course libraries · curated curricula · subscriptions · content licensing · App Store
distribution · cloud deployment · multi-user · prerequisite graphs · learner
confidence models · spaced-repetition scheduling · a "teach me" mode

These are recorded as declined rather than pending. Several were proposed, examined,
and cut for reasons documented above; re-proposing them should require new evidence.

## Parked (not scheduled)

- **Assistant platform API** — external assistants consuming the Core Knowledge
  Engine. Serves the knowledge-infrastructure thesis rather than the learning one.
- **Desktop packaging (Tauri)** — plausible endpoint for personal use.
- **Hosted deployment (Postgres + auth)** — implies a commercial product; not
  decidable before M10's gate.
- **Remaining parsers** — DOCX, web page (URL).
- **Additional providers** — Gemini, OpenAI, local via Ollama, Voyage embeddings.
- **Cross-type entity reconciliation** — e.g. "Rome" typed place vs. organization
  across runs; dedup deliberately will not merge across types.
- **Retry backoff for pipeline jobs; chunk overlap experiment for retrieval.**
- **Cost and token telemetry** — worth doing if usage ever justifies it.

**Removed:** per-stage resource usage capture (RAM / CPU / storage).
