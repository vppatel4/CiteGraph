import fitz

from app.ingestion.pdf import parse_pdf


def _pdf(lines):
    """Build a one-page PDF from (text, font size) pairs, top to bottom."""
    doc = fitz.open()
    page = doc.new_page()
    y = 60
    for text, size in lines:
        page.insert_text((50, y), text, fontsize=size)
        y += size + 12
    data = doc.tobytes()
    doc.close()
    return data


def test_title_skips_license_line_and_joins_wrapped_title():
    pdf = _pdf([
        ("Provided proper attribution is provided, Google grants permission", 8),
        ("Attention Is All You", 18),
        ("Need For Testing", 18),
        ("Some Author, Some University", 10),
    ])
    title, num_pages, _ = parse_pdf(pdf, "paper.pdf")
    assert title == "Attention Is All You Need For Testing"
    assert num_pages == 1


def test_nul_bytes_are_removed_from_text(monkeypatch):
    original = fitz.Page.get_text

    def with_nul(self, *args, **kwargs):
        out = original(self, *args, **kwargs)
        return out.replace("model", "mo\x00del") if isinstance(out, str) else out

    monkeypatch.setattr(fitz.Page, "get_text", with_nul)
    pdf = _pdf([
        ("A Paper Title Here", 18),
        ("This sentence describes the model and is long enough to keep.", 10),
    ])
    _, _, segments = parse_pdf(pdf, "paper.pdf")
    assert segments
    assert all("\x00" not in s.text for s in segments)
    assert any("model" in s.text for s in segments)
