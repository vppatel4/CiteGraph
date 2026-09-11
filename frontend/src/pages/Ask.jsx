import { useState } from "react";
import { api } from "../api.js";
import { AnswerText, CitationCard } from "../components.jsx";

const EXAMPLES = [
  "What methods do these papers use to reduce false positives?",
  "Compare the datasets used across the papers.",
  "What are the main limitations the authors mention?",
];

export default function Ask({ hasPapers }) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const ask = async (q) => {
    const query = (q ?? question).trim();
    if (!query) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const res = await api.ask(query);
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="main">
      <div className="glass" style={{ padding: 18 }}>
        <p className="section-title">Ask across your papers</p>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What methods do these papers use to reduce false positives?"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) ask();
          }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 12, gap: 12 }}>
          <div className="chips">
            {EXAMPLES.map((ex) => (
              <button key={ex} className="chip" onClick={() => { setQuestion(ex); ask(ex); }}>
                {ex.length > 42 ? ex.slice(0, 40) + "…" : ex}
              </button>
            ))}
          </div>
          <button className="btn primary" onClick={() => ask()} disabled={busy || !question.trim()}>
            {busy ? <span className="spinner" /> : "Ask"}
          </button>
        </div>
        {!hasPapers && (
          <div className="faint" style={{ fontSize: 12, marginTop: 10 }}>
            Tip: upload a PDF on the left first — with no papers, every question is honestly refused.
          </div>
        )}
      </div>

      <div className="scroll" style={{ paddingRight: 4 }}>
        {error && <div className="glass answer-wrap"><div className="error-msg">{error}</div></div>}

        {busy && (
          <div className="glass answer-wrap">
            <span className="spinner" /> <span className="muted" style={{ marginLeft: 8 }}>
              decomposing → retrieving → drafting → verifying…
            </span>
          </div>
        )}

        {result && !busy && (
          <>
            {result.sub_questions?.length > 1 && (
              <div className="glass" style={{ padding: "12px 16px", marginBottom: 14 }}>
                <span className="section-title">Broke this into</span>
                <div className="chips" style={{ marginTop: 8 }}>
                  {result.sub_questions.map((s, i) => (
                    <span key={i} className="chip" style={{ cursor: "default" }}>{s}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="glass answer-wrap" style={{ marginBottom: 14 }}>
              {result.answered ? (
                <AnswerText text={result.answer} />
              ) : (
                <div className="refusal">
                  <span className="icon">⚠</span>
                  <div>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>Not found in your papers</div>
                    <div className="muted" style={{ fontSize: 13.5 }}>
                      {result.answer}
                      {result.refusal_reason ? ` (${result.refusal_reason})` : ""}
                    </div>
                  </div>
                </div>
              )}
              {result.dropped_citations > 0 && (
                <div className="faint" style={{ fontSize: 12, marginTop: 14 }}>
                  {result.dropped_citations} claim{result.dropped_citations > 1 ? "s" : ""} dropped by the verifier for lack of support.
                </div>
              )}
            </div>

            {result.citations?.length > 0 && (
              <>
                <p className="section-title" style={{ margin: "0 2px 10px" }}>
                  Citations — checked against source
                </p>
                {result.citations.map((c, i) => (
                  <CitationCard key={i} c={c} />
                ))}
              </>
            )}
          </>
        )}

        {!result && !busy && !error && (
          <div className="glass empty">Ask a question to see a cited, verified answer here.</div>
        )}
      </div>
    </div>
  );
}
