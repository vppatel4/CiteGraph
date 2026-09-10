import numpy as np

from app.eval import classifier


def test_classifier_learns_separable_data(tmp_path):
    # similarity is the first feature; make it clearly separable
    rng = np.random.default_rng(0)
    pos = np.column_stack(
        [rng.uniform(0.6, 0.9, 40), rng.uniform(0.5, 1.0, 40), np.ones(40), rng.random(40), rng.random(40)]
    )
    neg = np.column_stack(
        [rng.uniform(0.0, 0.3, 40), rng.uniform(0.0, 0.4, 40), np.ones(40), rng.random(40), rng.random(40)]
    )
    X = np.vstack([pos, neg]).astype(np.float32)
    y = np.array([1] * 40 + [0] * 40)

    model = classifier.train(X, y)
    acc = (model.predict(X) == y).mean()
    assert acc > 0.9

    path = tmp_path / "clf.joblib"
    classifier.save(model, str(path))
    loaded = classifier.load(str(path))
    assert loaded is not None
    assert classifier.predict_proba(loaded, list(pos[0])) > 0.5
    assert classifier.predict_proba(loaded, list(neg[0])) < 0.5


def test_load_missing_returns_none(tmp_path):
    assert classifier.load(str(tmp_path / "nope.joblib")) is None
