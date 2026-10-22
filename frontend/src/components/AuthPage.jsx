import { useState } from "react";
import Icon from "./Icon.jsx";
import ThemeToggle from "./ThemeToggle.jsx";
import { login, register } from "../api.js";

export default function AuthPage({ onAuthed }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const switchMode = (m) => {
    setMode(m);
    setError("");
  };

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (mode === "signup" && password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      const data =
        mode === "login" ? await login(email, password) : await register(name, email, password);
      onAuthed(data.token, data.user);
    } catch (err) {
      setError(
        err.message === "OFFLINE"
          ? "Can't reach the URLYZE server. Make sure the backend is running."
          : err.message
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <ThemeToggle compact className="theme-corner" />
      <div className="auth-card">
        <div className="auth-brand">
          <span className="brand-logo">
            <Icon name="shield" size={24} />
          </span>
          <h1>
            URLYZE <span>AI</span>
          </h1>
          <p>Analyze. Detect. Stay Safe.</p>
        </div>

        <div className="auth-tabs" role="tablist">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => switchMode("login")}>
            Log in
          </button>
          <button type="button" className={mode === "signup" ? "active" : ""} onClick={() => switchMode("signup")}>
            Sign up
          </button>
        </div>

        <form onSubmit={submit} className="auth-form">
          {mode === "signup" && (
            <label className="field">
              <span>Name</span>
              <div className="field-box">
                <Icon name="user" size={18} />
                <input
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                  maxLength={60}
                />
              </div>
            </label>
          )}

          <label className="field">
            <span>Email</span>
            <div className="field-box">
              <Icon name="mail" size={18} />
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </label>

          <label className="field">
            <span>Password</span>
            <div className="field-box">
              <Icon name="lock" size={18} />
              <input
                type={show ? "text" : "password"}
                placeholder={mode === "signup" ? "At least 8 characters" : "Your password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
              />
              <button type="button" className="show-btn" onClick={() => setShow((s) => !s)}>
                {show ? "Hide" : "Show"}
              </button>
            </div>
          </label>

          {error && (
            <div className="auth-error" role="alert">
              <Icon name="alert" size={18} /> <span>{error}</span>
            </div>
          )}

          <button className="btn-primary" type="submit" disabled={busy}>
            {busy ? "PLEASE WAIT..." : mode === "login" ? "LOG IN" : "CREATE ACCOUNT"}
          </button>
        </form>

        <p className="auth-switch">
          {mode === "login" ? "New here?" : "Already have an account?"}{" "}
          <button type="button" onClick={() => switchMode(mode === "login" ? "signup" : "login")}>
            {mode === "login" ? "Create an account" : "Log in"}
          </button>
        </p>
      </div>
    </div>
  );
}
