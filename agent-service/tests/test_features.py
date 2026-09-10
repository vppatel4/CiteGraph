from app.eval.baseline import label_to_int
from app.eval.features import extract_features, keyword_overlap, number_overlap


def test_keyword_overlap_recall():
    claim = "The method reduces false positives"
    chunk = "we reduce false positives using a verification method on citations"
    ov = keyword_overlap(claim, chunk)
    assert ov > 0.7  # method, reduce(s), false, positives all present


def test_keyword_overlap_none():
    assert keyword_overlap("quantum entanglement dynamics", "banana bread recipe") == 0.0


def test_number_overlap():
    assert number_overlap("accuracy was 0.92", "we report 0.92 accuracy") == 1.0
    assert number_overlap("accuracy was 0.92", "we report 0.10 accuracy") == 0.0
    # no numbers in the claim -> nothing to contradict -> 1.0
    assert number_overlap("no numbers here", "still nothing") == 1.0


def test_extract_features_shape_and_range():
    feats = extract_features("a claim with words", "a chunk of text with words", 0.8)
    assert len(feats) == 5
    assert feats[0] == 0.8
    assert all(0.0 <= f <= 1.0 for f in feats)


def test_label_to_int():
    assert label_to_int("supports") == 1
    assert label_to_int("does_not_support") == 0
    assert label_to_int("Does Not Support") == 0
