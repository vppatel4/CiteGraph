"""Turn a PDF's bytes into (title, page count, section-tagged text segments).

The section tagging is deliberately simple and rule-based: research papers use a
small, predictable set of headings ("Introduction", "Methods", "3.2 Results"…),
so a regex catches the common cases without any ML. Every segment carries the
page it came from and the section it falls under, which is what lets a citation
point at "paper X, Methods, p.4".
"""
from __future__ import annotations

import io
import re

import fitz  # PyMuPDF

from app.ingestion.chunking import Segment

# Words that, when a short line is basically just one of them, mark a new section.
_SECTION_WORDS = (
    "abstract",
    "introduction",
    "background",
    "related work",
    "motivation",
    "method",
    "methods",
    "methodology",
    "approach",
    "materials and methods",
    "model",
    "architecture",
    "experiment",
    "experiments",
    "experimental setup",
    "evaluation",
    "results",
    "analysis",
    "discussion",
    "limitations",
    "conclusion",
    "conclusions",
    "future work",
    "references",
    "acknowledgments",
    "acknowledgements",
    "appendix",
)

# e.g. "3", "3.2", "IV." at the start of a heading line.
_NUMBER_PREFIX = re.compile(r"^\s*(\d+(\.\d+)*|[IVXLC]+)[.)]?\s+")


def _is_heading(line: str) -> str | None:
    """Return the normalized section name if the line looks like a heading."""
    raw = line.strip()
    if not raw or len(raw) > 80:
        return None
    if raw.endswith((".", ",", ";", ":")) and not _NUMBER_PREFIX.match(raw):
        return None

    stripped = _NUMBER_PREFIX.sub("", raw).strip()
    low = stripped.lower()

    if low in _SECTION_WORDS:
        return stripped.title()
    # A numbered short line with few words is very likely a heading.
    if _NUMBER_PREFIX.match(raw) and 0 < len(stripped.split()) <= 6:
        return stripped
    # An ALL-CAPS short line (common for section titles).
    if stripped.isupper() and 1 <= len(stripped.split()) <= 6:
        return stripped.title()
    return None


def _guess_title(first_page_text: str, fallback: str) -> str:
    for line in first_page_text.splitlines():
        candidate = line.strip()
        # Skip obvious non-titles.
        if len(candidate) < 8 or candidate.lower() in ("abstract",):
            continue
        if candidate.lower().startswith(("arxiv", "doi", "http")):
            continue
        return candidate[:300]
    return fallback


def parse_pdf(content: bytes, filename: str) -> tuple[str, int, list[Segment]]:
    doc = fitz.open(stream=io.BytesIO(content), filetype="pdf")
    num_pages = doc.page_count

    first_page_text = doc.load_page(0).get_text("text") if num_pages else ""
    title = _guess_title(first_page_text, fallback=filename.rsplit(".", 1)[0])

    segments: list[Segment] = []
    current_section = "Body"
    for page_index in range(num_pages):
        text = doc.load_page(page_index).get_text("text")
        buffer: list[str] = []

        def flush() -> None:
            if buffer:
                paragraph = " ".join(buffer).strip()
                if len(paragraph) >= 40:  # drop tiny fragments / stray lines
                    segments.append(
                        Segment(page=page_index + 1, section=current_section, text=paragraph)
                    )
                buffer.clear()

        for line in text.splitlines():
            heading = _is_heading(line)
            if heading is not None:
                flush()
                current_section = heading
                continue
            if line.strip() == "":
                flush()
            else:
                buffer.append(line.strip())
        flush()

    doc.close()
    return title, num_pages, segments
