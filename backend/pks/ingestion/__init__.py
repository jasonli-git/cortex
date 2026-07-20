"""Ingestion: turning uploaded resources into parsed, chunked evidence.

Modules:
- intake:   accept uploads/notes, store originals, kick off the pipeline
- parsers:  per-format text + structure extraction (pdf, markdown, text, note)
- chunking: structure-aware chunking of parsed documents
- pipeline: the parse/chunk stages wired into the event registry
"""

from pks.ingestion import pipeline

__all__ = ["pipeline"]
