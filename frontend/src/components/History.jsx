import Icon from "./Icon.jsx";

export default function History({ history, onRescan, onClear }) {
  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Scan history</h1>
          <p className="muted">Your last {history.length} scans, saved to your account.</p>
        </div>
        {history.length > 0 && (
          <button className="btn-ghost small" onClick={onClear}>
            <Icon name="trash" size={16} /> Clear
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div className="card empty">
          <Icon name="clock" size={32} />
          <p>No scans yet. Analyze a URL or an email and it will appear here.</p>
        </div>
      ) : (
        <ul className="history">
          {history.map((h) => (
            <li key={h.id}>
              <button
                className={`history-item lvl-${h.level}`}
                onClick={() => h.kind === "url" && onRescan(h.subject)}
                style={h.kind === "url" ? undefined : { cursor: "default" }}
              >
                <span className="history-score">{h.risk_score}</span>
                <span className="history-main">
                  <span className="history-url">{h.subject}</span>
                  <span className="history-meta">
                    <span className="kind-badge">{h.kind === "email" ? "EMAIL" : "URL"}</span>
                    {h.verdict} · {new Date(h.created_at).toLocaleString()}
                  </span>
                </span>
                <span className="pill">{h.level}</span>
                {h.kind === "url" && <Icon name="arrow" size={16} />}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
