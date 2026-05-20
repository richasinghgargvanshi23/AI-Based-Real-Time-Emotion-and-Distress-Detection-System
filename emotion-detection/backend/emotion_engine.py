"""
EmotionEngine - Core facial emotion recognition using DeepFace + OpenCV
Supports: FER2013 model via DeepFace, with fallback to Haar cascade + rule-based
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Emotion labels matching FER2013 dataset
EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

EMOTION_COLORS = {
    "angry":    (0,   0,   220),
    "disgust":  (0,   140, 0  ),
    "fear":     (128, 0,   128),
    "happy":    (0,   200, 100),
    "sad":      (200, 80,  0  ),
    "surprise": (0,   180, 220),
    "neutral":  (180, 180, 180),
}


class EmotionEngine:
    def __init__(self):
        self._loaded = False
        self._use_deepface = False
        self._face_cascade = None
        self._model = None
        self._load_models()

    def _load_models(self):
        """Load DeepFace (preferred) or fallback to Haar + simple CNN."""
        # Try DeepFace first
        try:
            from deepface import DeepFace
            self._deepface = DeepFace
            self._use_deepface = True
            self._loaded = True
            logger.info("✅ DeepFace loaded successfully")
        except ImportError:
            logger.warning("DeepFace not available, using fallback detector")
            self._use_deepface = False

        # Always load Haar cascade as fallback face detector
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
            if not self._use_deepface:
                self._loaded = True
                logger.info("✅ Haar cascade face detector loaded (fallback mode)")
        except Exception as e:
            logger.error(f"Failed to load face cascade: {e}")

        # Try to load custom TF/Keras model if available
        try:
            import tensorflow as tf
            import os
            model_path = os.path.join(os.path.dirname(__file__), "../model/emotion_model.h5")
            if os.path.exists(model_path):
                self._model = tf.keras.models.load_model(model_path)
                logger.info("✅ Custom TF model loaded")
        except Exception:
            pass

    def is_loaded(self) -> bool:
        return self._loaded

    def analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Analyze a single BGR frame. Returns dict with:
          - faces: list of face analysis results
          - face_count: int
          - dominant_emotion: str
          - annotated_frame_b64: base64 JPEG with drawn boxes (optional)
        """
        if frame is None or frame.size == 0:
            return {"faces": [], "face_count": 0, "error": "Empty frame"}

        if self._use_deepface:
            return self._analyze_deepface(frame)
        return self._analyze_fallback(frame)

    def _analyze_deepface(self, frame: np.ndarray) -> Dict[str, Any]:
        try:
            results = self._deepface.analyze(
                frame,
                actions=["emotion", "age", "gender"],
                enforce_detection=False,
                silent=True,
            )

            # DeepFace returns list or dict depending on face count
            if isinstance(results, dict):
                results = [results]

            faces = []
            for r in results:
                emotions = r.get("emotion", {})
                dominant = r.get("dominant_emotion", "neutral")
                region = r.get("region", {})

                face_data = {
                    "bbox": {
                        "x": region.get("x", 0),
                        "y": region.get("y", 0),
                        "w": region.get("w", 0),
                        "h": region.get("h", 0),
                    },
                    "emotions": {k.lower(): round(float(v), 2) for k, v in emotions.items()},
                    "dominant_emotion": dominant.lower(),
                    "confidence": round(float(emotions.get(dominant, 0)), 2),
                    "age": r.get("age"),
                    "gender": r.get("dominant_gender"),
                }
                faces.append(face_data)

            dominant = faces[0]["dominant_emotion"] if faces else "none"
            return {
                "faces": faces,
                "face_count": len(faces),
                "dominant_emotion": dominant,
            }
        except Exception as e:
            logger.warning(f"DeepFace analysis failed: {e}")
            return self._analyze_fallback(frame)

    def _analyze_fallback(self, frame: np.ndarray) -> Dict[str, Any]:
        """Haar cascade + rule-based emotion estimation."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces_rects = []

        if self._face_cascade:
            faces_rects = self._face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48)
            )

        faces = []
        for (x, y, w, h) in faces_rects:
            face_roi = gray[y:y+h, x:x+w]
            emotions = self._estimate_emotion_from_roi(face_roi)
            dominant = max(emotions, key=emotions.get)
            faces.append({
                "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                "emotions": emotions,
                "dominant_emotion": dominant,
                "confidence": round(emotions[dominant], 2),
                "age": None,
                "gender": None,
            })

        dominant = faces[0]["dominant_emotion"] if faces else "none"
        return {
            "faces": faces,
            "face_count": len(faces),
            "dominant_emotion": dominant,
        }

    def _estimate_emotion_from_roi(self, roi: np.ndarray) -> Dict[str, float]:
        """
        Simple rule-based emotion proxy from facial ROI statistics.
        In production, replace this with inference from self._model.
        """
        if self._model is not None:
            return self._infer_from_model(roi)

        # Fallback: derive rough proxy from pixel distribution
        roi_resized = cv2.resize(roi, (48, 48))
        mean_val = float(np.mean(roi_resized))
        std_val = float(np.std(roi_resized))
        upper_half_mean = float(np.mean(roi_resized[:24, :]))
        lower_half_mean = float(np.mean(roi_resized[24:, :]))

        # Heuristic: high variance in lower half may indicate open mouth (happy/surprise)
        emotions = {e: 0.0 for e in EMOTIONS}
        base = 1.0 / len(EMOTIONS)
        for e in EMOTIONS:
            emotions[e] = base

        # Very rough heuristic — replaced by CNN in real deployment
        if std_val > 60:
            emotions["happy"] += 0.25
            emotions["surprise"] += 0.15
        if mean_val < 100:
            emotions["sad"] += 0.2
            emotions["fear"] += 0.1
        if lower_half_mean > upper_half_mean + 20:
            emotions["happy"] += 0.2
        if upper_half_mean > lower_half_mean + 20:
            emotions["angry"] += 0.2

        total = sum(emotions.values())
        return {k: round(v / total, 4) for k, v in emotions.items()}

    def _infer_from_model(self, roi: np.ndarray) -> Dict[str, float]:
        """Run inference on loaded Keras model."""
        try:
            roi_resized = cv2.resize(roi, (48, 48)).astype("float32") / 255.0
            roi_input = roi_resized.reshape(1, 48, 48, 1)
            predictions = self._model.predict(roi_input, verbose=0)[0]
            return {EMOTIONS[i]: round(float(predictions[i]), 4) for i in range(len(EMOTIONS))}
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            return {e: round(1.0 / len(EMOTIONS), 4) for e in EMOTIONS}

    def draw_annotations(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        """Draw bounding boxes and emotion labels on frame."""
        annotated = frame.copy()
        for face in result.get("faces", []):
            bbox = face["bbox"]
            emotion = face["dominant_emotion"]
            confidence = face["confidence"]
            color = EMOTION_COLORS.get(emotion, (255, 255, 255))

            x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            label = f"{emotion.upper()} {confidence:.0%}"
            cv2.putText(annotated, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

            # Draw mini emotion bar
            bar_x = x
            bar_y = y + h + 8
            bar_w = w
            bar_h = 6
            for i, (em, score) in enumerate(
                sorted(face["emotions"].items(), key=lambda x: -x[1])[:4]
            ):
                segment_w = int(bar_w * score)
                seg_color = EMOTION_COLORS.get(em, (200, 200, 200))
                cv2.rectangle(annotated, (bar_x, bar_y + i * 8),
                              (bar_x + segment_w, bar_y + i * 8 + 5), seg_color, -1)

        return annotated
