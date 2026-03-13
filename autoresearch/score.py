#!/usr/bin/env python3
"""AutoResearch Scoring — frozen hackathon evaluation metric.

Based on Gemini Live Agent Challenge judging criteria:
- Innovation & Multimodal UX (40%)
- Technical Implementation & Agent Architecture (30%)
- Demo & Presentation (30%)

DO NOT MODIFY THIS FILE. This is the frozen metric.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def check_file_exists(path: str) -> bool:
    return (PROJECT_ROOT / path).exists()


def check_file_contains(path: str, text: str) -> bool:
    try:
        return text in (PROJECT_ROOT / path).read_text()
    except Exception:
        return False


def count_tools_in_agent(path: str) -> int:
    try:
        content = (PROJECT_ROOT / path).read_text()
        return content.count("tools=[") + content.count("tools=\n")
    except Exception:
        return 0


def run_tests() -> tuple[int, int]:
    """Run pytest and return (passed, total)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
            capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=60
        )
        output = result.stdout
        # Parse "X passed" from output
        for line in output.split("\n"):
            if "passed" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "passed":
                        return int(parts[i-1]), int(parts[i-1])
                    if p == "passed,":
                        total = int(parts[i-1]) + int(parts[i+1]) if i+1 < len(parts) else int(parts[i-1])
                        return int(parts[i-1]), total
        return 0, 0
    except Exception:
        return 0, 0


def score() -> dict:
    """Score the project. Returns dict with category scores and total."""

    scores = {
        "innovation_multimodal_ux": {},
        "technical_implementation": {},
        "demo_presentation": {},
    }

    # ============================================================
    # INNOVATION & MULTIMODAL UX (40%) — max 40 points
    # ============================================================
    ux = scores["innovation_multimodal_ux"]

    # 1. Voice-first interaction (not text box) — 6 pts
    ux["voice_first"] = 6 if (
        check_file_contains("agents/root_agent.py", "native-audio") and
        check_file_contains("server/main.py", "/ws/audio")
    ) else 0

    # 2. Distinct persona/voice — 5 pts
    ux["distinct_persona"] = 0
    if check_file_contains("agents/root_agent.py", "Al-Jazari"):
        ux["distinct_persona"] += 2
    if check_file_contains("agents/root_agent.py", "COACH"):
        ux["distinct_persona"] += 2
    if check_file_contains("agents/root_agent.py", "Turkish"):
        ux["distinct_persona"] += 1

    # 3. Context-aware (memory across sessions) — 6 pts
    ux["context_aware"] = 0
    if check_file_exists("memory/store.py"):
        ux["context_aware"] += 3
    if check_file_contains("memory/store.py", "LanceDB") or check_file_contains("memory/store.py", "lancedb"):
        ux["context_aware"] += 2
    if check_file_contains("memory/forgetting.py", "Ebbinghaus") or check_file_contains("memory/forgetting.py", "decay"):
        ux["context_aware"] += 1

    # 4. Multimodal input (photo + audio + text) — 6 pts
    ux["multimodal_input"] = 0
    if check_file_exists("frontend/src/components/CameraButton.tsx"):
        ux["multimodal_input"] += 2
    if check_file_contains("frontend/src/components/MicButton.tsx", "onVoiceNote"):
        ux["multimodal_input"] += 2
    if check_file_contains("server/main.py", "/api/media-memory"):
        ux["multimodal_input"] += 2

    # 5. Cross-modal search — 4 pts
    ux["cross_modal_search"] = 0
    if check_file_contains("memory/store.py", "_embed_image"):
        ux["cross_modal_search"] += 2
    if check_file_contains("memory/store.py", "_embed_audio"):
        ux["cross_modal_search"] += 2

    # 6. Proactive behavior (agent initiates) — 5 pts
    ux["proactive"] = 0
    if check_file_contains("agents/root_agent.py", "decaying_goals") or check_file_contains("agents/root_agent.py", "get_decaying_goals"):
        ux["proactive"] += 3
    if check_file_contains("agents/root_agent.py", "follow up"):
        ux["proactive"] += 2

    # 7. Live/seamless (not turn-based) — 4 pts
    ux["live_seamless"] = 0
    if check_file_contains("server/main.py", "run_live") or check_file_exists("server/audio_bridge.py"):
        ux["live_seamless"] += 2
    if check_file_contains("frontend/src/hooks/useWebSocket.ts", "AudioWorklet"):
        ux["live_seamless"] += 2

    # 8. Innovative features (unique differentiators) — 4 pts
    ux["innovative"] = 0
    if check_file_contains("memory/forgetting.py", "exp"):  # Ebbinghaus formula
        ux["innovative"] += 2
    if check_file_contains("memory/scoring.py", "score_importance"):
        ux["innovative"] += 2

    # ============================================================
    # TECHNICAL IMPLEMENTATION (30%) — max 30 points
    # ============================================================
    tech = scores["technical_implementation"]

    # 1. Uses Google GenAI SDK or ADK — 5 pts
    tech["sdk_usage"] = 0
    if check_file_contains("requirements.txt", "google-adk"):
        tech["sdk_usage"] += 3
    if check_file_contains("requirements.txt", "google-genai"):
        tech["sdk_usage"] += 2

    # 2. Google Cloud hosting — 4 pts
    tech["cloud_hosting"] = 0
    if check_file_exists("Dockerfile"):
        tech["cloud_hosting"] += 2
    if check_file_exists("cloudbuild.yaml"):
        tech["cloud_hosting"] += 2

    # 3. Agent architecture (multi-agent, sub-agents) — 4 pts
    tech["agent_arch"] = 0
    if check_file_contains("agents/root_agent.py", "sub_agents"):
        tech["agent_arch"] += 2
    agent_files = list((PROJECT_ROOT / "agents").glob("*_agent.py"))
    tech["agent_arch"] += min(2, len(agent_files) - 1)  # bonus for multiple agents

    # 4. Error handling / graceful degradation — 3 pts
    tech["error_handling"] = 0
    if check_file_contains("memory/scoring.py", "except"):
        tech["error_handling"] += 1
    if check_file_contains("memory/store.py", "except"):
        tech["error_handling"] += 1
    if check_file_contains("agents/root_agent.py", "hallucin") or check_file_contains("agents/root_agent.py", "not sure"):
        tech["error_handling"] += 1

    # 5. Grounding (avoids hallucinations) — 4 pts
    tech["grounding"] = 0
    if check_file_contains("agents/root_agent.py", "grounding") or check_file_contains("agents/root_agent.py", "Google Search"):
        tech["grounding"] += 2
    if check_file_contains("tools/memory_tools.py", "search_memory"):
        tech["grounding"] += 1  # memory-based grounding
    if any(check_file_contains(f"agents/{f.name}", "google_search") for f in agent_files):
        tech["grounding"] += 1

    # 6. Test coverage — 4 pts
    passed, total = run_tests()
    tech["tests"] = min(4, passed)  # 1 pt per passing test, max 4

    # 7. Code quality (no hardcoded secrets, proper structure) — 3 pts
    tech["code_quality"] = 0
    if check_file_exists(".env.example"):
        tech["code_quality"] += 1
    if check_file_exists(".gitignore"):
        tech["code_quality"] += 1
    if check_file_exists("memory/__init__.py"):
        tech["code_quality"] += 1

    # 8. Multiple Google Cloud services — 3 pts
    tech["multi_gcp"] = 0
    if check_file_contains("requirements.txt", "google-cloud-firestore"):
        tech["multi_gcp"] += 1
    if check_file_contains("requirements.txt", "google-cloud-storage"):
        tech["multi_gcp"] += 1
    if check_file_exists("cloudbuild.yaml"):
        tech["multi_gcp"] += 1

    # ============================================================
    # DEMO & PRESENTATION (30%) — max 30 points
    # ============================================================
    demo = scores["demo_presentation"]

    # 1. Architecture diagram — 5 pts
    demo["architecture_diagram"] = 5 if check_file_exists("docs/architecture.html") else 0

    # 2. README with clear problem/solution — 5 pts
    demo["readme"] = 0
    if check_file_exists("README.md"):
        readme = (PROJECT_ROOT / "README.md").read_text()
        if len(readme) > 500:
            demo["readme"] += 2
        if "problem" in readme.lower() or "why" in readme.lower():
            demo["readme"] += 1
        if "setup" in readme.lower() or "install" in readme.lower():
            demo["readme"] += 1
        if "architecture" in readme.lower() or "diagram" in readme.lower():
            demo["readme"] += 1

    # 3. Cloud deployment proof — 5 pts
    demo["deploy_proof"] = 0
    if check_file_exists("scripts/deploy.sh"):
        demo["deploy_proof"] += 2
    if check_file_exists("cloudbuild.yaml"):
        demo["deploy_proof"] += 2
    if check_file_contains("cloudbuild.yaml", "set-secrets") or check_file_contains("cloudbuild.yaml", "GOOGLE_API_KEY"):
        demo["deploy_proof"] += 1

    # 4. Working frontend — 4 pts
    demo["frontend"] = 0
    if check_file_exists("frontend/src/App.tsx"):
        demo["frontend"] += 2
    if check_file_exists("frontend/package.json"):
        demo["frontend"] += 1
    if check_file_exists("frontend/src/components/CameraButton.tsx"):
        demo["frontend"] += 1

    # 5. Public repo with instructions — 4 pts
    demo["repo"] = 0
    if check_file_exists(".gitignore"):
        demo["repo"] += 1
    if check_file_exists("requirements.txt"):
        demo["repo"] += 1
    if check_file_exists(".env.example"):
        demo["repo"] += 1
    if check_file_exists("Dockerfile"):
        demo["repo"] += 1

    # 6. Bonus content (blog, hashtag) — 3 pts
    demo["bonus"] = 0
    if check_file_exists("docs/SUBMISSION.md") or check_file_exists("SUBMISSION.md"):
        demo["bonus"] += 2
    if check_file_contains("README.md", "GeminiLiveAgentChallenge"):
        demo["bonus"] += 1

    # 7. Automated deployment — 4 pts
    demo["auto_deploy"] = 0
    if check_file_exists("scripts/deploy.sh"):
        demo["auto_deploy"] += 2
    if check_file_exists("cloudbuild.yaml"):
        demo["auto_deploy"] += 2

    # ============================================================
    # COMPUTE TOTALS
    # ============================================================
    innovation_total = sum(ux.values())
    technical_total = sum(tech.values())
    demo_total = sum(demo.values())

    innovation_max = 40
    technical_max = 30
    demo_max = 30

    total = innovation_total + technical_total + demo_total

    return {
        "innovation_multimodal_ux": {
            "items": ux,
            "total": innovation_total,
            "max": innovation_max,
            "pct": round(innovation_total / innovation_max * 100, 1),
        },
        "technical_implementation": {
            "items": tech,
            "total": technical_total,
            "max": technical_max,
            "pct": round(technical_total / technical_max * 100, 1),
        },
        "demo_presentation": {
            "items": demo,
            "total": demo_total,
            "max": demo_max,
            "pct": round(demo_total / demo_max * 100, 1),
        },
        "total_score": total,
        "max_score": 100,
        "pct": round(total / 100 * 100, 1),
    }


def print_scorecard(s: dict):
    """Pretty-print the scorecard."""
    print("=" * 60)
    print(f"  JAZARI AUTORESEARCH SCORECARD")
    print("=" * 60)

    for category in ["innovation_multimodal_ux", "technical_implementation", "demo_presentation"]:
        cat = s[category]
        label = category.replace("_", " ").title()
        print(f"\n  {label}: {cat['total']}/{cat['max']} ({cat['pct']}%)")
        for k, v in cat["items"].items():
            status = "OK" if v > 0 else "--"
            print(f"    [{status}] {k}: {v}")

    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {s['total_score']}/{s['max_score']} ({s['pct']}%)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    result = score()
    print_scorecard(result)

    # Save to JSON for tracking
    log_file = PROJECT_ROOT / "autoresearch" / "scores.jsonl"
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, "a") as f:
        import datetime
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "score": result["total_score"],
            "pct": result["pct"],
            "details": result,
        }
        f.write(json.dumps(entry) + "\n")
