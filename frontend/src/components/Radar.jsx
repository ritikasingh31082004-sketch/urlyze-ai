import { useEffect, useState } from "react";

const STEPS = [
  "Parsing URL structure",
  "Extracting security features",
  "Running AI model",
  "Building risk report",
];

export default function Radar({ url }) {
  const [i, setI] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setI((n) => Math.min(n + 1, STEPS.length - 1)), 450);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="radar-card">
      <div className="radar">
        <div className="radar-sweep" />
        <div className="radar-dot" />
      </div>
      <div className="radar-text">
        <div className="radar-step">{STEPS[i]}...</div>
        <div className="radar-url">{url}</div>
      </div>
    </div>
  );
}
