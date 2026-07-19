"""Core Knowledge Engine.

The one module every other module consumes. Owns storage, indexing,
relationships, retrieval, metadata, provenance, and versioning of knowledge.
It has no knowledge of file formats, prompts, or HTTP.
"""

from pks.core.engine import KnowledgeEngine

__all__ = ["KnowledgeEngine"]
