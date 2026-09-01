# Cortex — TODO

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
- [x] Per-segment source labels: Cortex (validated citations) vs. model knowledge
- [x] Conversations/messages persistence (migration 0004) + API
- [x] Conversation context window management (recent turns)
- Note: fast-tier (Haiku) grounding is imperfect — a cited claim can still misread
  its source. Citations make this checkable; consider a heavy-tier chat option or
  a verification pass post-V1.

## Milestone 7 — Workspaces + notes

- [x] Workspaces table (migration 0005) + engine/API CRUD
- [x] Workspace refs: attach/detach resources, knowledge objects, conversations
- [x] Upload/note endpoints accept workspace_id (ingest straight into a workspace)
- [x] Workspace scoping for chat retrieval and /api/search

## Milestone 8 — Frontend

- [x] Vite + React + TypeScript + Tailwind scaffold (Node installed via brew)
- [x] Library: resources, upload with pipeline progress, notes, chunk viewer
- [x] Search page (knowledge + passages)
- [x] Knowledge detail with provenance, relationships, history
- [x] Graph view (cytoscape, click-through to detail)
- [x] Chat with Cortex/model segment labels + citations; workspace selector
- [x] Workspaces management (create/delete, contents, detach)
- Nits for M9: upload-into-workspace from the Library UI; graph layout spreads
  small graphs tightly (cose params); TYPE_COLORS export triggers a fast-refresh
  lint warning

## Milestone 9 — Hardening

- [x] Resource reprocessing with stable knowledge/provenance
- [x] Pipeline observability (GET /api/jobs + Pipeline page)
- [x] Learning-evidence groundwork (migration 0006 + recorder, wired at intake/chat)
- [x] Docs polish (README, ARCHITECTURE)
- [x] Frontend nits from M8 (workspace-targeted upload, graph layout, lint)

## Milestone 10 — Practice loop  ← current

Thesis, scope rationale, and design constraints: [ROADMAP.md](ROADMAP.md) "V1.5 —
Practice & Diagnosis".

### Schema (migration 0007)

- [ ] `practice_sessions` — conversation / workspace / resource refs, mode
      (quiz | explain), focus concept, started_at, ended_at
- [ ] `practice_attempts` — the corpus M12 depends on. One row per graded exchange:
      session, knowledge object, mode, the **question asked**, the learner's
      **full answer text** (not a boolean), the verdict, and the
      `evidence_chunk_id` it was graded against
- [ ] Domain models + repositories + engine API, mirroring existing
      provenance/versioning patterns
- [ ] Leave `learning_events` (0006) alone — it stays the *activity* log
- [ ] No `understanding_state` table. Confidence modelling is explicitly out of scope

### Practice service (`pks/tutor/`)

- [ ] Module composes ChatService + KnowledgeEngine + SearchService (dependency
      rule: modules import `core.engine`, never each other)
- [ ] **Quiz** — question drawn from a specific chunk; verdict graded against that
      same chunk; stores question, answer, verdict, evidence chunk
- [ ] **Explain back** — learner explains a concept; graded on a short rubric
      (accuracy / completeness / own words) naming the missing piece with a
      citation. Must refuse a fluent wrong answer
- [ ] No "teach me" mode — cut deliberately, see ROADMAP
- [ ] Extend `CHAT_SCHEMA` with an `assessment` block; keep the existing
      segment/citation contract so unbacked `pks` segments still downgrade to `model`

### Model tier

- [ ] `fast_model` → `claude-sonnet-5` (rationale: M6 note above). Heavy tier unchanged
- [ ] Confirm no regressions in existing chat after the tier change

### Frontend (minimal — real UI work is M11)

- [ ] Practice view: mode switcher, focus-concept selector, session transcript
- [ ] Verdict rendered inline with the passage it was graded against

### Chore

- [ ] CI workflow running `uv run pytest` (99 tests currently unproven publicly)

### Success gate

- [ ] Two weeks of the author's own use, **with ChatGPT + the same textbook as the
      control condition**. Measure 7-day retention and adherence (did returning
      require force?)
- [ ] Confirm enough real error data accumulated to attempt M12's clustering

## Milestone 11 — UI revamp

- [ ] Reading-first typography; material centered rather than sidebarred
- [ ] One deliberate typeface pairing and palette; intentional dark mode
- [ ] Task-organized navigation (study first; graph, pipeline, history reachable
      but not competing for primary attention)
- [ ] Target: the screenshot reads as a study tool with no caption

Kept as first-class pages per user decision: **Workspaces** (name unchanged) and
**Pipeline observability**.

## Milestone 12 — Misconception detection  (gated on M10)

- [ ] Embed `practice_attempts` answer text into the existing vector index
- [ ] Cluster attempts into candidate misconceptions across unrelated topics
- [ ] Surface a pattern only with the specific supporting instances; below
      threshold, show nothing
- [ ] No mastery percentages anywhere in the UI

## Milestone 13 — Material coverage

- [ ] EPUB parser
- [ ] OCR for scanned PDFs

Longer-horizon, declined, and parked items: [ROADMAP.md](ROADMAP.md).

## Parked / needs user input

- Anthropic API key required before Milestone 3 (`ANTHROPIC_API_KEY`)
- Node.js required before Milestone 8 (frontend scaffold)
