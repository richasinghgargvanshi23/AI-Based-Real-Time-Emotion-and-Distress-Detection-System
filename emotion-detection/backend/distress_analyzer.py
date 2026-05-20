"""
DistressAnalyzer
Computes a composite distress/wellness score from emotion probabilities.
Also flags alert conditions for clinical or assistive applications.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# How much each emotion contributes to distress (0=calm, 1=highly distressed)
DISTRESS_WEIGHTS = {
    "angry":    0.80,
    "disgust":  0.55,
    "fear":     0.90,
    "happy":    0.00,
    "sad":      0.70,
    "surprise": 0.25,
    "neutral":  0.10,
}

ALERT_THRESHOLD = 0.65   # Above this -> alert
CONCERN_THRESHOLD = 0.40  # Above this -> concern


class DistressAnalyzer:
    def calculate_distress(self, faces: List[Dict]) -> Dict[str, Any]:
        """
        Compute distress info from a list of face analysis dicts.
        Returns:
            score: float 0–1
            level: "calm" | "mild" | "moderate" | "high" | "critical"
            alert: bool
            primary_stressor: str
            wellness_score: float 0–100
            recommendation: str
        """
        if not faces:
            return self._empty_result()

        # Average distress across all detected faces (primary face weighted more)
        scores = []
        primary_stressors = []

        for i, face in enumerate(faces):
            emotions = face.get("emotions", {})
            if not emotions:
                continue

            distress_score = sum(
                emotions.get(em, 0) * weight
                for em, weight in DISTRESS_WEIGHTS.items()
            )
            scores.append(distress_score)

            # Identify top distress-contributing emotion
            stressor = max(
                (em for em in emotions if em != "neutral" and em != "happy"),
                key=lambda e: emotions.get(e, 0) * DISTRESS_WEIGHTS.get(e, 0),
                default="neutral"
            )
            primary_stressors.append(stressor)

        if not scores:
            return self._empty_result()

        # Weight first face more heavily
        if len(scores) > 1:
            avg_score = scores[0] * 0.6 + sum(scores[1:]) * 0.4 / (len(scores) - 1)
        else:
            avg_score = scores[0]

        avg_score = min(max(avg_score, 0.0), 1.0)
        primary_stressor = primary_stressors[0] if primary_stressors else "neutral"

        level = self._score_to_level(avg_score)
        alert = avg_score >= ALERT_THRESHOLD
        wellness = round((1.0 - avg_score) * 100, 1)

        return {
            "score": round(avg_score, 4),
            "level": level,
            "alert": alert,
            "primary_stressor": primary_stressor,
            "wellness_score": wellness,
            "recommendation": self._get_recommendation(level, primary_stressor),
            "face_count": len(faces),
        }

    def _score_to_level(self, score: float) -> str:
        if score < 0.20:
            return "calm"
        elif score < 0.40:
            return "mild"
        elif score < 0.60:
            return "moderate"
        elif score < 0.80:
            return "high"
        return "critical"

    def _get_recommendation(self, level: str, stressor: str) -> str:
        recs = {
            "calm": "You appear relaxed. Keep it up! 😊",
            "mild": "Slight tension detected. Consider a short breathing exercise.",
            "moderate": "Moderate stress signals detected. Try box breathing: inhale 4s, hold 4s, exhale 4s.",
            "high": "High distress detected. Please take a break and talk to someone you trust.",
            "critical": "Critical distress signals detected. Please seek immediate support or contact a mental health professional.",
        }

        stressor_additions = {
            "fear":  " (Fear indicators present — grounding exercises may help.)",
            "angry": " (Frustration signals detected — try progressive muscle relaxation.)",
            "sad":   " (Sadness indicators present — reaching out to a friend can help.)",
        }

        return recs.get(level, "") + stressor_additions.get(stressor, "")

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "score": 0.0,
            "level": "calm",
            "alert": False,
            "primary_stressor": "none",
            "wellness_score": 100.0,
            "recommendation": "No face detected.",
            "face_count": 0,
        }
