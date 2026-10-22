import RiskMeter from "./RiskMeter.jsx";
import Icon from "./Icon.jsx";

const ORDER = { danger: 0, warning: 1, safe: 2 };
const ICON = { danger: "alert", warning: "alert", safe: "check" };

export default function ResultView({ result, onReset }) {
  const factors = [...result.factors].sort((a, b) => ORDER[a.type] - ORDER[b.type]);

  return (
    <div className="result">
      <div className={`card meter-card lvl-${result.level}`}>
        <RiskMeter score={result.risk_score} level={result.level} />
        <div className="verdict">{result.verdict}</div>
        <div className="host" title={result.host}>{result.host || result.url}</div>
        <div className="mini-stats">
          <div>
            <span>AI confidence</span>
            <b>{result.model_probability}%</b>
          </div>
          <div>
            <span>Trusted domain</span>
            <b>{result.trusted_domain ? "Yes" : "No"}</b>
          </div>
        </div>
        <button className="btn-ghost" onClick={onReset}>
          Scan another URL
        </button>
      </div>

      <div className="card factors-card">
        <h2>Risk analysis</h2>
        <ul className="factors">
          {factors.map((f, idx) => (
            <li key={idx} className={`factor ${f.type}`} style={{ animationDelay: `${idx * 90}ms` }}>
              <span className="factor-icon">
                <Icon name={ICON[f.type]} size={18} />
              </span>
              <div>
                <div className="factor-title">{f.title}</div>
                <div className="factor-detail">{f.detail}</div>
              </div>
            </li>
          ))}
        </ul>

        <details className="tech">
          <summary>Technical features used by the model</summary>
          <div className="tech-grid">
            {Object.entries(result.features).map(([k, v]) => (
              <div key={k} className="tech-row">
                <span>{k.replace(/_/g, " ")}</span>
                <b>{String(v)}</b>
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  );
}
