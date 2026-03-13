# Jazari — Your AI Life Coach

> Named after [Al-Jazari](https://en.wikipedia.org/wiki/Al-Jazari), the 12th-century engineer from Diyarbakir who built the world's first programmable automata. Like his mechanical marvels, Jazari is systematic, precise, and ingenious — but now he coaches your life instead of powering fountains.

**"Jazari doesn't flatter. He coaches."**

## The Problem

AI assistants today are goldfish — they forget everything between sessions. You share your goals, your struggles, your progress... and next time, blank slate. This makes them useless as real coaches.

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
- **Semantic memory** — LanceDB vector search with Gemini Embedding 2 for cross-session recall
- **Ebbinghaus forgetting curve** — Memories decay over time; important goals persist, small talk fades
- **Photo memory** — Take a photo of your meal, Jazari remembers it with multimodal embedding
- **Voice note memory** — Long-press mic to save voice notes as searchable memories
- **Cross-modal search** — Ask "what did I eat?" and find photo memories via text query
- **Proactive follow-up** — Jazari detects goals you haven't mentioned and brings them up
- **Google Search grounding** — Verified nutrition/exercise facts, no hallucinated calorie counts

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

See [docs/architecture.html](docs/architecture.html) for the full interactive architecture diagram.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Framework | [Google ADK](https://google.github.io/adk-docs/) |
| Voice | Gemini Live API (bidirectional audio streaming) |
| Model | Gemini 2.5 Flash (native audio) |
| Backend | Python 3.12 + FastAPI |
| Frontend | React + Vite + Tailwind CSS |
| Memory | LanceDB + Gemini Embedding 2 (768-dim vectors) |
| Database | Google Cloud Firestore |
| Media Storage | Google Cloud Storage |
| Search | Google Search (grounding via ADK) |
| Deploy | Google Cloud Run + Cloud Build |

## Setup

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
| **Search Agent** | Google Search grounding | Verified facts, no hallucination |

## Demo

[Watch the demo video →](TODO)

## License

MIT

---

Built for the **Gemini Live Agent Challenge 2026** by [Mahsum Aktas](https://github.com/mahsumaktas) #GeminiLiveAgentChallenge
