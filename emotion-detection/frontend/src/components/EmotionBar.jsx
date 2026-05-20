// EmotionBar.jsx
export function EmotionBar({ emotions }) {
  if (!emotions) return null;
  const sorted = Object.entries(emotions).sort((a, b) => b[1] - a[1]);

  const COLORS = {
    happy:    "#00c9a7",
    neutral:  "#8b9eb0",
    sad:      "#5b8dee",
    angry:    "#ff4757",
    fear:     "#a55eea",
    surprise: "#ffa502",
    disgust:  "#2ed573",
  };

  return (
    <div className="emotion-bars">
      {sorted.map(([emotion, score]) => (
        <div className="emotion-row" key={emotion}>
          <span className="emotion-name">{emotion}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{
                width: `${score * 100}%`,
                backgroundColor: COLORS[emotion] || "#666",
              }}
            />
          </div>
          <span className="bar-pct">{(score * 100).toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}

export default EmotionBar;
