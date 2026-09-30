# Cortex — TODO

Open work only. Shipped detail lives in [CHANGELOG.md](CHANGELOG.md), decisions and
limitations in [ARCHITECTURE.md](ARCHITECTURE.md), milestone status in
[ROADMAP.md](ROADMAP.md).

## Now — M14 in review, as of 2026-09-30

M14 (cleanup) is complete on `milestone/m14-cleanup` and awaiting review and merge.
Next is M15; don't start it until M14 is merged.

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

### M20 — Citation binding (runs after M15, before M16)

Model: housing-intelligence's binding (`hip.packets.citations`, decisions #112, #114,
#116, #263, #266). One deterministic checker — never a language model — is both the
publication gate and the evaluation's metric.

- [ ] `CHAT_SCHEMA` segments gain a `quote` (verbatim, ≤ 25 words) from the cited source
      for every `pks` segment
- [ ] Sources rendered to the model and sources bound against are the same text (today
      the prompt gets the first 1,200 chars of a chunk but the citation names all of it)
- [ ] `pks/chat/binding.py`: locate each quote in its cited passage — exact, then
      normalized (whitespace, curly quotes, dashes, hyphenation); record segment → chunk,
      resource, resource version, character span, match method
- [ ] Figure binding: every number, amount, duration, percentage, and date in a `pks`
      segment must appear in its bound passage; whole-token matching, years exact
- [ ] Unbound segment handling: personal mode downgrades to `model`; documents-only
      mode (M17) sends one revision call quoting the refusal reasons, then refuses with
      the contact pointer
- [ ] Bindings persisted on the message with `BINDING_VERSION`; bumping it re-binds
      stored answers for free
- [ ] Re-binding on document change: stored answers are re-bound against the new
      version by quote search; answers whose quotes no longer exist are marked as citing
      a superseded version (feeds M17's flag)
- [ ] Extraction provenance quotes verified against their chunk at ingest; unverifiable
      quotes are dropped or flagged, not stored as evidence
- [ ] Evaluation runner reports bound rate per model alongside the model-graded claim
      support score
- [ ] UI: citation click opens the passage with the bound span highlighted
- Note: binding checks quotes and figures, not claims — a correct quote under a wrong
  paraphrase passes. Claim support stays a model-graded evaluation score, not a gate
  (same line housing drew in #112). Record in ARCHITECTURE when M20 ships.

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
- Note: the resource `relationship` value `active_learning` predates SPEC v2.0's
  "active use" wording; renaming it (migration + frontend type) is optional (noted
  during M14)
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
