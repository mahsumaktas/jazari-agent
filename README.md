# Jazari — Your AI Life Coach

> Named after [Al-Jazari](https://en.wikipedia.org/wiki/Al-Jazari), the 12th-century engineer from Diyarbakir who built the world's first programmable automata. Like his mechanical marvels, Jazari is systematic, precise, and ingenious — but now he coaches your life instead of powering fountains.

**"Jazari doesn't flatter. He coaches."**

## What is Jazari?

Jazari is a **voice-first AI life coach** that actually remembers you. Unlike generic assistants that reset every conversation, Jazari builds a persistent understanding of who you are, what you're working toward, and whether you're actually doing it.

Built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) — Category: **Live Agents**

### Features

- **Voice-first interaction** — Talk naturally using Gemini Live API with real-time bidirectional audio
- **Multi-agent orchestration** — 5 specialist coaches working under one unified personality via Google ADK
- **Persistent memory** — Remembers your name, goals, preferences, and progress across sessions
- **Honest coaching** — Not a yes-man. Celebrates real wins, calls out real failures
- **Multilingual** — Speaks your language (Turkish, English, and 40+ languages via Gemini)
- **Goal & habit tracking** — Career goals, health habits, spending, and discipline routines

### Architecture

```
User (Voice) → WebSocket → Cloud Run (FastAPI)
                                │
                          ADK Runner (run_live)
                                │
                        Jazari Root Agent
                    ┌───┬───┬───┬───┐
                Career Health Finance Discipline
                    └───┴───┴───┴───┘
                            │
                      Memory Agent → Firestore
```

See [docs/architecture.md](docs/architecture.md) for the full diagram.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | [Google ADK](https://google.github.io/adk-docs/) |
| Voice | Gemini Live API (bidirectional audio streaming) |
| Model | Gemini 2.5 Flash (native audio) |
| Backend | Python 3.12 + FastAPI |
| Frontend | React + Vite + Tailwind CSS |
| Database | Google Cloud Firestore |
| Deploy | Google Cloud Run |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Google Cloud account with billing enabled
- Gemini API key

### Local Development

```bash
# Clone
git clone https://github.com/mahsumaktas/jazari-agent.git
cd jazari-agent

# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env — add your GOOGLE_API_KEY

# Start Firestore emulator (optional, for local testing)
gcloud emulators firestore start --host-port=localhost:8080

# Start backend
python server/main.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — click the mic button to start talking.

### Cloud Deployment

```bash
# Set GCP project
gcloud config set project jazari-coach

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com firestore.googleapis.com secretmanager.googleapis.com

# Create Firestore
gcloud firestore databases create --location=us-central1

# Store API key
echo -n "YOUR_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# Deploy
gcloud builds submit --config cloudbuild.yaml
```

## The Coaches

| Agent | Domain | Personality |
|-------|--------|-------------|
| **Jazari** (Root) | Orchestration | Systematic, honest, adapts to your language |
| **Career Coach** | Goals, skills, milestones | Actionable, no vague advice |
| **Health Coach** | Fitness, nutrition, sleep | Celebrates streaks, rebuilds after breaks |
| **Finance Coach** | Spending, budgets, savings | Pattern-focused, no judgment on purchases |
| **Discipline Coach** | Habits, routines, accountability | The tough one — no excuses accepted |
| **Memory Agent** | Cross-session knowledge | Never forgets, never fabricates |

## Demo

[Watch the demo video →](TODO)

## License

MIT

---

Built for the **Gemini Live Agent Challenge 2026** by [Mahsum Aktas](https://github.com/mahsumaktas)
