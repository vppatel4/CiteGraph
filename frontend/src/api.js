// Thin wrapper around the gateway's REST API. The token is kept in localStorage
// and attached to every authenticated call.

const TOKEN_KEY = "citegraph_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, auth = true, isForm = false } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  const res = await fetch(path, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    throw new Error(data.error || `request failed (${res.status})`);
  }
  return data;
}

export const api = {
  signup: (email, password) =>
    request("/api/auth/signup", { method: "POST", body: { email, password }, auth: false }),
  login: (email, password) =>
    request("/api/auth/login", { method: "POST", body: { email, password }, auth: false }),
  me: () => request("/api/me"),
  health: () => request("/healthz", { auth: false }),
  listPapers: () => request("/api/papers"),
  uploadPaper: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/api/papers", { method: "POST", body: fd, isForm: true });
  },
  ask: (question, paperIds = []) =>
    request("/api/ask", { method: "POST", body: { question, paper_ids: paperIds } }),
  eval: () => request("/api/eval", { auth: false }),
};
