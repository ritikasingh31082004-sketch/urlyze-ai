import { useEffect, useState } from "react";
import { getModelInfo } from "../api.js";

const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const CHARTS = [
  { file: "confusion_matrix.png", label: "Confusion matrix" },
  { file: "roc_curves.png", label: "ROC curves" },
  { file: "feature_importance.png", label: "Top features used by the model" },
  { file: "model_comparison.png", label: "Model comparison" },
];

const pct = (v) => (parseFloat(v) * 100).toFixed(1);

export default function Dashboard({ history, user, onLogout }) {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getModelInfo()
      .then(setInfo)
      .catch(() => setError("Start the backend to see model performance."));
  }, []);

  const counts = { LOW: 0, MEDIUM: 0, HIGH: 0 };
  history.forEach((h) => {
    if (counts[h.level] !== undefined) counts[h.level] += 1;
  });
  const total = history.length;
  const seg = (n) => (total ? (n / total) * 100 : 0);

  const best = info?.metadata?.metrics;

  return (
    <section className="page">
      <h1 className="page-title">Dashboard</h1>

      {user && (
        <div className="card account-card">
          <div>
            <div className="account-name">{user.name || "Your account"}</div>
            <div className="muted">{user.email}</div>
          </div>
          <button className="btn-ghost small" onClick={onLogout}>
            Log out
          </button>
        </div>
      )}

      <div className="card">
        <h2>Your activity</h2>
        <div className="stat-row">
          <div className="stat">
            <b>{total}</b>
            <span>Total scans</span>
          </div>
          <div className="stat lvl-LOW">
            <b>{counts.LOW}</b>
            <span>Low risk</span>
          </div>
          <div className="stat lvl-MEDIUM">
            <b>{counts.MEDIUM}</b>
            <span>Medium</span>
          </div>
          <div className="stat lvl-HIGH">
            <b>{counts.HIGH}</b>
            <span>High risk</span>
          </div>
        </div>
        <p className="muted" style={{ marginBottom: 12 }}>
          {history.filter((h) => h.kind === "url").length} URL scans ·{" "}
          {history.filter((h) => h.kind === "email").length} email checks
        </p>
        <div className="stackbar" aria-hidden="true">
          <i className="lvl-LOW" style={{ width: `${seg(counts.LOW)}%` }} />
          <i className="lvl-MEDIUM" style={{ width: `${seg(counts.MEDIUM)}%` }} />
          <i className="lvl-HIGH" style={{ width: `${seg(counts.HIGH)}%` }} />
        </div>
      </div>

      <div className="card">
        <h2>Model performance</h2>
        {error && <p className="muted">{error}</p>}
        {!info && !error && <p className="muted">Loading...</p>}

        {info && best && (
          <>
            <p className="muted">
              Best model: <b className="accent">{info.metadata.best_model}</b> · tested on{" "}
              {info.metadata.test_size?.toLocaleString()} URLs from unseen domains
            </p>
            <div className="stat-row">
              {["accuracy", "precision", "recall", "f1", "roc_auc"].map((k) => (
                <div className="stat" key={k}>
                  <b>{pct(best[k])}%</b>
                  <span>{k === "roc_auc" ? "ROC-AUC" : k === "f1" ? "F1-score" : k}</span>
                </div>
              ))}
            </div>
          </>
        )}

        {info && info.comparison.length > 0 && (
          <div className="compare">
            <h3>Model comparison (F1-score)</h3>
            {info.comparison.map((m) => (
              <div className="bar-row" key={m.model}>
                <span className="bar-label">{m.model}</span>
                <div className="bar-track">
                  <i style={{ width: `${pct(m.f1)}%` }} />
                </div>
                <b>{pct(m.f1)}%</b>
              </div>
            ))}
          </div>
        )}
      </div>
      {info && (
        <div className="card">
          <h2>Evaluation charts</h2>
          <p className="muted">Generated during training on unseen test data. Click a chart to enlarge.</p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: 16,
              marginTop: 14,
            }}
          >
            {CHARTS.map((c) => (
              <a
                key={c.file}
                href={`${BASE}/reports/${c.file}`}
                target="_blank"
                rel="noreferrer"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <img
                  src={`${BASE}/reports/${c.file}`}
                  alt={c.label}
                  loading="lazy"
                  style={{ width: "100%", display: "block", borderRadius: 12, background: "#fff" }}
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
                <div className="muted" style={{ marginTop: 8 }}>{c.label}</div>
              </a>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
