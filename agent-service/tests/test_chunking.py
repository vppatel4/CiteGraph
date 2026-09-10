from app.ingestion.chunking import Segment, chunk_segments


def _words(n, word="w"):
    return " ".join(f"{word}{i}" for i in range(n))


def test_chunks_respect_size_and_overlap():
    seg = Segment(page=1, section="Methods", text=_words(1000))
    chunks = chunk_segments([seg], "Paper", size_words=100, overlap_words=20)
    # 1000 words, step 80 -> ceil coverage
    assert len(chunks) >= 12
    for c in chunks[:-1]:
        assert len(c.content.split()) == 100
    assert all(c.section == "Methods" for c in chunks)
    # overlap: the last 20 words of chunk 0 reappear at the start of chunk 1
    first = chunks[0].content.split()
    second = chunks[1].content.split()
    assert first[-20:] == second[:20]


def test_chunks_never_cross_sections():
    segs = [
        Segment(page=1, section="Intro", text=_words(50, "a")),
        Segment(page=2, section="Results", text=_words(50, "b")),
    ]
    chunks = chunk_segments(segs, "Paper", size_words=200, overlap_words=0)
    sections = {c.section for c in chunks}
    assert sections == {"Intro", "Results"}
    # no chunk mixes tokens from both sections
    for c in chunks:
        toks = c.content.split()
        assert all(t.startswith("a") for t in toks) or all(t.startswith("b") for t in toks)


def test_page_is_first_word_page():
    seg = Segment(page=7, section="Body", text=_words(30))
    chunks = chunk_segments([seg], "Paper", size_words=10, overlap_words=0)
    assert chunks[0].page == 7
