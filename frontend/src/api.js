const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "urlyze_token_v1";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable */
  }
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("OFFLINE");
  }

  if (res.status === 401 && auth) throw new Error("UNAUTHORIZED");

  if (!res.ok) {
    let msg = "Something went wrong. Please try again.";
    try {
      const j = await res.json();
      if (typeof j.detail === "string") msg = j.detail;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  return res.json();
}

export const register = (name, email, password) =>
  request("/auth/register", { method: "POST", body: { name, email, password }, auth: false });
export const login = (email, password) =>
  request("/auth/login", { method: "POST", body: { email, password }, auth: false });
export const fetchMe = () => request("/auth/me");
export const scanUrl = (url) => request("/predict", { method: "POST", body: { url } });
export const checkEmail = (text) => request("/email-check", { method: "POST", body: { text } });
export const getHistory = () => request("/history");
export const clearHistory = () => request("/history", { method: "DELETE" });
export const getModelInfo = () => request("/model-info", { auth: false });
