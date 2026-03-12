"""FastAPI server — WebSocket endpoint for Jazari agent."""

import sys
from pathlib import Path

# Ensure project root is in Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
import asyncio

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from google import genai
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService

from agents.root_agent import root_agent, root_agent_with_subs

app = FastAPI(title="Jazari Agent")

# Shared services — memory service enables cross-session recall
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# ADK Runners — separate for text (with sub-agents) and audio (simple)
runner = Runner(
    agent=root_agent,
    app_name="jazari",
    session_service=session_service,
    memory_service=memory_service,
)
text_runner = Runner(
    agent=root_agent_with_subs,
    app_name="jazari",
    session_service=session_service,
    memory_service=memory_service,
)

# Serve frontend static files if built
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


@app.get("/audio-processor.js")
async def audio_processor():
    """Serve AudioWorklet processor script."""
    return FileResponse(FRONTEND_DIR / "audio-processor.js", media_type="application/javascript")


@app.get("/")
async def index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "Jazari is running", "mode": "API only (no frontend build)"}


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "jazari"}


@app.websocket("/ws")
async def websocket_text(websocket: WebSocket, userId: str = "anonymous"):
    """Text WebSocket — for testing without voice."""
    await websocket.accept()

    session = await session_service.create_session(
        app_name="jazari",
        user_id=userId,
    )

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "text":
                user_text = msg.get("content", "")
                content = types.Content(
                    role="user",
                    parts=[types.Part.from_text(user_text)],
                )

                response_text = ""
                async for event in text_runner.run_async(
                    user_id=userId,
                    session_id=session.id,
                    new_message=content,
                ):
                    if event.is_final_response() and event.content and event.content.parts:
                        response_text = event.content.parts[0].text or ""

                await websocket.send_json({
                    "type": "text",
                    "content": response_text,
                    "agent": "jazari",
                })

    except WebSocketDisconnect:
        pass


@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket, userId: str = "anonymous"):
    """Voice WebSocket — bidirectional audio via ADK run_live()."""
    await websocket.accept()
    print(f"[audio] WebSocket connected: userId={userId}")

    from server.audio_bridge import AudioBridge

    session = await session_service.create_session(app_name="jazari", user_id=userId)
    bridge = AudioBridge(runner=runner, user_id=userId, session_id=session.id)
    event_task = None

    try:
        async def on_audio(data: bytes):
            try:
                await websocket.send_bytes(data)
            except Exception:
                pass  # WebSocket may have closed

        async def on_transcript(text: str):
            try:
                await websocket.send_json({"type": "transcript", "content": text})
            except Exception:
                pass

        # Start ADK live session
        print(f"[audio] Starting ADK live session...")
        event_task = await bridge.start(on_audio=on_audio, on_transcript=on_transcript)
        print(f"[audio] ADK live session started")

        # Forward browser audio to ADK
        while True:
            try:
                data = await websocket.receive()
            except (WebSocketDisconnect, RuntimeError):
                print(f"[audio] WebSocket disconnected")
                break
            if "bytes" in data:
                await bridge.send_audio(data["bytes"])

    except Exception as e:
        print(f"[audio] Error: {type(e).__name__}: {e}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass

    finally:
        if event_task:
            event_task.cancel()
        await bridge.close()
        print(f"[audio] Session cleaned up")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
