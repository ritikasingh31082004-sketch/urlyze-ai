import { useState } from "react";

const KEY = "urlyze_theme_v1";
const current = () => (document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark");

function Sun() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 8a4 4 0 100 8 4 4 0 000-8z" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

function Moon() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" />
    </svg>
  );
}

export default function ThemeToggle({ compact = false, className = "" }) {
  const [theme, setTheme] = useState(current);

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* storage unavailable */
    }
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", next === "light" ? "#f2f6fc" : "#060a12");
    setTheme(next);
  };

  return (
    <button
      type="button"
      role="switch"
      aria-checked={theme === "light"}
      aria-label="Switch between light and dark mode"
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className={`theme-toggle ${compact ? "compact" : ""} ${className}`}
      onClick={toggle}
    >
      {!compact && <span className="tt-label">{theme === "dark" ? "Dark mode" : "Light mode"}</span>}
      <span className="tt-track">
        <span className="tt-icon tt-sun"><Sun /></span>
        <span className="tt-icon tt-moon"><Moon /></span>
        <span className="tt-knob" />
      </span>
    </button>
  );
}
