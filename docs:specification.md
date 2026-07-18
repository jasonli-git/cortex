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

---

### Learning Philosophy

---

### Architecture Philosophy

---

### Long-Term Product Direction

---

### Non-Goals (Version 1)

---

### Changes from Previous Draft