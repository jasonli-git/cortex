"""Per-format parsers: file → ParsedDocument (text + native structure).

Parsers extract whatever structure the format itself carries (Markdown
headings, PDF table of contents). Deeper semantic structure — chapters,
periods, topics — is the extraction module's job (Milestone 3).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from pks.core.errors import ValidationError
from pks.core.models import ResourceType


@dataclass
class ParsedSection:
    path: str | None  # e.g. "Chapter 3 > The Republic"; None for unstructured text
    text: str


@dataclass
class ParsedDocument:
    sections: list[ParsedSection] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(section.text for section in self.sections)

    def to_dict(self) -> dict:
        return {"sections": [{"path": s.path, "text": s.text} for s in self.sections]}

    @classmethod
    def from_dict(cls, data: dict) -> ParsedDocument:
        return cls(
            sections=[ParsedSection(path=s["path"], text=s["text"]) for s in data["sections"]]
        )


def parse_resource_file(path: Path, resource_type: ResourceType) -> ParsedDocument:
    if resource_type is ResourceType.PDF:
        return parse_pdf(path)
    if resource_type in (ResourceType.MARKDOWN, ResourceType.NOTE):
        return parse_markdown(path.read_text(encoding="utf-8"))
    if resource_type is ResourceType.TEXT:
        return parse_text(path.read_text(encoding="utf-8"))
    raise ValidationError(f"no parser for resource type {resource_type!r}")


def parse_text(content: str) -> ParsedDocument:
    content = content.strip()
    if not content:
        raise ValidationError("resource is empty")
    return ParsedDocument(sections=[ParsedSection(path=None, text=content)])


_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def parse_markdown(content: str) -> ParsedDocument:
    """Split a Markdown document into sections along its heading hierarchy."""
    sections: list[ParsedSection] = []
    # Stack of (level, title) for the current heading path.
    stack: list[tuple[int, str]] = []
    lines: list[str] = []

    def flush() -> None:
        text = "\n".join(lines).strip()
        lines.clear()
        if text:
            path = " > ".join(title for _, title in stack) or None
            sections.append(ParsedSection(path=path, text=text))

    in_code_block = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
        match = None if in_code_block else _HEADING.match(line)
        if match:
            flush()
            level = len(match.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, match.group(2)))
        else:
            lines.append(line)
    flush()

    if not sections:
        raise ValidationError("resource is empty")
    return ParsedDocument(sections=sections)


def parse_pdf(path: Path) -> ParsedDocument:
    """One section per non-empty page; paths come from the PDF outline when present."""
    with pymupdf.open(path) as doc:
        toc = doc.get_toc()  # entries: [level, title, 1-based page]
        sections: list[ParsedSection] = []
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if not text:
                continue
            outline_path = _outline_path_for_page(toc, page_number)
            path_str = outline_path or f"Page {page_number}"
            sections.append(ParsedSection(path=path_str, text=text))

    if not sections:
        raise ValidationError("PDF contains no extractable text (scanned PDFs need OCR, post-V1)")
    return ParsedDocument(sections=sections)


def _outline_path_for_page(toc: list, page_number: int) -> str | None:
    """Hierarchical outline path of the last TOC entry at or before this page."""
    stack: list[tuple[int, str]] = []
    found = False
    for level, title, page in toc:
        if page > page_number:
            break
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title.strip()))
        found = True
    if not found:
        return None
    return " > ".join(title for _, title in stack)
