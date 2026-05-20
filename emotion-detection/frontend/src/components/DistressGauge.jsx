export default function DistressGauge({ distress }) {
  if (!distress) return null;

  const { score, level, wellness_score } = distress;
  const pct = score * 100;

  const levelColors = {
    calm:     "#00c9a7",
    mild:     "#7bed9f",
    moderate: "#ffa502",
    high:     "#ff6348",
    critical: "#ff4757",
  };

  const color = levelColors[level] || "#aaa";

  // Arc SVG gauge
  const R = 54, CX = 70, CY = 70;
  const circumference = Math.PI * R; // half circle
  const dashOffset = circumference * (1 - score);

  return (
    <div className="distress-gauge-card">
      <h3 className="section-title">Distress Level</h3>
      <div className="gauge-container">
        <svg viewBox="0 0 140 80" className="gauge-svg">
          {/* Background arc */}
          <path
            d={`M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`}
            fill="none"
            stroke="#2a2a3a"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Filled arc */}
          <path
            d={`M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{ transition: "stroke-dashoffset 0.5s ease, stroke 0.5s ease" }}
          />
          {/* Score label */}
          <text x={CX} y={CY - 8} textAnchor="middle" className="gauge-score" fill={color}>
            {pct.toFixed(0)}
          </text>
          <text x={CX} y={CY + 6} textAnchor="middle" className="gauge-label" fill="#888">
            / 100
          </text>
        </svg>

        <div className="gauge-info">
          <div className="level-badge" style={{ backgroundColor: color + "22", color }}>
            {level.toUpperCase()}
          </div>
          <div className="wellness-row">
            <span className="wellness-label">Wellness</span>
            <span className="wellness-value">{wellness_score.toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
