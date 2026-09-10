from dataclasses import dataclass

from app.graph.citations import (
    is_refusal,
    is_structural,
    parse_markers,
    strip_markers,
    verify_answer,
)
from app.graph.prompts import REFUSAL_SENTENCE


@dataclass
class FakeChunk:
    paper_id: str
    chunk_id: str
    paper_title: str
    section: str
    page: int
    content: str


class StubVerifier:
    """Supports a claim iff it shares the word 'reduce' with the chunk — lets us
    test the keep/drop logic without loading any embedding model."""

    def support_score(self, claim, chunk_text):
        return 0.9 if ("reduce" in claim.lower() and "reduce" in chunk_text.lower()) else 0.1

    def is_supported(self, score):
        return score >= 0.5


def test_parse_and_strip_markers():
    assert parse_markers("The model works well [1].") == [1]
    assert parse_markers("Both hold [2][3].") == [2, 3]
    assert parse_markers("Combined [1, 4].") == [1, 4]
    assert parse_markers("No citation here.") == []
    assert strip_markers("A claim [1][2].") == "A claim ."


def test_is_structural_and_refusal():
    assert is_structural("")
    assert is_structural("## Heading")
    assert is_structural("Key findings:")
    assert not is_structural("The system reduces false positives significantly in tests")
    assert is_refusal(REFUSAL_SENTENCE)
    assert is_refusal("the provided papers don't address this question")
    assert not is_refusal("The papers describe three methods [1].")


def _chunks():
    return [
        FakeChunk("p1", "c1", "Paper A", "Methods", 3, "we reduce false positives via checks"),
        FakeChunk("p2", "c2", "Paper B", "Results", 5, "accuracy improved on the benchmark"),
    ]


def test_verify_keeps_supported_and_drops_unsupported():
    draft = (
        "- The method helps reduce false positives [1].\n"
        "- Accuracy jumped to 99 percent on every dataset [2].\n"
    )
    out = verify_answer(draft, _chunks(), StubVerifier())
    assert out["answered"] is True
    assert "reduce false positives" in out["answer"]
    assert "99 percent" not in out["answer"]  # unsupported claim dropped
    assert out["dropped"] == 1
    assert len(out["citations"]) == 1
    assert out["citations"][0]["paper_title"] == "Paper A"


def test_all_unsupported_collapses_to_refusal():
    draft = "- Accuracy jumped to 99 percent [2].\n"
    out = verify_answer(draft, _chunks(), StubVerifier())
    assert out["answered"] is False
    assert out["answer"] == REFUSAL_SENTENCE
    assert out["citations"] == []


def test_model_refusal_passthrough():
    out = verify_answer(REFUSAL_SENTENCE, _chunks(), StubVerifier())
    assert out["answered"] is False
    assert out["citations"] == []
