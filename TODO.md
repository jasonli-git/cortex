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

## Milestone 10 — Tutor loop  ← current

Thesis and rationale: [ROADMAP.md](ROADMAP.md) "V2 — Interactive Learning".

### Schema (migration 0007)

- [ ] `study_sessions` — conversation/workspace/resource refs, mode, focus concept,
      started/ended, carry-forward summary
- [ ] `understanding_events` — append-only evidence: concept, kind
      (recalled/applied/explained/missed/hinted/confused), outcome 0..1, difficulty,
      evidence chunk, detail JSON
- [ ] `understanding_state` — derived cache (confidence, evidence_count, last_seen_at,
      due_at, computed_from). Must be safe to DELETE and rebuild from events
- [ ] Domain models + repositories + engine API, mirroring the existing
      provenance/versioning patterns
- [ ] Leave `learning_events` (0006) alone — it stays the *activity* log

### Tutor service (`pks/tutor/`)

- [ ] Module composes ChatService + KnowledgeEngine + SearchService (dependency rule:
      modules import `core.engine`, never each other)
- [ ] **Teach** — tutor opens; one explanation step grounded in the focus concept's
      chunks, then a checking question; reply scored → recalled/missed
- [ ] **Quiz** — question drawn from a specific chunk, verdict graded against that same
      chunk; records applied/missed with `evidence_chunk_id`
- [ ] **Explain back** — learner explains, tutor grades on a rubric (accuracy /
      completeness / own-words) naming the missing piece with a citation; records
      `explained` + rubric. Highest-signal mode; must refuse a fluent wrong answer
- [ ] Extend `CHAT_SCHEMA` with an `assessment` block — keep the existing
      segment/citation contract so unbacked `pks` segments still downgrade to `model`
- [ ] Session summary written at session end, injected into the next session's prefix

### Model tier

- [ ] `fast_model` → `claude-sonnet-5` (rationale: M6 note below — Haiku mis-grounding
      is a citation defect in a knowledge tool and a teaching-something-false defect
      in a tutor). Heavy tier unchanged
- [ ] Confirm no prompt regressions in existing chat after the tier change

### Frontend

- [ ] Study view: mode switcher, focus-concept selector, session transcript
- [ ] Assessment feedback rendered inline (verdict + the chunk it was graded against)

### Exit criterion (not optional)

- [ ] Two weeks of the author's own use against the ingested economics textbook,
      answering: *is talking to my material meaningfully better than reading it?*
      M13 and everything past it stay unscheduled until this is a yes.

## Deferred into later V2 milestones

- M11: confidence estimator, `prerequisite_of` extraction, weak-spot traversal,
  spaced review, "why does Cortex think I know this?" panel
- M12: per-turn token/cost logging, prompt caching on the session prefix, grounding
  eval across tiers — this absorbs the old "heavy-tier chat mode or grounding
  verification pass" candidate
- M13 (gated): EPUB parser, OCR, Gemini provider

Longer-horizon and parked items: [ROADMAP.md](ROADMAP.md) "Parked".

## Parked / needs user input

- Anthropic API key required before Milestone 3 (`ANTHROPIC_API_KEY`)
- Node.js required before Milestone 8 (frontend scaffold)
