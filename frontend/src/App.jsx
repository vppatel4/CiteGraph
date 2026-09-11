import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { useAuth } from "./auth.jsx";
import Ask from "./pages/Ask.jsx";
import Eval from "./pages/Eval.jsx";

function HealthDot() {
  const [h, setH] = useState(null);
  useEffect(() => {
    let alive = true;
    const tick = () => api.health().then((d) => alive && setH(d)).catch(() => {});
    tick();
    const id = setInterval(tick, 8000);
    return () => { alive = false; clearInterval(id); };
  }, []);
  const agent = h?.agent;
  let cls = "led", label = "connecting";
  if (agent?.ok) {
    if (agent.llm_ready && agent.embeddings_ready) { cls = "led on"; label = "ready"; }
    else { cls = "led warm"; label = "models warming up"; }
  } else if (h) { cls = "led"; label = "agent offline"; }
  return (
    <span className="status" title={agent?.detail || ""}>
      <span className={cls} /> {label}
    </span>
  );
}

function Sidebar({ papers, onUpload, uploading }) {
  const [over, setOver] = useState(false);
  const inputRef = useRef(null);

  const handleFiles = (files) => {
    const f = files?.[0];
    if (f) onUpload(f);
  };

  return (
    <aside className="glass sidebar">
      <div>
        <p className="section-title">Your papers</p>
        <div
          className={"drop" + (over ? " over" : "")}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setOver(true); }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => { e.preventDefault(); setOver(false); handleFiles(e.dataTransfer.files); }}
        >
          {uploading ? (
            <><span className="spinner" /> parsing &amp; embedding…</>
          ) : (
            <>Drop a PDF here or <span style={{ color: "var(--aqua)" }}>browse</span></>
          )}
          <input
            ref={inputRef} type="file" accept="application/pdf" hidden
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      </div>

      <div className="scroll" style={{ flex: 1 }}>
        {papers.length === 0 ? (
          <div className="faint" style={{ fontSize: 13, padding: "8px 2px" }}>
            No papers yet. Upload a few research PDFs to ask across them.
          </div>
        ) : (
          papers.map((p) => (
            <div className="paper" key={p.paper_id}>
              <div className="t">{p.title}</div>
              <div className="m">{p.num_pages} pages · {p.num_chunks} chunks</div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}

export default function App() {
  const { user, logout } = useAuth();
  const [papers, setPapers] = useState([]);
  const [tab, setTab] = useState("ask");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const refresh = useCallback(() => {
    api.listPapers().then((d) => setPapers(d.papers || [])).catch(() => {});
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const onUpload = async (file) => {
    setUploading(true);
    setUploadError("");
    try {
      await api.uploadPaper(file);
      refresh();
    } catch (e) {
      setUploadError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="app">
      <header className="glass topbar">
        <div className="brand">
          <h1>Cite<span className="dot">Graph</span></h1>
          <span className="tag">verified citations</span>
        </div>
        <div className="top-actions">
          <HealthDot />
          <span className="who">{user?.email}</span>
          <button className="btn ghost small" onClick={logout}>Log out</button>
        </div>
      </header>

      <div className="layout">
        <Sidebar papers={papers} onUpload={onUpload} uploading={uploading} />

        <div style={{ display: "flex", flexDirection: "column", gap: 18, minHeight: 0 }}>
          <div className="glass tabs" style={{ flex: "none" }}>
            <button className={"tab" + (tab === "ask" ? " active" : "")} onClick={() => setTab("ask")}>Ask</button>
            <button className={"tab" + (tab === "eval" ? " active" : "")} onClick={() => setTab("eval")}>Evaluation</button>
          </div>
          {uploadError && (
            <div className="glass" style={{ padding: "10px 16px" }}>
              <span className="error-msg">{uploadError}</span>
            </div>
          )}
          {tab === "ask" ? <Ask hasPapers={papers.length > 0} /> : <Eval />}
        </div>
      </div>
    </div>
  );
}
