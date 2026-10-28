# 🌾 FasalAI — Smart Agriculture for Pakistan

AI-powered crop disease diagnosis, market predictions, weather alerts, and expert farming advisory — in **Urdu** and **English** for Pakistani farmers.

## Architecture

```
┌─────────────────┐     ┌─────────────────────────────────────┐
│   Next.js UI    │────▶│  FastAPI Backend (:8000)             │
│   (:3000)       │     │                                     │
│  • Advisory     │     │  Routes: /advisory /diagnosis        │
│  • Diagnosis    │     │          /market /weather /farm      │
│  • Market       │     │                                     │
│  • Weather      │     │  Services:                          │
│  • Calendar     │     │  ├─ Agent Orchestrator (multi-agent) │
└─────────────────┘     │  ├─ RAG Service (TF-IDF in-memory)  │
                        │  ├─ Disease Classifier (ResNet50)    │
                        │  ├─ Market Prediction               │
                        │  ├─ Weather Service                  │
                        │  └─ Voice Service (gTTS/Whisper)     │
                        │                                     │
                        │  AI: Routeway AI                     │
                        │  ├─ gpt-oss-120b:free (primary)     │
                        │  └─ deepseek-r1:free (backup)       │
                        └─────────────────────────────────────┘
```

## Features

| Feature | Description |
|---------|-------------|
| 🔬 Disease Diagnosis | Upload a photo → CNN identifies disease + AI treatment plan |
| 💬 AI Advisory | Ask any farming question in English/Urdu/Roman Urdu |
| 📈 Market Prices | Real-time mandi prices + AI price predictions |
| 🌤️ Weather Impact | Crop-specific weather alerts and action plans |
| 📅 Crop Calendar | Province-specific planting & harvesting schedules |
| 🗣️ Bilingual | Full Urdu + English responses on every query |

## Prerequisites

- **Python** 3.11+ (for backend)
- **Node.js** 18+ (for frontend)
- **Routeway AI API Key** (free tier works)

## Quick Start

### 1. Clone & Configure

```bash
cd fasalai/backend
cp .env.example .env
# Edit .env → add your ROUTEWAY_API_KEY
```

### 2. Backend

```bash
cd fasalai/backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/docs
```

### 3. Frontend

```bash
cd fasalai/frontend
npm install
npm run dev
# → http://localhost:3000
```

### 4. One-Click (Windows)

```bash
# From fasalai/ root:
run_backend.bat   # starts backend
run_frontend.bat  # starts frontend
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ROUTEWAY_API_KEY` | ✅ | — | Routeway AI API key |
| `ROUTEWAY_API_URL` | No | `https://api.routeway.ai/v1` | API endpoint |
| `PRIMARY_MODEL` | No | `gpt-oss-120b:free` | Primary LLM model |
| `FAST_MODEL` | No | `gpt-oss-120b:free` | Fast model for quick queries |
| `BACKUP_MODEL` | No | `deepseek-r1:free` | Fallback model |
| `OPENWEATHER_API_KEY` | No | — | OpenWeatherMap key (mock data if blank) |
| `LLM_MAX_RETRIES` | No | `2` | LLM retry count |
| `LLM_TIMEOUT` | No | `60` | LLM timeout in seconds |
| `DEBUG` | No | `true` | Enable debug logging |

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health + model status |
| POST | `/advisory/ask` | Ask farming question |
| POST | `/advisory/quick` | Quick crop-specific query |
| POST | `/diagnosis/image` | Upload image for disease detection |
| POST | `/diagnosis/symptoms` | Text-based symptom diagnosis |
| GET | `/market/predict/{crop}` | Price predictions |
| GET | `/market/current/{crop}` | Current mandi prices |
| GET | `/market/trends/{crop}` | Historical price trends |
| GET | `/market/sell-advice/{crop}` | Best time to sell |
| GET | `/weather/current` | Current weather |
| GET | `/weather/forecast` | 7-day forecast |
| GET | `/weather/crop-impact` | Crop-specific weather analysis |
| GET | `/farm/calendar/{province}/{crop}` | Crop calendar |
| GET | `/farm/crops` | List supported crops |

## Docker

```bash
cd fasalai
docker-compose up --build
# Backend  → http://localhost:8000
# Frontend → http://localhost:3000
```

## Tech Stack

- **Backend:** FastAPI + Python 3.11+
- **Frontend:** Next.js 16 + TypeScript + Tailwind CSS v4
- **AI:** Routeway AI (GPT-OSS-120B, DeepSeek R1)
- **Vision:** ResNet50 CNN (33 crop diseases)
- **RAG:** In-memory TF-IDF (fast, no external deps)
- **Speech:** gTTS (text-to-speech)

## License

Made by **Hafiz Mustafa Murtaza** — AI Hackathon 2026
