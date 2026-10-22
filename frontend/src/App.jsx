import { useCallback, useEffect, useState } from "react";
import Icon from "./components/Icon.jsx";
import Scanner from "./components/Scanner.jsx";
import EmailChecker from "./components/EmailChecker.jsx";
import History from "./components/History.jsx";
import Dashboard from "./components/Dashboard.jsx";
import AuthPage from "./components/AuthPage.jsx";
import ThemeToggle from "./components/ThemeToggle.jsx";
import { checkEmail, clearHistory, fetchMe, getHistory, getToken, scanUrl, setToken } from "./api.js";

const TABS = [
  { id: "scan", label: "Scanner", icon: "scan" },
  { id: "email", label: "Email", icon: "mail" },
  { id: "history", label: "History", icon: "clock" },
  { id: "dash", label: "Dashboard", icon: "chart" },
];

const IDLE_SCAN = { status: "idle", url: "", result: null, error: "" };
const IDLE_EMAIL = { status: "idle", text: "", result: null, error: "" };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function friendly(e) {
  return e.message === "OFFLINE"
    ? "Can't reach the URLYZE engine. Make sure the backend is running (uvicorn main:app --reload)."
    : e.message;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(() => !!getToken());
  const [tab, setTab] = useState("scan");
  const [history, setHistory] = useState([]);
  const [scan, setScan] = useState(IDLE_SCAN);
  const [email, setEmail] = useState(IDLE_EMAIL);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setHistory([]);
    setScan(IDLE_SCAN);
    setEmail(IDLE_EMAIL);
    setTab("scan");
  }, []);

  const refreshHistory = useCallback(async () => {
    try {
      setHistory(await getHistory());
    } catch (e) {
      if (e.message === "UNAUTHORIZED") logout();
    }
  }, [logout]);

  // restore an existing login when the page opens
  useEffect(() => {
    if (!getToken()) return;
    fetchMe()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setBooting(false));
  }, []);

  useEffect(() => {
    if (user) refreshHistory();
  }, [user, refreshHistory]);

  const onAuthed = (token, u) => {
    setToken(token);
    setUser(u);
  };

  const runScan = useCallback(
    async (rawUrl) => {
      const url = rawUrl.trim();
      setTab("scan");
      if (!url) {
        setScan({ status: "error", url: "", result: null, error: "Please enter a URL to analyze." });
        return;
      }
      setScan({ status: "scanning", url, result: null, error: "" });
      try {
        const [result] = await Promise.all([scanUrl(url), sleep(1800)]);
        setScan({ status: "done", url, result, error: "" });
        refreshHistory();
      } catch (e) {
        if (e.message === "UNAUTHORIZED") return logout();
        setScan({ status: "error", url, result: null, error: friendly(e) });
      }
    },
    [refreshHistory, logout]
  );

  const runEmail = useCallback(
    async (text) => {
      if (!text.trim()) {
        setEmail({ status: "error", text: "", result: null, error: "Please paste the email text first." });
        return;
      }
      setEmail({ status: "scanning", text, result: null, error: "" });
      try {
        const [result] = await Promise.all([checkEmail(text), sleep(1600)]);
        setEmail({ status: "done", text, result, error: "" });
        refreshHistory();
      } catch (e) {
        if (e.message === "UNAUTHORIZED") return logout();
        setEmail({ status: "error", text, result: null, error: friendly(e) });
      }
    },
    [refreshHistory, logout]
  );

  const onClearHistory = async () => {
    try {
      await clearHistory();
      setHistory([]);
    } catch (e) {
      if (e.message === "UNAUTHORIZED") logout();
    }
  };

  if (booting) return <div className="splash">Loading...</div>;
  if (!user) return <AuthPage onAuthed={onAuthed} />;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-logo">
            <Icon name="shield" size={22} />
          </span>
          <div>
            <div className="brand-name">URLYZE AI</div>
            <div className="brand-sub">Analyze. Detect. Stay Safe.</div>
          </div>
        </div>
        <nav>
          {TABS.map((t) => (
            <button key={t.id} className={`nav-btn ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
              <Icon name={t.icon} /> {t.label}
            </button>
          ))}
        </nav>
        <ThemeToggle className="theme-side" />
        <div className="user-chip">
          <span className="avatar">{(user.name || user.email).charAt(0).toUpperCase()}</span>
          <div className="user-info">
            <b>{user.name || "Account"}</b>
            <span>{user.email}</span>
          </div>
          <button className="icon-btn" onClick={logout} title="Log out" aria-label="Log out">
            <Icon name="logout" size={18} />
          </button>
        </div>
      </aside>

      <main className="main">
        {tab === "scan" && <Scanner scan={scan} onScan={runScan} onReset={() => setScan(IDLE_SCAN)} />}
        {tab === "email" && (
          <EmailChecker state={email} onCheck={runEmail} onReset={() => setEmail(IDLE_EMAIL)} />
        )}
        {tab === "history" && <History history={history} onRescan={runScan} onClear={onClearHistory} />}
        {tab === "dash" && <Dashboard history={history} user={user} onLogout={logout} />}
      </main>

      <ThemeToggle compact className="theme-float" />

      <nav className="tabbar" aria-label="Main">
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
            <Icon name={t.icon} size={22} />
            <span>{t.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
