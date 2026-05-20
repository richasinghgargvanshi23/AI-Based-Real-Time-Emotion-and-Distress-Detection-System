# 🧠 EmoSense — AI-Based Real-Time Emotion & Distress Detection System

> **Healthcare + Computer Vision** — Real-time facial emotion recognition and mental wellness monitoring using deep learning.

![Python](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green) ![React](https://img.shields.io/badge/React-18-61dafb) ![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16-orange) ![OpenCV](https://img.shields.io/badge/OpenCV-4.9-red)

---

## 📌 Overview

EmoSense detects 7 facial emotions in real-time from a webcam stream, computes a composite **distress score**, and alerts users when stress/distress indicators are elevated. Designed for mental wellness monitoring, assistive care, and healthcare research.

**Detected Emotions:** `angry` · `disgust` · `fear` · `happy` · `sad` · `surprise` · `neutral`

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (React)                     │
│  Webcam → Canvas → Base64 JPEG → WebSocket → Backend   │
│  ← Emotion JSON + Distress Score ← Analytics UI        │
└─────────────────────────────────────────────────────────┘
                          ↕ WebSocket / REST
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│  EmotionEngine (DeepFace / TF CNN)                      │
│  DistressAnalyzer → composite score                     │
│  SessionManager → timeline, report                      │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Tech Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Backend   | Python 3.11, FastAPI, WebSockets        |
| ML Engine | DeepFace (primary), TensorFlow/Keras CNN (custom) |
| Vision    | OpenCV 4.9, Haar Cascades               |
| Frontend  | React 18, Vite, plain CSS               |
| Deploy    | Docker + Docker Compose                 |

---

## 🚀 Quick Start

### Option 1 — Docker (recommended)

```bash
git clone https://github.com/YOUR_USERNAME/emosense.git
cd emosense
docker-compose up --build
```

Open http://localhost:3000

---

### Option 2 — Local Dev

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
Open http://localhost:3000

---

## 🧬 Training a Custom Model (Optional)

The system uses **DeepFace** by default (no training needed). To train your own CNN on FER2013:

1. Download FER2013 from [Kaggle](https://www.kaggle.com/datasets/msambare/fer2013)
2. Place `fer2013.csv` in `data/`
3. Run:
```bash
cd scripts
python train_model.py
```
The trained model is saved to `model/emotion_model.h5` and auto-loaded by the backend.

---

## 🔌 API Reference

| Method    | Endpoint                        | Description                     |
|-----------|---------------------------------|---------------------------------|
| GET       | `/health`                       | Health check                    |
| POST      | `/analyze/image`                | Analyze a single base64 frame   |
| WS        | `/ws/stream/{session_id}`       | Real-time stream analysis       |
| GET       | `/session/{id}/report`          | Session analytics report        |
| GET       | `/session/{id}/history`         | Raw emotion history             |
| DELETE    | `/session/{id}`                 | Delete session data             |

**POST `/analyze/image` example:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
  "faces": [{
    "bbox": {"x": 120, "y": 80, "w": 160, "h": 160},
    "emotions": {"happy": 0.72, "neutral": 0.18, "sad": 0.05, ...},
    "dominant_emotion": "happy",
    "confidence": 0.72,
    "age": 28,
    "gender": "Woman"
  }],
  "face_count": 1,
  "dominant_emotion": "happy",
  "distress": {
    "score": 0.12,
    "level": "calm",
    "alert": false,
    "wellness_score": 88.0,
    "recommendation": "You appear relaxed. Keep it up! 😊"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 📊 Distress Score

| Score     | Level     | Description                        |
|-----------|-----------|------------------------------------|
| 0.00–0.20 | Calm      | Relaxed, minimal stress            |
| 0.20–0.40 | Mild      | Slight tension                     |
| 0.40–0.60 | Moderate  | Noticeable stress indicators       |
| 0.60–0.80 | High      | Strong distress — alert triggered  |
| 0.80–1.00 | Critical  | Severe distress — urgent alert     |

---

## 📁 Project Structure

```
emosense/
├── backend/
│   ├── main.py               # FastAPI app, routes, WebSocket
│   ├── emotion_engine.py     # DeepFace + CNN inference
│   ├── distress_analyzer.py  # Distress scoring
│   ├── session_manager.py    # Session tracking & reports
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EmotionMonitor.jsx   # Main live monitor
│   │   │   ├── SessionReport.jsx   # Report view
│   │   │   ├── EmotionBar.jsx
│   │   │   ├── DistressGauge.jsx
│   │   │   └── AlertBanner.jsx
│   │   ├── hooks/useWebSocket.js
│   │   ├── utils/videoUtils.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── scripts/
│   └── train_model.py        # FER2013 training script
├── model/                    # Trained .h5 model goes here
├── data/                     # FER2013 CSV goes here
├── docker-compose.yml
└── README.md
```

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**. It is **not a certified medical device** and should not be used for clinical diagnosis or treatment decisions.

---

## 📄 License

MIT License — free to use, modify, and distribute.
