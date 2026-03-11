"""FastAPI server — WebSocket endpoint for Jazari agent."""

import os
import json
import asyncio
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from google import genai
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from agents.root_agent import root_agent

app = FastAPI(title="Jazari Agent")

# ADK Runner
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="jazari",
    session_service=session_service,
)

# Serve frontend static files if built
FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


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
                async for event in runner.run_async(
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
    """Voice WebSocket — bidirectional audio via ADK run_live().

    Full agent pipeline works in voice mode: sub-agent routing,
    tool calling (Firestore ops), and memory — all through voice.
    """
    await websocket.accept()

    from server.audio_bridge import AudioBridge

    bridge = AudioBridge(runner=runner, user_id=userId)

    try:
        async def on_audio(data: bytes):
            await websocket.send_bytes(data)

        async def on_transcript(text: str):
            await websocket.send_json({"type": "transcript", "content": text})

        # Start ADK live session (full agent pipeline)
        event_task = await bridge.start(on_audio=on_audio, on_transcript=on_transcript)

        # Forward browser audio to ADK
        try:
            while True:
                data = await websocket.receive()
                if "bytes" in data:
                    await bridge.send_audio(data["bytes"])
        except WebSocketDisconnect:
            pass
        finally:
            event_task.cancel()

    finally:
        await bridge.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
