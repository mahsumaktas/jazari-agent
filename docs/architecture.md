# Jazari — System Architecture

## Overview

```
┌─────────────────────────────────────────────────────┐
│                    User (Browser)                    │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐│
│  │ Mic/Audio│  │Transcript│  │ Profile │ Dashboard ││
│  └─────┬────┘  └──────────┘  └────────────────────┘│
│        │ WebSocket (PCM audio + JSON transcripts)   │
└────────┼────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│              Google Cloud Run (FastAPI)             │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │           ADK Runner (run_live)               │  │
│  │                                               │  │
│  │  ┌────────────────────────────────────────┐   │  │
│  │  │         Jazari Root Agent              │   │  │
│  │  │    (Orchestrator + Personality)         │   │  │
│  │  └────────────┬───────────────────────────┘   │  │
│  │               │                               │  │
│  │    ┌──────────┼──────────┬──────────┐        │  │
│  │    ▼          ▼          ▼          ▼        │  │
│  │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐    │  │
│  │ │Career│ │Health│ │Finance│ │Discipline│    │  │
│  │ │Agent │ │Agent │ │Agent │ │  Agent   │    │  │
│  │ └──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘    │  │
│  │    │        │        │          │           │  │
│  │    └────────┴────┬───┴──────────┘           │  │
│  │                  │                          │  │
│  │           ┌──────▼──────┐                   │  │
│  │           │Memory Agent │                   │  │
│  │           └──────┬──────┘                   │  │
│  └──────────────────┼──────────────────────────┘  │
│                     │                              │
└─────────────────────┼──────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │   Google Firestore     │
         │                        │
         │  users/{id}/           │
         │  ├── profile           │
         │  ├── memories/         │
         │  ├── goals/            │
         │  ├── habits/           │
         │  ├── expenses/         │
         │  └── conversations/    │
         └────────────────────────┘
```

## Data Flow

1. **User speaks** → Browser captures audio (16kHz PCM) via Web Audio API
2. **Audio streams** → WebSocket to Cloud Run FastAPI backend
3. **ADK processes** → `runner.run_live()` handles STT, agent routing, tool calling, TTS
4. **Agent routes** → Root agent identifies intent, delegates to specialist (Career/Health/Finance/Discipline)
5. **Tools execute** → Firestore reads/writes (goals, habits, expenses, memories)
6. **Response streams** → Audio (24kHz PCM) + transcript back to browser via WebSocket
7. **Memory persists** → Key information stored in Firestore for cross-session recall

## Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Framework | Google ADK | Multi-agent orchestration, Live API integration |
| Voice Model | Gemini 2.5 Flash | Native audio processing, multilingual |
| Database | Cloud Firestore | Persistent user data, memories, goals |
| Backend | FastAPI + uvicorn | WebSocket server, static file serving |
| Frontend | React + Vite + Tailwind | Voice-first UI with dark/gold theme |
| Deploy | Cloud Run (2nd gen) | Serverless, WebSocket support, scale-to-zero |
