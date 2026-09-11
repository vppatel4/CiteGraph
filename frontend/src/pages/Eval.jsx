import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Eval() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.eval().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="main"><div className="glass empty">{error}</div></div>;
  if (!data) return <div className="main"><div className="glass empty"><span className="spinner" /></div></div>;

  if (!data.available) {
    return (
      <div className="main">
        <div className="glass answer-wrap">
          <p className="section-title">Evaluation</p>
          <p className="muted">{data.message || "No evaluation results yet."}</p>
          <p className="faint" style={{ fontSize: 13 }}>
            Run <code style={{ fontFamily: "var(--mono)", color: "var(--aqua)" }}>make eval</code> to
            score the citation verifier and the anti-hallucination check.
          </p>
        </div>
      </div>
    );
  }

  const cit = data.citation;
  const clfWins = cit.classifier.f1 >= cit.baseline.f1;
  const na = data.cannot_answer;

  return (
    <div className="main scroll">
      <div className="glass answer-wrap" style={{ marginBottom: 16 }}>
        <p className="section-title">How well does the citation check work?</p>
        <p className="muted" style={{ fontSize: 13.5, marginTop: 4 }}>
          Measured on {cit.count} hand-labeled (claim, source, verdict) examples
          ({cit.positives} supports). Classifier scored with {cit.cv_note}. Higher is better.
        </p>
        <table className="compare">
          <thead>
            <tr><th>Method</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th></tr>
          </thead>
          <tbody>
            <tr className={!clfWins ? "win" : ""}>
              <td>Baseline (similarity ≥ {data.threshold})</td>
              <td className="num">{cit.baseline.accuracy}</td>
              <td className="num">{cit.baseline.precision}</td>
              <td className="num">{cit.baseline.recall}</td>
              <td className="num">{cit.baseline.f1}</td>
            </tr>
            <tr className={clfWins ? "win" : ""}>
              <td>Classifier (logistic regression)</td>
              <td className="num">{cit.classifier.accuracy}</td>
              <td className="num">{cit.classifier.precision}</td>
              <td className="num">{cit.classifier.recall}</td>
              <td className="num">{cit.classifier.f1}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="glass answer-wrap">
        <p className="section-title">Anti-hallucination: does it refuse when it should?</p>
        {na ? (
          <div className="stat-grid" style={{ marginTop: 12 }}>
            <div className="stat">
              <div className="k">Unanswerable Qs</div>
              <div className="v">{na.total}</div>
            </div>
            <div className="stat">
              <div className="k">Correctly refused</div>
              <div className="v aqua">{na.refused}</div>
            </div>
            <div className="stat">
              <div className="k">False-answer rate</div>
              <div className={"v " + (na.false_answer_rate === 0 ? "aqua" : "amber")}>
                {(na.false_answer_rate * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        ) : (
          <p className="muted" style={{ fontSize: 13.5, marginTop: 4 }}>
            Run <code style={{ fontFamily: "var(--mono)", color: "var(--aqua)" }}>
              make eval
            </code>{" "}
            against a user with papers loaded (add <code style={{ fontFamily: "var(--mono)" }}>--live --user-id</code>)
            to measure how often the system wrongly answers a question the papers can't support.
          </p>
        )}
      </div>
    </div>
  );
}
