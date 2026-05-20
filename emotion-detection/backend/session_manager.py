"""
SessionManager
In-memory session tracking for emotion timelines and report generation.
In production, replace with Redis or a database.
"""

from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics
import logging

logger = logging.getLogger(__name__)

MAX_RECORDS_PER_SESSION = 1000  # ~33 minutes at 0.5 fps


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, dict] = {}

    def create_session(self, session_id: str):
        self._sessions[session_id] = {
            "id": session_id,
            "started_at": datetime.utcnow().isoformat(),
            "ended_at": None,
            "records": deque(maxlen=MAX_RECORDS_PER_SESSION),
            "alert_count": 0,
        }

    def add_record(self, session_id: str, result: dict):
        if session_id not in self._sessions:
            self.create_session(session_id)

        session = self._sessions[session_id]
        record = {
            "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
            "dominant_emotion": result.get("dominant_emotion", "neutral"),
            "face_count": result.get("face_count", 0),
            "distress_score": result.get("distress", {}).get("score", 0.0),
            "distress_level": result.get("distress", {}).get("level", "calm"),
            "wellness_score": result.get("distress", {}).get("wellness_score", 100.0),
            "alert": result.get("distress", {}).get("alert", False),
        }
        session["records"].append(record)

        if record["alert"]:
            session["alert_count"] += 1

    def get_history(self, session_id: str, limit: int = 100) -> List[dict]:
        session = self._sessions.get(session_id)
        if not session:
            return []
        records = list(session["records"])[-limit:]
        return records

    def generate_report(self, session_id: str) -> Optional[dict]:
        session = self._sessions.get(session_id)
        if not session:
            return None

        records = list(session["records"])
        if not records:
            return {
                "session_id": session_id,
                "started_at": session["started_at"],
                "ended_at": session["ended_at"],
                "duration_seconds": 0,
                "total_frames": 0,
                "summary": "No data recorded.",
            }

        distress_scores = [r["distress_score"] for r in records]
        wellness_scores = [r["wellness_score"] for r in records]
        emotions = [r["dominant_emotion"] for r in records]

        emotion_freq = {}
        for em in emotions:
            emotion_freq[em] = emotion_freq.get(em, 0) + 1

        dominant_overall = max(emotion_freq, key=emotion_freq.get)

        return {
            "session_id": session_id,
            "started_at": session["started_at"],
            "ended_at": session["ended_at"] or datetime.utcnow().isoformat(),
            "total_frames": len(records),
            "alert_count": session["alert_count"],
            "average_distress_score": round(statistics.mean(distress_scores), 4),
            "peak_distress_score": round(max(distress_scores), 4),
            "average_wellness_score": round(statistics.mean(wellness_scores), 2),
            "dominant_emotion_overall": dominant_overall,
            "emotion_distribution": {
                em: round(count / len(records), 3)
                for em, count in emotion_freq.items()
            },
            "timeline": [
                {
                    "timestamp": r["timestamp"],
                    "distress_score": r["distress_score"],
                    "wellness_score": r["wellness_score"],
                    "dominant_emotion": r["dominant_emotion"],
                    "alert": r["alert"],
                }
                for r in records[::max(1, len(records) // 100)]  # downsample to 100 pts
            ],
        }

    def end_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id]["ended_at"] = datetime.utcnow().isoformat()

    def delete_session(self, session_id: str):
        self._sessions.pop(session_id, None)
