import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function SessionReport({ sessionId }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/session/${sessionId}/report`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setReport(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [sessionId]);

  if (loading) return <div className="report-loading">Loading report…</div>;
  if (error) return <div className="report-error">No report available yet. Start monitoring first.</div>;
  if (!report) return null;

  const emotionDist = report.emotion_distribution || {};
  const sorted = Object.entries(emotionDist).sort((a, b) => b[1] - a[1]);

  const COLORS = {
    happy: "#00c9a7", neutral: "#8b9eb0", sad: "#5b8dee",
    angry: "#ff4757", fear: "#a55eea", surprise: "#ffa502", disgust: "#2ed573",
  };

  return (
    <div className="report-layout">
      <div className="report-header">
        <h2>Session Report</h2>
        <span className="session-id-badge">{sessionId}</span>
        <button className="btn-secondary" onClick={fetchReport}>↻ Refresh</button>
      </div>

      <div className="report-cards">
        <div className="stat-card">
          <div className="stat-value">{report.total_frames}</div>
          <div className="stat-label">Frames Analyzed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{(report.average_wellness_score || 0).toFixed(1)}%</div>
          <div className="stat-label">Avg Wellness</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{(report.average_distress_score * 100 || 0).toFixed(1)}</div>
          <div className="stat-label">Avg Distress</div>
        </div>
        <div className="stat-card alert-stat">
          <div className="stat-value">{report.alert_count}</div>
          <div className="stat-label">Alerts Triggered</div>
        </div>
      </div>

      <div className="report-section">
        <h3>Dominant Overall Emotion</h3>
        <div className="dominant-emotion-badge">
          {report.dominant_emotion_overall?.toUpperCase() || "N/A"}
        </div>
      </div>

      <div className="report-section">
        <h3>Emotion Distribution</h3>
        <div className="emotion-bars">
          {sorted.map(([emotion, frac]) => (
            <div className="emotion-row" key={emotion}>
              <span className="emotion-name">{emotion}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${frac * 100}%`, backgroundColor: COLORS[emotion] || "#666" }}
                />
              </div>
              <span className="bar-pct">{(frac * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>

      {report.timeline?.length > 1 && (
        <div className="report-section">
          <h3>Distress Timeline</h3>
          <TimelineChart timeline={report.timeline} />
        </div>
      )}
    </div>
  );
}

function TimelineChart({ timeline }) {
  const W = 600, H = 120;
  const scores = timeline.map((t) => t.distress_score || 0);
  const max = Math.max(...scores, 0.01);

  const points = scores.map((s, i) => {
    const x = (i / (scores.length - 1)) * W;
    const y = H - (s / max) * (H - 10) - 5;
    return `${x},${y}`;
  });

  const alertPoints = timeline
    .map((t, i) => ({ ...t, i }))
    .filter((t) => t.alert);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="report-timeline-svg">
      {/* Grid lines */}
      {[0.25, 0.5, 0.65, 1].map((v) => {
        const y = H - (v / max) * (H - 10) - 5;
        return (
          <line key={v} x1={0} y1={y} x2={W} y2={y}
            stroke={v === 0.65 ? "#ff444455" : "#ffffff10"} strokeWidth="1"
            strokeDasharray={v === 0.65 ? "6 4" : "none"} />
        );
      })}

      {/* Area fill */}
      <polygon
        points={`0,${H} ${points.join(" ")} ${W},${H}`}
        fill="#5b8dee22"
      />

      {/* Line */}
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke="#5b8dee"
        strokeWidth="2"
        strokeLinejoin="round"
      />

      {/* Alert markers */}
      {alertPoints.map(({ i }) => {
        const x = (i / (scores.length - 1)) * W;
        const y = H - (scores[i] / max) * (H - 10) - 5;
        return <circle key={i} cx={x} cy={y} r={4} fill="#ff4757" />;
      })}
    </svg>
  );
}
