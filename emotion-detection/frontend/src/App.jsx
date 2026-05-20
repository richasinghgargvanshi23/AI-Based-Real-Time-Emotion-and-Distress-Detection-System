import { useState } from "react";
import Dashboard from "./components/Dashboard";
import EmotionMonitor from "./components/EmotionMonitor";
import SessionReport from "./components/SessionReport";

export default function App() {
  const [page, setPage] = useState("monitor"); // "monitor" | "report"
  const [sessionId] = useState(() => `session_${Date.now()}`);

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="header-brand">
          <span className="brand-icon">🧠</span>
          <span className="brand-name">EmoSense</span>
          <span className="brand-sub">AI Mental Wellness Monitor</span>
        </div>
        <nav className="header-nav">
          <button
            className={`nav-btn ${page === "monitor" ? "active" : ""}`}
            onClick={() => setPage("monitor")}
          >
            Live Monitor
          </button>
          <button
            className={`nav-btn ${page === "report" ? "active" : ""}`}
            onClick={() => setPage("report")}
          >
            Session Report
          </button>
        </nav>
      </header>

      <main className="app-main">
        {page === "monitor" ? (
          <EmotionMonitor sessionId={sessionId} />
        ) : (
          <SessionReport sessionId={sessionId} />
        )}
      </main>

      <footer className="app-footer">
        <span>EmoSense v1.0 — For educational & research purposes only</span>
        <span>⚠️ Not a medical device</span>
      </footer>
    </div>
  );
}
