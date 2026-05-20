export default function AlertBanner({ level, recommendation }) {
  const isHigh = level === "high" || level === "critical";
  return (
    <div className={`alert-banner ${isHigh ? "alert-critical" : "alert-warning"}`}>
      <span className="alert-icon">{isHigh ? "🚨" : "⚠️"}</span>
      <div>
        <strong>{isHigh ? "High Distress Detected" : "Elevated Stress Detected"}</strong>
        <p>{recommendation}</p>
      </div>
    </div>
  );
}
