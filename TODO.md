# Cortex — TODO

Open work only. Shipped detail lives in [CHANGELOG.md](CHANGELOG.md), decisions and
limitations in [ARCHITECTURE.md](ARCHITECTURE.md), milestone status in
[ROADMAP.md](ROADMAP.md).

## Now — M14 Cleanup, as of 2026-09-30

Roadmap rescoped 2026-09-30: V1.5 (tutoring) dropped, V2 (cost, reliability, polish)
planned. Nothing started on M14 yet; begin on a `milestone/m14-cleanup` branch.

- [ ] Migration 0007 drops `learning_events`; `LearningEvent` model, repository,
      `engine.record_learning_event` / `list_learning_events` removed
- [ ] Recorder call sites removed from `pks/ingestion/intake.py` and
      `pks/chat/service.py`
- [ ] Learning-event tests removed from `test_hardening.py`; full suite passing
- Note: the resource `relationship` field (`active_learning | reference`) is not
  learning-event code — SPEC v2.0 keeps "active use vs. passive reference". Kept;
  renaming `active_learning` is optional and belongs in M17 config cleanup
- [ ] ARCHITECTURE decision row 10 superseded: learning analytics dropped, with pointer
      to the archived V1.5 plan
- [ ] CI workflow running `uv run pytest` and the frontend lint/build

## Open

### M15 — Cost visibility + evaluation

- [ ] Provider returns token usage (input, output, cache read, cache write) alongside
      every result; `AnthropicProvider` reads it from `response.usage`
- [ ] Usage persisted per call with stage, resource, conversation/message, model, and
      tier (new migration)
- [ ] Per-model price table in config; estimated USD computed at read time, not stored
- [ ] Cost per resource and per pipeline stage on the Pipeline page and resource
      detail; cost per chat message available in the API
- [ ] Demo corpus: a clearly fictional therapy clinic's handbook (onboarding, records
      system, supervision, time off, documentation deadlines, crisis procedures, billing
      basics), committed as the reference corpus alongside 1–2 personal-use documents
- [ ] Question set: 30–50 realistic new-hire questions with expected answer and source
      section, including questions the handbook deliberately does not answer
- [ ] Evaluation runner scoring accuracy, citation faithfulness (does the cited passage
      support the claim), and correct refusal; results written to a report file
- [ ] Unanswered-question log: every answer with no grounded segment is recorded;
      a gap report groups similar questions by embedding and counts repeats
- [ ] Top-asked questions and cost per question visible to the document owner
- [ ] Baseline cost and question-set scores recorded
- [ ] Model candidate evaluation on the reference corpus, per tier: current
      `claude-opus-4-8` (heavy) and `claude-haiku-4-5` (fast) vs. newer Opus models and
      other candidates; pick per-stage models on quality first, cost second. The
      winners become the baseline M16 is measured against

### M16 — Cost reduction, quality held

- [ ] Prompt caching on the stable prefix of every call (system prompt + JSON schema)
      for extraction, summary, dedup, and chat
- [ ] Summary derived in the extraction pass, so the full document text is sent to the
      heavy model once instead of twice (today `extract_batch` and `summarize` each
      read every chunk)
- [ ] Extraction cache keyed by chunk text hash + prompt version + model: reprocessing
      an unchanged chunk reuses its prior result instead of calling the model
- [ ] Dedup confirmations batched: several candidate pairs judged in one heavy-tier
      call instead of one call per pair (`pks/graph/dedup.py`)
- [ ] Opt-in "economy" ingestion via the Message Batches API for bulk uploads, with the
      Pipeline page showing the batch as pending
- [ ] Prompt and output-schema trimming; chat retrieval breadth
      (`chat_context_chunks`, `chat_context_objects`, `chat_history_limit`) tuned
      against the reference question set
- [ ] Before/after report on the reference corpus: cost delta and quality check (M16
      success gate in ROADMAP)
- Note: fast-tier (Haiku) chat grounding is imperfect — a cited claim can still misread
  its source. The M15 model evaluation must score chat candidates on citation
  faithfulness, not just answer quality.

### M17 — Reliability + trustworthy answers

- [ ] Documents-only answer mode (per workspace): `model` segments are not allowed; when
      retrieval does not support an answer, reply that the documents don't cover it and
      name the contact configured for that workspace or document
- [ ] Document versions: re-uploading a document with the same title in a workspace
      supersedes the old version; retrieval uses the current version only; citations
      show version and effective date; unchanged chunks reuse cached extraction (M16)
- [ ] Past answers that cite a superseded version are flagged in the UI

- [ ] Retry backoff for pipeline jobs (currently immediate retries)
- [ ] Provider and pipeline failures show a user-readable reason on the resource and
      Pipeline page, not the raw exception string stored in `jobs.error`
- [ ] Config reduced to the settings a user actually changes; the rest become constants
- [ ] Duplicated logic consolidated (audit extraction/chat/search for repeated helpers)
- [ ] Provenance integrity check: every citation and knowledge object resolves to an
      existing chunk after reprocessing and merges

### M18 — UI polish

- [ ] Standalone assistant page: one question box, cited answers, citation click opens
      the source passage; no library/graph/pipeline chrome. The primary demo surface

- [ ] Navigation and information hierarchy reworked around Library, Search, Graph, Chat;
      Workspaces and Pipeline reachable but secondary
- [ ] One consistent type scale, spacing, and palette across pages; intentional dark mode
- [ ] Empty, loading, error, and processing states on every page
- [ ] Graph readability: labels, type filtering, neighborhood focus, sane layout on
      small and large graphs
- [ ] Chat citations visually tied to source passages; Cortex vs. model segments clear
- [ ] Responsive down to tablet width where practical

### M19 — Completion

- [ ] Scripted end-to-end demo on the fictional clinic handbook: upload → assistant page
      answers with citations → an unanswered question → gap report → policy re-upload
      changes the answer
- [ ] Evaluation results published in README
- [ ] Screenshots refreshed in `screenshots/`
- [ ] README, ARCHITECTURE, and supported-formats/AI-pipeline docs match the final code

## Parked / needs user input

- **Model candidates for M15.** Newer Opus models are confirmed candidates; the rest of
  the candidate list (other tiers, other providers) is still to be decided.
