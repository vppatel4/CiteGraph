import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

const DEMO_EMAIL = "demo@citegraph.dev";
const DEMO_PASSWORD = "demo1234";

export default function Login() {
  const { login, signup } = useAuth();
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await signup(email, password);
      nav("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const useDemo = () => {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    setMode("login");
  };

  return (
    <div className="login-shell">
      <div className="glass login-card">
        <div className="brand" style={{ marginBottom: 4 }}>
          <span className="tag">multi-paper Q&amp;A</span>
        </div>
        <h1>Cite<span style={{ color: "var(--accent)" }}>Graph</span></h1>
        <p className="sub">
          Ask questions across your research papers and get answers where every
          citation is checked against its source before you see it.
        </p>

        <form onSubmit={submit}>
          <label className="field">Email</label>
          <input
            type="email" value={email} autoComplete="username"
            onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required
          />
          <div style={{ height: 14 }} />
          <label className="field">Password</label>
          <input
            type="password" value={password} autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required
          />
          {error && <div className="error-msg">{error}</div>}
          <div style={{ height: 18 }} />
          <button className="btn primary" style={{ width: "100%" }} disabled={busy}>
            {busy ? <span className="spinner" /> : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>

        <div className="switch">
          {mode === "login" ? "New here?" : "Already have an account?"}{" "}
          <button onClick={() => setMode(mode === "login" ? "signup" : "login")}>
            {mode === "login" ? "Create an account" : "Log in"}
          </button>
        </div>

        <div className="demo-box">
          <strong>Try the demo account</strong>
          <div style={{ marginTop: 6 }}>
            <code>{DEMO_EMAIL}</code> / <code>{DEMO_PASSWORD}</code>
          </div>
          <button className="btn small" style={{ marginTop: 10 }} onClick={useDemo}>
            Fill demo credentials
          </button>
        </div>
      </div>
    </div>
  );
}
