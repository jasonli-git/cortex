"""Tests for parsers and structure-aware chunking."""

import pymupdf
import pytest

from pks.core.errors import ValidationError
from pks.ingestion.chunking import chunk_document
from pks.ingestion.parsers import (
    ParsedDocument,
    ParsedSection,
    parse_markdown,
    parse_pdf,
    parse_text,
)

# ----------------------------------------------------------------------
# Parsers
# ----------------------------------------------------------------------


def test_parse_text_single_section():
    doc = parse_text("Hello world.\n\nSecond paragraph.")
    assert len(doc.sections) == 1
    assert doc.sections[0].path is None
    assert "Second paragraph." in doc.sections[0].text


def test_parse_text_rejects_empty():
    with pytest.raises(ValidationError):
        parse_text("   \n  ")


def test_parse_markdown_builds_heading_paths():
    content = """Intro before any heading.

# American History

## The Colonial Era

Colonial text.

### Jamestown

Jamestown text.

## The Revolution

Revolution text.
"""
    doc = parse_markdown(content)
    assert [(s.path, s.text) for s in doc.sections] == [
        (None, "Intro before any heading."),
        ("American History > The Colonial Era", "Colonial text."),
        ("American History > The Colonial Era > Jamestown", "Jamestown text."),
        ("American History > The Revolution", "Revolution text."),
    ]


def test_parse_markdown_ignores_headings_in_code_blocks():
    content = "# Real Heading\n\nText.\n\n```\n# not a heading\n```\n\nMore text."
    doc = parse_markdown(content)
    assert len(doc.sections) == 1
    assert doc.sections[0].path == "Real Heading"
    assert "# not a heading" in doc.sections[0].text


def test_parse_pdf_with_outline(tmp_path):
    pdf_path = tmp_path / "book.pdf"
    doc = pymupdf.open()
    for text in ["Chapter one text.", "More of chapter one.", "Chapter two text."]:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.set_toc([[1, "Chapter One", 1], [1, "Chapter Two", 3]])
    doc.save(pdf_path)
    doc.close()

    parsed = parse_pdf(pdf_path)
    assert [s.path for s in parsed.sections] == ["Chapter One", "Chapter One", "Chapter Two"]
    assert "Chapter two text." in parsed.sections[2].text


def test_parse_pdf_without_outline_uses_page_numbers(tmp_path):
    pdf_path = tmp_path / "plain.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Only page.")
    doc.save(pdf_path)
    doc.close()

    parsed = parse_pdf(pdf_path)
    assert [s.path for s in parsed.sections] == ["Page 1"]


def test_parse_pdf_rejects_empty(tmp_path):
    pdf_path = tmp_path / "empty.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()

    with pytest.raises(ValidationError):
        parse_pdf(pdf_path)


def test_parsed_document_round_trips_through_dict():
    doc = ParsedDocument(sections=[ParsedSection(path="A > B", text="text")])
    assert ParsedDocument.from_dict(doc.to_dict()) == doc


# ----------------------------------------------------------------------
# Chunking
# ----------------------------------------------------------------------


def test_chunks_preserve_structure_and_order():
    doc = ParsedDocument(
        sections=[
            ParsedSection(path="Ch 1", text="First paragraph.\n\nSecond paragraph."),
            ParsedSection(path="Ch 2", text="Third paragraph."),
        ]
    )
    chunks = chunk_document(doc, target_chars=1000)
    assert [(ordinal, path) for ordinal, _, path, _ in chunks] == [(0, "Ch 1"), (1, "Ch 2")]
    assert "Second paragraph." in chunks[0][1]


def test_chunks_never_cross_sections():
    doc = ParsedDocument(
        sections=[
            ParsedSection(path="A", text="short"),
            ParsedSection(path="B", text="also short"),
        ]
    )
    # Both would fit in one chunk by size, but sections keep them apart.
    chunks = chunk_document(doc, target_chars=1000)
    assert len(chunks) == 2


def test_large_section_splits_into_multiple_chunks():
    paragraphs = "\n\n".join(f"Paragraph number {i} with some words." for i in range(100))
    doc = ParsedDocument(sections=[ParsedSection(path="Big", text=paragraphs)])
    chunks = chunk_document(doc, target_chars=500)

    assert len(chunks) > 1
    assert all(len(text) <= 500 for _, text, _, _ in chunks)
    assert [ordinal for ordinal, _, _, _ in chunks] == list(range(len(chunks)))
    # Nothing lost: every paragraph appears in exactly one chunk.
    joined = "\n\n".join(text for _, text, _, _ in chunks)
    assert all(f"Paragraph number {i} " in joined for i in range(100))


def test_oversized_paragraph_is_hard_split():
    doc = ParsedDocument(sections=[ParsedSection(path=None, text="word " * 500)])
    chunks = chunk_document(doc, target_chars=400)
    assert len(chunks) > 1
    assert all(len(text) <= 400 for _, text, _, _ in chunks)


def test_token_counts_estimated():
    doc = ParsedDocument(sections=[ParsedSection(path=None, text="x" * 400)])
    chunks = chunk_document(doc)
    assert chunks[0][3] == 100
