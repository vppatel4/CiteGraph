// Small presentational pieces shared across pages.

// A little SVG ring that fills according to a 0..1 confidence score and is
// colored by how confident it is (aqua = strong, amber = middling).
export function ConfidenceRing({ value }) {
  const pct = Math.max(0, Math.min(1, value));
  const r = 14;
  const c = 2 * Math.PI * r;
  const color = pct >= 0.66 ? "var(--ok)" : pct >= 0.45 ? "var(--warn)" : "var(--danger)";
  return (
    <svg className="ring" viewBox="0 0 34 34" title={`confidence ${(pct * 100).toFixed(0)}%`}>
      <circle cx="17" cy="17" r={r} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="3.5" />
      <circle
        cx="17" cy="17" r={r} fill="none" stroke={color} strokeWidth="3.5"
        strokeLinecap="round" strokeDasharray={c}
        strokeDashoffset={c * (1 - pct)} transform="rotate(-90 17 17)"
      />
      <text x="17" y="20" textAnchor="middle" fontSize="9" fill="var(--text)" fontFamily="var(--mono)">
        {Math.round(pct * 100)}
      </text>
    </svg>
  );
}

// Render the answer text: turn "- " lines into a bullet list and highlight the
// [n] citation markers. Plain and predictable — no markdown library needed.
export function AnswerText({ text }) {
  const lines = text.split("\n").filter((l) => l.trim() !== "");
  const blocks = [];
  let bullets = [];
  const flush = () => {
    if (bullets.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`}>
          {bullets.map((b, i) => (
            <li key={i}>{withMarkers(b)}</li>
          ))}
        </ul>
      );
      bullets = [];
    }
  };
  for (const line of lines) {
    const t = line.trim();
    if (/^[-*•–]\s+/.test(t)) {
      bullets.push(t.replace(/^[-*•–]\s+/, ""));
    } else {
      flush();
      blocks.push(<p key={`p-${blocks.length}`}>{withMarkers(t)}</p>);
    }
  }
  flush();
  return <div className="answer">{blocks}</div>;
}

function withMarkers(text) {
  // Split on [n] / [n,m] markers and render them as small superscripts.
  const parts = text.split(/(\[\d+(?:\s*[,;]\s*\d+)*\])/g);
  return parts.map((p, i) =>
    /^\[\d/.test(p) ? (
      <sup className="cite-ref" key={i}>{p}</sup>
    ) : (
      <span key={i}>{p}</span>
    )
  );
}

export function CitationCard({ c }) {
  const bar = c.confidence >= 0.66 ? "var(--ok)" : c.confidence >= 0.45 ? "var(--warn)" : "var(--danger)";
  return (
    <div className="cite" style={{ "--bar": bar }}>
      <div className="head">
        <div>
          <div className="paper-title">{c.paper_title}</div>
          <div className="loc">
            {c.section || "Body"} · p.{c.page}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {c.verified ? <span className="pill ok">verified</span> : <span className="pill warn">flagged</span>}
          <ConfidenceRing value={c.confidence} />
        </div>
      </div>
      <div className="snippet">{c.snippet}</div>
      {c.claim && <div className="claim">backs: “{c.claim}”</div>}
    </div>
  );
}
