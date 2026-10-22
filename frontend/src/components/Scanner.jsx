import { useEffect, useState } from "react";
import Icon from "./Icon.jsx";
import Radar from "./Radar.jsx";
import ResultView from "./ResultView.jsx";

const STEPS = [
  { icon: "link", title: "Paste a URL", text: "Any website link you are unsure about." },
  { icon: "scan", title: "AI analyzes it", text: "A trained model studies the link's structure." },
  { icon: "shield", title: "Get a clear verdict", text: "A risk score with the reasons behind it." },
];

const EXAMPLES = ["github.com/anthropics", "paypal-secure-login.xyz/verify", "192.168.4.7/bank/login.php"];

export default function Scanner({ scan, onScan, onReset }) {
  const [value, setValue] = useState(scan.url || "");
  const scanning = scan.status === "scanning";

  useEffect(() => {
    setValue(scan.url || "");
  }, [scan.url]);

  const submit = (e) => {
    e.preventDefault();
    if (!scanning) onScan(value);
  };

  return (
    <section className="page">
      <header className="hero">
        <div className="hero-badge">
          <Icon name="shield" size={16} /> AI POWERED ANALYSIS
        </div>
        <h1>
          URLYZE <span>AI</span>
        </h1>
        <p className="hero-sub">Intelligent URL Security</p>
      </header>

      <form className="scan-form" onSubmit={submit}>
        <div className="input-wrap">
          <Icon name="link" />
          <input
            type="text"
            inputMode="url"
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
            placeholder="Enter a website URL..."
            value={value}
            onChange={(e) => setValue(e.target.value)}
            aria-label="URL to analyze"
          />
          {value && (
            <button type="button" className="clear" onClick={() => setValue("")} aria-label="Clear">
              <Icon name="x" size={16} />
            </button>
          )}
        </div>
        <button className="btn-primary" type="submit" disabled={scanning}>
          {scanning ? "ANALYZING..." : "ANALYZE URL"}
        </button>
      </form>

      {scan.status === "idle" && (
        <div className="chips">
          <span>Try:</span>
          {EXAMPLES.map((ex) => (
            <button key={ex} type="button" onClick={() => onScan(ex)}>
              {ex}
            </button>
          ))}
        </div>
      )}

      {scan.status === "idle" && (
        <>
          <div className="how">
            {STEPS.map((st, i) => (
              <div className="how-step" key={st.title}>
                <span className="how-num">{i + 1}</span>
                <span className="how-icon">
                  <Icon name={st.icon} size={22} />
                </span>
                <h3>{st.title}</h3>
                <p>{st.text}</p>
              </div>
            ))}
          </div>
          <div className="trust-row">
            <span>30+ security signals</span>
            <span>Explainable results</span>
            <span>Trained on 2 datasets</span>
          </div>
        </>
      )}

      {scanning && <Radar url={scan.url} />}

      {scan.status === "error" && (
        <div className="error-box">
          <Icon name="alert" /> <span>{scan.error}</span>
        </div>
      )}

      {scan.status === "done" && scan.result && <ResultView result={scan.result} onReset={onReset} />}

      <p className="tagline">Analyze. Detect. Stay Safe.</p>
    </section>
  );
}
