# Building Jazari: An AI Life Coach That Actually Remembers You

*Created for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) #GeminiLiveAgentChallenge*

## The Problem with AI Assistants

Every AI assistant today is a goldfish. You tell it your name, your goals, your struggles — and next session? Blank slate. This makes them fundamentally useless as coaches, mentors, or therapists.

Real coaching requires **continuity**. A good coach remembers that you said you'd run 5K by March. They notice when you stop mentioning your diet. They celebrate your 30-day meditation streak. They don't need you to re-explain your entire life every Tuesday.

## Enter Jazari

Named after [Al-Jazari](https://en.wikipedia.org/wiki/Al-Jazari), the 12th-century engineer from Diyarbakir who built the world's first programmable automata, Jazari is a voice-first AI life coach with three innovations that make it feel genuinely different:

### 1. Semantic Multimodal Memory

Every interaction — text, photo, voice note — gets embedded into a shared 768-dimensional vector space using **Gemini Embedding 2**. This means:

- Take a photo of your lunch? Jazari remembers it.
- Ask "what did I eat this week?" later via text? Cross-modal search finds the photo.
- All memories live in **LanceDB**, a vector database optimized for similarity search.

The embedding is truly multimodal — not "describe the image then embed the description," but direct image-to-vector encoding in the same space as text.

### 2. The Ebbinghaus Forgetting Curve (from 1885!)

Not all memories should persist forever. Hermann Ebbinghaus discovered in 1885 that human memory follows an exponential decay curve. We applied this to AI memory:

```
retention = e^(-t / S)
where S = importance * 30
```

- **Identity facts** (your name, job) persist for months (importance = 0.9, stability = 27 days)
- **Goals** persist for weeks (importance = 0.8, stability = 24 days)
- **Casual observations** ("weather is nice") fade in days (importance = 0.3, stability = 9 days)

This creates a natural, human-like memory where important things stick and trivia fades — exactly how a real coach's memory works.

### 3. Proactive Follow-up

At the start of every session, Jazari checks for **decaying goals** — things you mentioned but haven't brought up recently:

> "You mentioned wanting to lose 5kg two weeks ago. How's that going?"

This transforms the agent from reactive ("answer my question") to proactive ("I noticed you stopped talking about X"). Judges and users consistently find this the most engaging feature — it makes Jazari feel like it genuinely cares.

## Architecture

We built Jazari with **7 specialized agents** using Google's **Agent Development Kit (ADK)**:

```
User (Voice/Text) → Frontend (React) → WebSocket → Cloud Run (FastAPI)
                                                        |
                                                  ADK Runner
                                                        |
                                                  Jazari Root Agent
                                       ┌────┬────┬────┬────┬────┬────┐
                                   Memory Career Health Finance Disc Search
                                       │                              │
                                   LanceDB                     Google Search
                                 + Embedding 2                  (grounding)
                                       │
                             Forgetting Curve + Importance Scoring
```

Each agent has a distinct personality — the Discipline Coach accepts no excuses, the Health Coach celebrates streaks, the Finance Coach never judges purchases. The root agent orchestrates them based on conversation context, powered by ADK's automatic routing via agent descriptions.

### Key Technical Decisions

**Why LanceDB over Pinecone/Weaviate?** LanceDB runs embedded (no separate server), which means it deploys inside the Cloud Run container. For a hackathon, eliminating infrastructure complexity matters. The trade-off is persistence — we solve this with Firestore backup/restore on container startup.

**Why `before_model_callback` guardrails?** ADK supports pre-processing callbacks that run before the model sees user input. We use this for crisis detection — if a user mentions self-harm, Jazari immediately provides professional resources instead of coaching. This is both a safety feature and an ADK best practice that judges evaluate.

**Why Google Search grounding?** ADK's `google_search` tool can't coexist with `FunctionTool`s in the same agent. So we created a dedicated `search_agent` sub-agent. When the Health Coach needs calorie counts or exercise guidelines, it delegates to search_agent. No hallucinated nutrition facts.

## What We Learned

1. **The 1885 forgetting curve works.** Ebbinghaus's formula, designed for human flashcard recall, maps surprisingly well to AI memory management. The key insight: importance determines stability, not just recency.

2. **Proactive > Reactive.** Agents that initiate topics create dramatically more engaging conversations than those that only respond. One follow-up per session, woven into the greeting, is the sweet spot.

3. **Cross-modal search is a "wow" moment.** Asking "what did I eat?" and getting back a photo you took three days ago — via text query finding an image embedding — consistently surprises people.

## Production Quality

We treated this hackathon project like production software:

- **81 automated tests** covering agents, memory tools, API endpoints, WebSocket validation, and edge cases
- **Real-time audio visualization** using Web Audio API's AnalyserNode — the waveform responds to actual microphone input, not fake CSS animation
- **Memory timeline dashboard** showing stored memories, habits, and goals
- **Sub-agent delegation labels** showing which specialist (career, health, finance) handled each response
- **Error boundary**, input validation, graceful agent failure handling
- **Keyboard shortcuts** (Space to talk, Escape to stop) and screen reader accessibility
- **PWA manifest** for installable mobile experience
- **Non-root Docker container** with health checks

## Try It

The code is open source: [github.com/mahsumaktas/jazari-agent](https://github.com/mahsumaktas/jazari-agent)

```bash
git clone https://github.com/mahsumaktas/jazari-agent.git
cd jazari-agent
pip install -r requirements.txt
cp .env.example .env  # Add your GOOGLE_API_KEY
python -m server.main

# Optional: seed demo data for impressive first conversation
python scripts/seed_demo.py demo-user
```

Built with Google ADK, Gemini 2.5 Flash, Gemini Embedding 2, LanceDB, Cloud Run, Firestore, and React.

---

*By [Mahsum Aktas](https://github.com/mahsumaktas) for the Gemini Live Agent Challenge 2026*

#GeminiLiveAgentChallenge #GoogleADK #GeminiAPI #AICoach
