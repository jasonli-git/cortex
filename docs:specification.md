# AI PKS Specifications
## Product Specification v1.0

### Vision

Build a modular AI-powered Personal Knowledge System (PKS) that functions as a user’s long-term knowledge operating system.

The purpose of the application is not to replace ChatGPT, Claude, or future frontier models. Instead, it exists to organize, preserve, connect, and retrieve a user’s accumulated knowledge across years of learning, projects, work, and personal interests.

The system should transform unstructured information—including documents, books, notes, conversations, code snippets, websites, and future knowledge sources—into structured, interconnected knowledge that can be searched, explored, reasoned over, and expanded by AI.

The PKS should prioritize long-term knowledge accumulation rather than short-term question answering.

The application should be designed as a platform rather than a single-purpose application, allowing future AI assistants and modules to build upon the same knowledge layer without requiring architectural changes.

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

#### 6. AI should be transparent.

Every AI-generated response should clearly distinguish between:

* knowledge retrieved from the user’s PKS
* general model knowledge
* external sources (future capability)

Users should always understand where information originated.

#### 7. Expensive reasoning should happen once.

Complex AI processing should occur primarily during ingestion.

After ingestion, knowledge should already be structured sufficiently to allow fast retrieval and conversation using smaller or faster models when appropriate.

#### 8. Modularity is mandatory.

Every major capability should exist as an independent module.

Examples include:

* ingestion
* embeddings
* search
* OCR
* graph generation
* summarization
* learning analytics
* future assistants

Modules should communicate through stable interfaces and should be replaceable without affecting the rest of the application.

---

### User Experience

The application should feel less like “chat with my PDFs” and more like a personal knowledge workspace.

The primary interactions should be:

* upload resources
* write notes
* search knowledge
* chat with accumulated knowledge
* browse relationships
* review learning
* manage workspaces

Users should never feel required to manually organize every piece of information.

Instead, the application should continuously perform background processing to maintain an organized knowledge base.

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

The application should support both active learning and passive reference.

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

### Learning Philosophy

The application should avoid claiming to know what a user understands.

Instead, it should estimate evidence of learning.

Evidence may include:

* resources read
* notes written
* questions asked
* concepts revisited
* conversations
* highlights
* projects completed
* future quizzes or exercises

Understanding should therefore be represented as confidence rather than certainty.

This model should remain extensible and should not be required for Version 1.

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

The PKS should become the shared intelligence layer for future applications.

---

### Long-Term Product Direction

The PKS should not attempt to become every AI application.

Instead, it should become the foundational knowledge platform upon which future specialized assistants can operate.

Examples include:

* AI Research Assistant
* AI Coding Assistant
* Agentic Job Search Assistant
* Learning Coach
* Decision Support Assistant

Each assistant should reuse the same knowledge base rather than maintaining separate memories.

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

---

### Changes from Previous Draft

#### 1. Shifted from “Project-centric” to “Knowledge-centric”

**Previous idea:**
Projects were described as the primary organizational unit.

**Current version:**
Knowledge is the primary object. Workspaces (projects, learning goals, areas of interest) are contexts that reference knowledge rather than owning it.

**Reason:** This avoids duplicating concepts across multiple endeavors. A concept like “vector embeddings” should exist once and be reusable in many workspaces.

#### 2. Introduced the distinction between Resources and Knowledge

The previous draft blurred uploaded files and the knowledge extracted from them.

The new version explicitly states that resources are inputs and evidence, while knowledge is the structured representation created from those inputs.

**Reason:** This better reflects the core purpose of the PKS and keeps the architecture flexible.

#### 3. Added a dedicated Learning Philosophy

Instead of claiming the PKS knows what a user understands, the specification now frames learning as evidence-based confidence.

**Reason:** This is both more realistic and more technically achievable. It avoids overpromising while leaving room for future educational features.

#### 4. Strengthened the role of the Core Knowledge Engine

The architecture now clearly identifies a single foundational component that stores, indexes, and relates knowledge, with all other capabilities acting as modular services around it.

**Reason:** This reinforces the long-term goal of making the PKS the shared knowledge layer for future AI applications.

#### 5. Added explicit Version 1 non-goals

The previous draft focused almost entirely on aspirations.

The new version defines what the first release should not attempt.

**Reason:** Clear boundaries reduce scope creep and make the project more likely to reach a polished, usable state.