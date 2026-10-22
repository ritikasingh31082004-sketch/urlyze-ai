const PATHS = {
  shield: ["M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"],
  scan: ["M4 8V5a1 1 0 011-1h3", "M16 4h3a1 1 0 011 1v3", "M20 16v3a1 1 0 01-1 1h-3", "M8 20H5a1 1 0 01-1-1v-3", "M4 12h16"],
  clock: ["M12 3a9 9 0 100 18 9 9 0 000-18z", "M12 7v5l3 2"],
  chart: ["M4 20V10", "M10 20V4", "M16 20v-7", "M22 20H2"],
  link: ["M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1", "M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"],
  alert: ["M12 3l10 18H2L12 3z", "M12 10v5", "M12 18h.01"],
  check: ["M5 13l4 4L19 7"],
  info: ["M12 3a9 9 0 100 18 9 9 0 000-18z", "M12 11v5", "M12 8h.01"],
  trash: ["M4 7h16", "M9 7V4h6v3", "M6 7l1 13h10l1-13"],
  arrow: ["M5 12h14", "M13 6l6 6-6 6"],
  x: ["M6 6l12 12", "M18 6L6 18"],
  mail: ["M4 6h16v12H4z", "M4 7l8 6 8-6"],
  logout: ["M9 4H5v16h4", "M16 8l4 4-4 4", "M20 12H9"],
  lock: ["M6 11h12v9H6z", "M8 11V8a4 4 0 018 0v3"],
  user: ["M12 12a4 4 0 100-8 4 4 0 000 8z", "M4 21c0-4 4-6 8-6s8 2 8 6"],
};

export default function Icon({ name, size = 20 }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {(PATHS[name] || []).map((d, i) => (
        <path key={i} d={d} />
      ))}
    </svg>
  );
}
