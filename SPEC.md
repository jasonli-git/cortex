# Cortex Specifications
## Product Specification v2.0 (2026-09-30)

### Vision

Build Cortex, a modular AI-powered Personal Knowledge System that functions as a user’s long-term knowledge operating system.

The purpose of the application is not to replace ChatGPT, Claude, or future frontier models. Instead, it exists to organize, preserve, connect, and retrieve a user’s accumulated knowledge across years of learning, projects, work, and personal interests.

The system should transform unstructured information—including documents, books, notes, conversations, code snippets, websites, and future knowledge sources—into structured, interconnected knowledge that can be searched, explored, reasoned over, and expanded by AI.

Cortex should prioritize long-term knowledge accumulation rather than short-term question answering.

The application should be designed as a platform rather than a single-purpose application, allowing future AI assistants and modules to build upon the same knowledge layer without requiring architectural changes.

For the current version, Cortex should be **a small, polished knowledge system that is pleasant to explore and inexpensive to use.** It serves two uses of the same engine:

* **Personal knowledge** — one person's accumulated material, explored through search, the graph, and chat.
* **Document assistant** — a team's policies, handbooks, and procedures, answered for people who ask the same questions repeatedly (for example, new hires asking onboarding questions that staff would otherwise answer by email).

The document assistant is the primary demonstration of Cortex. Its core workflow is the same:

```
Material → ingestion → structured knowledge → search / graph exploration → grounded AI interaction
```

Existing capabilities should be improved rather than substantially expanded. New features should only be added when they materially improve the existing experience without significantly increasing operating cost or architectural complexity.

---

### Core Principles

#### 1. Knowledge is the primary object.

The system is fundamentally about knowledge—not documents.

PDFs, EPUBs, notes, conversations, videos, web pages, code repositories, and future data sources are simply inputs that contribute to a structured knowledge base.

Knowledge should exist independently of the source from which it originated.

#### 2. Resources are evidence, not the destination.

Documents should never remain isolated files.

Every uploaded resource should be transformed into structured knowledge through automatic processing.

Examples include:
+ document hierarchy
* concepts
* entities
* events
* timelines
* relationships
* summaries
* metadata
* citations

The original resource should always remain available for reference.

#### 3. Knowledge should accumulate permanently.

The application should continuously grow smarter about the user’s knowledge over time.

Every interaction—including uploads, notes, conversations, highlights, decisions, and projects—should contribute to a persistent knowledge base.

The application should minimize repeated work by remembering previous context.

#### 4. Everything should be connected.

Knowledge should exist as an interconnected network rather than isolated folders.

Concepts should automatically relate to:

* other concepts
* people
* organizations
* projects
* notes
* documents
* conversations
* code
* learning topics

Relationships should be continuously improved as additional information is added.

#### 5. The system should reduce organization effort.

Manual organization should be optional.

The application should automatically:

* categorize
* summarize
* tag
* relate
* index
* de-duplicate

Users should organize only when they want additional control.

#### 6. AI providers are infrastructure, not the product.

The value of Cortex should not depend on whether it uses GPT-5.5, Claude, Gemini, or a local model.

The AI should be replaceable.

The knowledge layer is the product.

#### 7. AI should be transparent.

Every AI-generated response should clearly distinguish between:

* knowledge retrieved from the user’s Cortex knowledge base
* general model knowledge
* external sources (future capability)

Users should always understand where information originated.

In the document assistant, answers must come from the documents only. When the documents do not answer a question, the assistant should say so plainly and point to who can answer it, rather than filling the gap from general model knowledge.

#### 8. Expensive reasoning should happen once.

Complex AI processing should occur primarily during ingestion.

After ingestion, knowledge should already be structured sufficiently to allow fast retrieval and conversation using smaller or faster models when appropriate.

#### 9. Modularity is mandatory.

Every major capability should exist as an independent module.

Examples include:

* ingestion
* embeddings
* search
* graph generation
* summarization
* future assistants

Modules should communicate through stable interfaces and should be replaceable without affecting the rest of the application.

#### 10. Cost should be low without lowering quality.

Cortex should be cheap enough for occasional personal use, and its processing costs should be predictable.

Cost should be reduced by doing less work, not by doing worse work:

* avoid unnecessary model calls
* never reprocess unchanged material
* cache reusable outputs and stable prompt content
* batch extraction and processing when possible
* keep prompts and retrieved context small
* keep embeddings and deterministic processing local where they provide value without recurring cost

Model choice should follow measured output quality. A stage should not move to a weaker model to save money unless its output quality is shown to hold.

Approximate processing costs should be visible to the user.

---

### User Experience

The application should feel less like “chat with my PDFs” and more like a personal knowledge workspace.

The primary interactions should be:

* upload resources
* write notes
* search knowledge
* chat with accumulated knowledge
* browse relationships
* manage workspaces
* ask a question through a single, simple assistant page

Users should never feel required to manually organize every piece of information.

Instead, the application should perform background processing on the material the user adds to maintain an organized knowledge base.

For example, uploading an American History textbook should not simply create embeddings.

Instead, the system should automatically recognize:

* chapters
* sections
* historical periods
* important people
* major events
* timelines
* related concepts

These should become structured knowledge objects linked throughout the rest of the knowledge base.

___

The application should support both active use and passive reference.

Examples:

“I am currently studying American History.”

vs.

“I own this textbook and want it available for future reference.”

These represent different relationships with the same resource and should influence how the system surfaces information.

---

The application should support workspaces.

A workspace represents a context in which knowledge is used.

Examples include:

* learning American History
* building an AI application
* career development
* investing
* photography

A workspace should not own knowledge.

Instead, it references relevant knowledge objects while allowing the same knowledge to appear across multiple workspaces.

Knowledge should never require duplication.

---

### Philosophy of RAG

Retrieval-Augmented Generation exists to provide personal context rather than replace the language model’s general knowledge.

The purpose of RAG is not to make the AI smarter.

Its purpose is to allow the AI to reason using the user’s accumulated knowledge.

When answering questions, the system should prioritize:

1. user knowledge
2. general model knowledge
3. external information (future)

The system should make these distinctions explicit.

The application should avoid functioning as merely another “chat with your documents” interface.

Instead, documents should become raw material for building a persistent knowledge layer.

The primary value proposition is knowledge accumulation rather than document retrieval.

---

### Grounding and Provenance

Answers that depend on the user's material should clearly reference that material.

Every AI-generated claim drawn from Cortex should link back to the specific source passage it came from, and that link should survive reprocessing and de-duplication.

When a document is replaced by a newer version, answers should come from the current version, and cited sources should show which version and effective date they came from. Answers given against an older version should be identifiable as such.

Questions the documents could not answer should be recorded and grouped, so the owner of the documents can see which repeated questions still need a written answer.

Answer quality should be measured, not asserted: a fixed set of realistic questions, with expected answers and sources — including questions the documents deliberately do not answer — should score accuracy, citation faithfulness, and correct refusal.

Cortex does not model what a user understands. Tutoring, quizzes, mastery scoring, and learner models are out of scope (see Non-Goals).

---

### Architecture Philosophy

The application should be centered around a Core Knowledge Engine.

The Core Knowledge Engine is responsible for:

* storing knowledge
* indexing knowledge
* maintaining relationships
* semantic retrieval
* metadata
* provenance
* versioning

Everything else should be built around this engine.

The application should use an event-driven modular architecture.

Example:
```
Document Uploaded

↓

Document Parser

↓

Knowledge Extraction

↓

Summarization

↓

Entity Extraction

↓

Relationship Builder

↓

Embedding Generator

↓

Duplicate Detection

↓

Knowledge Graph

↓

Search Index
```
---

The application should distinguish between heavy processing and lightweight interaction.

Heavy AI models should perform:

* ingestion
* structure extraction
* relationship discovery
* quality verification

Fast models should perform:

* conversation
* summarization
* search assistance
* navigation

This separation improves both cost and responsiveness.

---

Future AI assistants should consume knowledge from the Core Knowledge Engine rather than maintaining separate memory systems.

Cortex should become the shared intelligence layer for future applications.

---

### Long-Term Product Direction

Cortex should not attempt to become every AI application.

Instead, it should become the foundational knowledge platform upon which future specialized assistants can operate. In other words, the objective is to build the best possible knowledge engine.

Examples include:

* AI Research Assistant
* AI Coding Assistant
* Agentic Job Search Assistant
* Decision Support Assistant

Each assistant should reuse the same knowledge base rather than maintaining separate memories.

This direction is not part of the current version. It constrains the architecture (the knowledge layer stays reusable) without adding scope.

---

### Non-Goals (Version 1)

Version 1 should not attempt to:

* perfectly model human understanding
* replace frontier language models
* automatically complete complex projects
* become an autonomous agent
* support every file type
* solve every knowledge-management workflow

Instead, Version 1 should focus on building a robust, modular knowledge foundation that can be expanded over time.

### Non-Goals (Version 2)

Version 2 should not attempt to add:

* tutoring modes
* quizzes or explain-back workflows
* mastery or confidence scoring
* learner models or prerequisite tracking
* spaced repetition
* automated study plans
* additional document formats solely for feature breadth
* continuous or autonomous ingestion
* expensive always-on AI functionality
* user accounts, logins, or per-user permissions — the assistant page runs without authentication for demonstration

These may remain in archived plans or documentation but should not drive development.

---

### Completion Criteria

Cortex is complete when:

* the primary UI feels polished and visually consistent
* ingestion works reliably for the supported formats
* search and graph exploration are intuitive
* grounded AI responses clearly reference their source material
* unnecessary model calls have been removed or reduced
* processing costs are predictable and reasonable for occasional personal use
* obsolete roadmap functionality has been removed or explicitly archived
* documentation accurately reflects the final product
* the project can be demonstrated end-to-end without significant ongoing maintenance
* the document assistant is demonstrated on a clearly fictional organization's handbook, with published evaluation results

---

### Changes in v2.0 (2026-09-30)

#### 1. Rescoped from expansion to completion

**Previous idea:** Cortex would grow into interactive learning — a practice partner with quizzes, explain-back, and misconception detection.

**Current version:** Cortex stays a personal knowledge system. The priority is polish, cost, and reliability of the existing workflow.

**Reason:** A finished, pleasant, inexpensive system is a better outcome than a broader unfinished one.

#### 2. Removed the Learning Philosophy

The evidence-based learning model, "review learning" as a primary interaction, learning analytics as a module, and the Learning Coach assistant are removed. A Grounding and Provenance section replaces the Learning Philosophy.

**Reason:** Education features are out of scope; the groundwork built for them is obsolete.

#### 3. Added cost as a core principle

Principle 10 makes low, predictable cost a requirement — achieved by doing less work, not by using weaker models.

**Reason:** Occasional personal use must be affordable, and a cheaper but worse Cortex defeats the purpose.

#### 4. Added Version 2 non-goals and completion criteria

**Reason:** A defined finish line keeps the remaining work bounded.

#### 5. Added the document assistant as the primary demonstration

Cortex now also serves a team's policy documents: documents-only answers with refusal, document versions, a report of unanswered questions, a measured evaluation set, and a simple assistant page.

**Reason:** Cortex demonstrates building custom internal knowledge assistants for organizations, a common and concrete need.

---

### Changes from Previous Draft (v1.0)

#### 1. Shifted from “Project-centric” to “Knowledge-centric”

**Previous idea:**
Projects were described as the primary organizational unit.

**Current version:**
Knowledge is the primary object. Workspaces (projects, learning goals, areas of interest) are contexts that reference knowledge rather than owning it.

**Reason:** This avoids duplicating concepts across multiple endeavors. A concept like “vector embeddings” should exist once and be reusable in many workspaces.

#### 2. Introduced the distinction between Resources and Knowledge

The previous draft blurred uploaded files and the knowledge extracted from them.

The new version explicitly states that resources are inputs and evidence, while knowledge is the structured representation created from those inputs.

**Reason:** This better reflects the core purpose of Cortex and keeps the architecture flexible.

#### 3. Added a dedicated Learning Philosophy

Instead of claiming Cortex knows what a user understands, the specification now frames learning as evidence-based confidence.

**Reason:** This is both more realistic and more technically achievable. It avoids overpromising while leaving room for future educational features.

#### 4. Strengthened the role of the Core Knowledge Engine

The architecture now clearly identifies a single foundational component that stores, indexes, and relates knowledge, with all other capabilities acting as modular services around it.

**Reason:** This reinforces the long-term goal of making Cortex the shared knowledge layer for future AI applications.

#### 5. Added explicit Version 1 non-goals

The previous draft focused almost entirely on aspirations.

The new version defines what the first release should not attempt.

**Reason:** Clear boundaries reduce scope creep and make the project more likely to reach a polished, usable state.