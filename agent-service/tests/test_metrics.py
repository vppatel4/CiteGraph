from app.eval.metrics import score


def test_perfect_predictions():
    s = score([1, 0, 1, 0], [1, 0, 1, 0])
    assert s.accuracy == 1.0
    assert s.precision == 1.0
    assert s.recall == 1.0
    assert s.f1 == 1.0


def test_mixed_predictions():
    # true: 1 1 0 0 ; pred: 1 0 0 1
    s = score([1, 1, 0, 0], [1, 0, 0, 1])
    assert s.tp == 1 and s.fp == 1 and s.tn == 1 and s.fn == 1
    assert s.accuracy == 0.5
    assert abs(s.precision - 0.5) < 1e-9
    assert abs(s.recall - 0.5) < 1e-9


def test_no_positive_predictions():
    s = score([1, 1, 0], [0, 0, 0])
    assert s.precision == 0.0
    assert s.recall == 0.0
    assert s.f1 == 0.0
