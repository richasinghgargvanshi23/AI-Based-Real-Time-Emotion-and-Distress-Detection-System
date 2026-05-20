import { useEffect, useRef, useState, useCallback } from "react";
import useWebSocket from "../hooks/useWebSocket";
import EmotionBar from "./EmotionBar";
import DistressGauge from "./DistressGauge";
import AlertBanner from "./AlertBanner";
import { captureFrame } from "../utils/videoUtils";

const API_WS = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
const FRAME_INTERVAL_MS = 400; // ~2.5 fps

const EMOTION_EMOJI = {
  happy: "😊",
  sad: "😢",
  angry: "😠",
  fear: "😨",
  surprise: "😮",
  disgust: "🤢",
  neutral: "😐",
  none: "🔍",
};

export default function EmotionMonitor({ sessionId }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);
  const [fps, setFps] = useState(0);
  const frameCountRef = useRef(0);
  const fpsTimerRef = useRef(null);

  const wsUrl = `${API_WS}/ws/stream/${sessionId}`;
  const { sendMessage, lastMessage, connected } = useWebSocket(wsUrl);

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;
    try {
      const data = JSON.parse(lastMessage);
      setCurrentResult(data);
      setHistory((prev) => [...prev.slice(-59), data]);
    } catch (e) {
      console.error("Parse error:", e);
    }
  }, [lastMessage]);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsStreaming(true);
      setError(null);

      // Start sending frames
      intervalRef.current = setInterval(() => {
        if (videoRef.current && canvasRef.current && connected) {
          const frame = captureFrame(videoRef.current, canvasRef.current, 640, 480);
          if (frame) {
            sendMessage(JSON.stringify({ type: "frame", data: frame }));
            frameCountRef.current++;
          }
        }
      }, FRAME_INTERVAL_MS);

      // FPS counter
      fpsTimerRef.current = setInterval(() => {
        setFps(frameCountRef.current);
        frameCountRef.current = 0;
      }, 1000);
    } catch (err) {
      setError(`Camera access denied: ${err.message}`);
    }
  }, [connected, sendMessage]);

  const stopCamera = useCallback(() => {
    clearInterval(intervalRef.current);
    clearInterval(fpsTimerRef.current);
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
    setCurrentResult(null);
  }, []);

  useEffect(() => () => stopCamera(), []);

  const faces = currentResult?.faces || [];
  const primaryFace = faces[0];
  const distress = currentResult?.distress;
  const dominantEmotion = currentResult?.dominant_emotion || "none";

  return (
    <div className="monitor-layout">
      {/* LEFT: Video feed */}
      <div className="video-panel">
        <div className="video-wrapper">
          <video ref={videoRef} className="video-feed" playsInline muted />
          <canvas ref={canvasRef} style={{ display: "none" }} />

          {!isStreaming && (
            <div className="video-placeholder">
              <span className="placeholder-icon">📷</span>
              <p>Camera not active</p>
            </div>
          )}

          {isStreaming && (
            <div className="video-overlay">
              <span className={`status-dot ${connected ? "connected" : "disconnected"}`} />
              <span className="fps-counter">{fps} fps</span>
            </div>
          )}
        </div>

        <div className="camera-controls">
          {!isStreaming ? (
            <button className="btn-primary" onClick={startCamera}>
              ▶ Start Monitor
            </button>
          ) : (
            <button className="btn-danger" onClick={stopCamera}>
              ⏹ Stop
            </button>
          )}
        </div>

        {error && <div className="error-banner">{error}</div>}

        {/* Face count badge */}
        {isStreaming && (
          <div className="face-count-bar">
            {faces.length === 0
              ? "No face detected"
              : `${faces.length} face${faces.length > 1 ? "s" : ""} detected`}
          </div>
        )}
      </div>

      {/* RIGHT: Analytics */}
      <div className="analytics-panel">
        {distress?.alert && (
          <AlertBanner level={distress.level} recommendation={distress.recommendation} />
        )}

        {/* Dominant emotion display */}
        <div className="emotion-card big-emotion">
          <div className="emotion-emoji">{EMOTION_EMOJI[dominantEmotion] || "🔍"}</div>
          <div className="emotion-label">{dominantEmotion.toUpperCase()}</div>
          {primaryFace && (
            <div className="emotion-confidence">
              {(primaryFace.confidence * 100).toFixed(1)}% confidence
            </div>
          )}
        </div>

        {/* Distress gauge */}
        {distress && <DistressGauge distress={distress} />}

        {/* Per-emotion breakdown */}
        {primaryFace?.emotions && (
          <div className="emotion-breakdown">
            <h3 className="section-title">Emotion Breakdown</h3>
            <EmotionBar emotions={primaryFace.emotions} />
          </div>
        )}

        {/* Demographics (if available) */}
        {primaryFace?.age && (
          <div className="demo-card">
            <span>Age estimate: <strong>{primaryFace.age}</strong></span>
            {primaryFace.gender && (
              <span>Gender: <strong>{primaryFace.gender}</strong></span>
            )}
          </div>
        )}

        {/* Recommendation */}
        {distress?.recommendation && (
          <div className="recommendation-card">
            <span className="rec-icon">💡</span>
            <p>{distress.recommendation}</p>
          </div>
        )}

        {/* Timeline sparkline */}
        {history.length > 1 && (
          <div className="timeline-section">
            <h3 className="section-title">Distress Timeline</h3>
            <DistressTimeline history={history} />
          </div>
        )}
      </div>
    </div>
  );
}

function DistressTimeline({ history }) {
  const scores = history.map((h) => h.distress?.score || 0);
  const max = Math.max(...scores, 0.01);
  const W = 300, H = 60;

  const points = scores.map((s, i) => {
    const x = (i / (scores.length - 1)) * W;
    const y = H - (s / max) * (H - 4) - 2;
    return `${x},${y}`;
  });

  const alertColor = scores[scores.length - 1] > 0.65 ? "#ff4444" : "#00c9a7";

  return (
    <svg width={W} height={H} className="timeline-svg">
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={alertColor}
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {/* Threshold line */}
      <line
        x1={0} y1={H - (0.65 / max) * (H - 4) - 2}
        x2={W} y2={H - (0.65 / max) * (H - 4) - 2}
        stroke="#ff444455"
        strokeDasharray="4 4"
        strokeWidth="1"
      />
    </svg>
  );
}
