# Cortex — Architecture

This document describes the system architecture for Cortex, an AI Personal Knowledge System.
The product specification lives in [SPEC.md](SPEC.md) and is the source of truth for *what*
the system does; this document records *how* it is built and *why*.

## System Shape

A **local-first, single-user web application**:

- A Python backend runs on the user's machine (one command to start).
- The UI is a React app served to the browser.
- All data lives locally: a SQLite database plus an on-disk resource store.
- The only external dependency is the AI provider API (Anthropic by default).

This can later be packaged as a desktop app (Tauri) or moved to a hosted deployment
(Postgres + auth) without architectural change, because all storage sits behind
repository interfaces and all AI calls sit behind provider interfaces.

## Decisions Log

| # | Decision | Rationale |
|---|---|---|
| 1 | Local-first web app | Personal system: private, free to run, simplest to build. Deployment can evolve later. |
| 2 | Python 3.12 + FastAPI backend, React + TypeScript frontend | Python has the strongest document-parsing and AI ecosystem; ingestion is the heart of the system. Clean REST boundary between the two. |
| 3 | SQLite + FTS5 (keyword) + float32-BLOB vectors compared with numpy | One file, zero ops, transactional. sqlite-vec was considered and deferred: it is also a linear scan internally, so at personal scale it buys little while requiring a native extension loaded on every connection. `EmbeddingIndex` is the seam where sqlite-vec/pgvector slot in if scale demands. |
| 4 | Durable job queue in the database + in-process async worker | Pipeline stages are event-driven and restart-safe without Redis/Celery. The event *interface* is stable; the transport is replaceable (spec principle 9). |
| 5 | AI provider abstraction; Anthropic default | Heavy tier `claude-opus-4-8` for ingestion-time extraction, fast tier `claude-haiku-4-5` for chat — both config-driven. Spec principle 6: providers are infrastructure. |
| 6 | Local embeddings (sentence-transformers) by default | Free, offline, private; Anthropic has no embeddings API. Swappable for Voyage/OpenAI via `EmbeddingProvider`. |
| 7 | Single-user, no auth in V1 | It is a *personal* knowledge system. The API layer is the seam where auth would be added. |
| 8 | Knowledge-object versioning = revision history | Every mutation snapshots the prior state (`ko_versions`). No branching. |
| 9 | V1 ingestion formats: PDF (text-based), Markdown, plaintext, in-app notes | Spec non-goal: "not every file type". EPUB / web / DOCX / OCR are future parser modules. |
| 10 | Learning analytics: schema groundwork only | Spec: evidence-based confidence model "not required for Version 1". |

## Module Layout

```
cortex/
├── backend/
│   ├── pks/
│   │   ├── core/            # CORE KNOWLEDGE ENGINE — the product
│   │   │   ├── models.py    #   domain objects: KnowledgeObject, Relationship, Provenance…
│   │   │   ├── store/       #   repositories + migrations (SQLite impl behind interfaces)
│   │   │   └── engine.py    #   the one public interface every module consumes
│   │   ├── events/          # event bus + durable job queue
│   │   ├── ingestion/       # resource intake, parsers (pdf, md, txt, note), chunking
│   │   ├── extraction/      # LLM stages: structure, concepts/entities/events, summaries
│   │   ├── embeddings/      # EmbeddingProvider impls + vector index management
│   │   ├── graph/           # relationship builder, dedup/merge
│   │   ├── search/          # hybrid retrieval (vector + FTS + graph expansion)
│   │   ├── chat/            # RAG conversation service with source attribution
│   │   ├── workspaces/
│   │   ├── providers/       # CompletionProvider abstraction (anthropic, …)
│   │   └── api/             # FastAPI routers (thin; no business logic)
│   └── tests/
├── frontend/                # React + TypeScript + Vite (scaffolded in Milestone 8)
└── SPEC.md ARCHITECTURE.md ROADMAP.md TODO.md CHANGELOG.md
```

**Dependency rule:** modules never import each other — they import `core.engine` and
communicate through events. The engine has no knowledge of PDFs, prompts, or HTTP.

## Core Knowledge Engine

Responsible for (per spec): storing knowledge, indexing, maintaining relationships,
semantic retrieval, metadata, provenance, versioning.

### Database schema (core tables)

```
resources          id, type(pdf|markdown|text|note), title, path, content_hash,
                   status(pending|processing|ready|failed),
                   relationship(active_learning|reference), metadata
resource_chunks    id, resource_id, ordinal, structure_path ("Ch 3 > §2"), text, token_count
knowledge_objects  id, type(concept|person|organization|place|event|summary), name,
                   description, aliases, metadata, version, created_at, updated_at
ko_versions        knowledge_object_id, version, snapshot, changed_by(stage), created_at
relationships      id, from_ko, to_ko, type(related_to|part_of|participated_in|…),
                   confidence, created_by(stage)
provenance         knowledge_object_id | relationship_id, resource_id, chunk_id, quote_span
embeddings         owner_type(chunk|knowledge_object), owner_id, model, vector   (sqlite-vec)
search_index       FTS5 virtual table over chunks + knowledge object names/descriptions
workspaces         id, name, description
workspace_refs     workspace_id, object_type(resource|knowledge_object|conversation), object_id
conversations      id, workspace_id?, title
messages           conversation_id, role, content, citations JSON
                   — each claim tagged {source: pks|model, refs: […]}
jobs               durable pipeline state: type, payload, status, attempts, error
```

Key properties encoded by the schema:

- Knowledge exists independently of resources; **provenance** links every knowledge
  object and relationship back to the evidence (resource + chunk + quote).
- **Workspaces reference, never own** — `workspace_refs` is a pure overlay.
- **Versioning** — `ko_versions` snapshots each prior state of a knowledge object.
- **Transparency** — chat citations distinguish Cortex knowledge from model knowledge.

## Ingestion Pipeline

Event-driven, per the spec's architecture diagram. Each stage is an independent,
retryable job; a failure pauses that resource, not the system.

```
resource.uploaded
  → parse            (text + native structure; per-format parser modules)
  → chunk            (structure-aware chunking)
  → extract_structure (LLM: chapters/sections/periods)
  → summarize        (per-section + whole-resource)
  → extract_entities (LLM: concepts, people, orgs, events — with quotes for provenance)
  → dedupe           (embedding similarity + LLM-confirmed merge into existing KOs)
  → build_relationships
  → embed
  → index            (FTS + vector)
```

Heavy models run only in this pipeline ("expensive reasoning happens once");
chat and search assistance use the fast tier.

Concrete stage chain (V1): `parse → chunk → extract_knowledge → summarize → index →
dedupe`, with `index` (embeddings + FTS) marking the resource ready and `dedupe`
refining the graph afterwards. Without an API key the AI stages are absent and
`index` follows `chunk` directly — parsing, chunking, and search all work AI-free.

Resources can be **reprocessed** (`POST /api/resources/{id}/reprocess`): the pipeline
re-runs from the stored original; chunks and indexes are rebuilt while knowledge and
provenance stay stable (extraction merges by name/alias, and provenance rows keyed by
(resource, quote) are re-pointed at the new chunks rather than duplicated). The global
job queue is observable at `GET /api/jobs`.

One known behavior: an ambiguous entity ("Rome" the city vs. the state) can be typed
differently across runs, producing same-name siblings of different types. The dedup
stage deliberately never merges across types; reconciling these is post-V1 work.

## Learning evidence (groundwork)

Per the spec's Learning Philosophy, V1 only *accumulates evidence*: `learning_events`
records resource ingests, notes written, and questions asked (via
`engine.record_learning_event`). The confidence model that interprets this evidence
is future work.

## Search

Hybrid retrieval fused with reciprocal-rank fusion (RRF), which avoids
calibrating cosine similarity against BM25 scores:

- **Semantic**: local sentence-transformers embeddings (chunks + knowledge
  objects), stored as float32 BLOBs, cosine via numpy.
- **Keyword**: FTS5 tables over chunk text and knowledge object
  names/aliases/descriptions, ranked by BM25.

Indexes are maintained by the `index` pipeline stage (explicit and retryable,
not triggers); stale entries for deleted objects are skipped at query time.

## AI Strategy

- `CompletionProvider` interface: `complete()` and schema-constrained
  `extract_structured()`. Default implementation: Anthropic SDK.
- Two configured tiers: `heavy` (ingestion/extraction, default `claude-opus-4-8`)
  and `fast` (chat/navigation, default `claude-haiku-4-5`).
- `EmbeddingProvider` interface. Default: local sentence-transformers model.
- All extraction uses structured outputs (JSON-schema-constrained) so pipeline
  stages receive validated data, not prose.
- Every chat answer labels each claim's origin: the user's Cortex knowledge (with citations) vs.
  general model knowledge (spec principle 7).
