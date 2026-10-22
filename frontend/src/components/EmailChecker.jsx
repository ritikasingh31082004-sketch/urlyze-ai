import { useEffect, useState } from "react";
import Icon from "./Icon.jsx";
import Radar from "./Radar.jsx";
import RiskMeter from "./RiskMeter.jsx";

const SAMPLE = `From: PayPal Support <security@paypa1-verify.xyz>
Subject: URGENT: Your account will be suspended

Dear customer,

We detected unusual activity on your account. You must verify your account immediately and confirm your password within 24 hours or your account will be suspended.

Click here to verify: http://paypal-secure-login.xyz/verify

PayPal Security Team`;

const ORDER = { danger: 0, warning: 1, safe: 2 };
const ICON = { danger: "alert", warning: "alert", safe: "check" };

function EmailResult({ result, onReset }) {
  const factors = [...result.factors].sort((a, b) => ORDER[a.type] - ORDER[b.type]);
  return (
    <div className="result">
      <div className={`card meter-card lvl-${result.level}`}>
        <RiskMeter score={result.risk_score} level={result.level} />
        <div className="verdict">{result.verdict}</div>
        <div className="host" title={result.subject}>
          {result.subject || "Email analysis"}
        </div>
        <div className="mini-stats">
          <div>
            <span>Links found</span>
            <b>{result.links.length}</b>
          </div>
          <div>
            <span>Red flags</span>
            <b>{result.factors.filter((f) => f.type !== "safe").length}</b>
          </div>
        </div>
        <button className="btn-ghost" onClick={onReset}>
          Check another email
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

        {result.links.length > 0 && (
          <div className="links-box">
            <h3>Links in this email</h3>
            {result.links.map((l, i) => (
              <div key={i} className={`link-row lvl-${l.level}`}>
                <span className="link-url">{l.url}</span>
                <span className="pill">
                  {l.risk_score}% {l.level}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function EmailChecker({ state, onCheck, onReset }) {
  const [value, setValue] = useState(state.text || "");
  const checking = state.status === "scanning";

  useEffect(() => {
    setValue(state.text || "");
  }, [state.text]);

  const submit = (e) => {
    e.preventDefault();
    if (!checking) onCheck(value);
  };

  return (
    <section className="page">
      <header className="page-head">
        <div>
          <h1 className="page-title">Email checker</h1>
          <p className="muted">Paste a suspicious email (include the From and Subject lines if you can).</p>
        </div>
      </header>

      <form className="email-form" onSubmit={submit}>
        <textarea
          className="email-box"
          placeholder="Paste the email text here..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          spellCheck={false}
          rows={9}
          aria-label="Email text"
        />
        <div className="email-actions">
          <button type="button" className="btn-ghost small" onClick={() => setValue(SAMPLE)}>
            Try a sample phishing email
          </button>
          {value && (
            <button type="button" className="btn-ghost small" onClick={() => setValue("")}>
              Clear
            </button>
          )}
          <button className="btn-primary email-submit" type="submit" disabled={checking}>
            {checking ? "ANALYZING..." : "CHECK EMAIL"}
          </button>
        </div>
      </form>

      {checking && <Radar url="Reading the email and scanning its links" />}

      {state.status === "error" && (
        <div className="error-box">
          <Icon name="alert" /> <span>{state.error}</span>
        </div>
      )}

      {state.status === "done" && state.result && <EmailResult result={state.result} onReset={onReset} />}
    </section>
  );
}
