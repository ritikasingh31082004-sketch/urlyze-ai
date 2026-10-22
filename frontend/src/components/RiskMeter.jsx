import { useEffect, useState } from "react";

const ARC = 314.16; // length of the half circle (pi * r, r = 100)

export default function RiskMeter({ score, level }) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    let raf;
    const start = performance.now();
    const duration = 1200;
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(Math.round(score * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [score]);

  return (
    <div className={`meter lvl-${level}`}>
      <svg viewBox="0 0 240 135" className="meter-svg" role="img" aria-label={`Risk score ${score} percent`}>
        <path d="M20 120 A100 100 0 0 1 220 120" className="meter-track" />
        <path
          d="M20 120 A100 100 0 0 1 220 120"
          className="meter-fill"
          strokeDasharray={ARC}
          strokeDashoffset={ARC * (1 - shown / 100)}
        />
      </svg>
      <div className="meter-readout">
        <span className="meter-num">{shown}</span>
        <span className="meter-pct">%</span>
      </div>
      <div className="meter-level">{level} RISK</div>
    </div>
  );
}
