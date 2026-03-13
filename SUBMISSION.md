# Jazari — Gemini Live Agent Challenge Submission

## Category: Live Agents

## What it does

Jazari is a voice-first AI life coach that remembers you across sessions, forgets unimportant details naturally, and follows up on your goals proactively. Unlike generic assistants that reset every conversation, Jazari builds a persistent understanding of who you are using semantic multimodal memory.

## The Problem

Current AI assistants are goldfish — they forget everything between sessions. You tell them your name, your goals, your preferences... and next time, blank slate. This makes them useless as coaches, therapists, or mentors.

## The Solution

Jazari solves this with three innovations:

1. **Semantic Memory with Gemini Embedding 2**: Every memory (text, photo, voice note) is embedded into a shared 768-dimensional vector space. Ask "what did I eat?" and it finds photo memories via cross-modal search.

2. **Ebbinghaus Forgetting Curve**: Memories decay naturally based on importance and time since last access. Identity facts (name, job) persist for months. Casual observations ("weather is nice") fade in days. The formula: `retention = e^(-t/S)` where S = importance * 30.

3. **Proactive Coaching**: At session start, Jazari checks for decaying goals and brings them up naturally: "You mentioned wanting to run 5K two weeks ago. How's that going?" This makes Jazari feel like a real coach who cares.

## How we built it

- **Google ADK** for multi-agent orchestration (7 specialized agents)
- **Gemini 2.5 Flash Native Audio** for real-time voice conversation
- **Gemini Embedding 2** (gemini-embedding-exp-03-07) for multimodal memory vectors
- **Gemini Flash** for importance scoring and media description
- **Google Search** tool for grounding factual claims (nutrition, exercise)
- **LanceDB** for vector similarity search
- **Cloud Run** for hosting, **Firestore** for structured data, **Cloud Storage** for media
- **React + Vite** frontend with camera button and voice note long-press

## Architecture

See [docs/architecture.html](docs/architecture.html) for the interactive diagram.

```
User → Frontend (React) → WebSocket/REST → Cloud Run (FastAPI)
                                                │
                                          ADK Runner
                                                │
                                        Jazari Root Agent
                              ┌────┬────┬────┬────┬────┬────┐
                          Memory Career Health Finance Disc Search
                              │                              │
                          LanceDB                     Google Search
                        + Embedding 2                  (grounding)
                              │
                    Forgetting Curve + Importance Scoring
```

## Challenges we ran into

- **LanceDB on Cloud Run**: LanceDB uses local disk, but Cloud Run containers are ephemeral. Solved with Firestore backup/restore on startup.
- **google_search tool limitation**: Can't mix with FunctionTools in same agent. Solved by creating a dedicated search_agent sub-agent.
- **Multimodal embedding model**: Gemini Embedding 2 is experimental — API surface changed during development.

## What we learned

- The Ebbinghaus forgetting curve from 1885 applies surprisingly well to AI memory systems
- Proactive agent behavior (initiating topics) creates a dramatically more engaging experience than reactive-only agents
- Cross-modal search (text query finding photo memories) is a powerful demo moment

## What's next

- Real-time camera vision during conversation (Gemini Live API supports video)
- Push notifications for decaying goals
- Habit streak visualization dashboard
- Multi-user family coaching mode

## Built with

Google ADK, Gemini 2.5 Flash, Gemini Embedding 2, Gemini Live API, Google Search, LanceDB, Cloud Run, Firestore, Cloud Storage, FastAPI, React, Vite, TypeScript, Python

#GeminiLiveAgentChallenge
