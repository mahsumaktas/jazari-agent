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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from google import genai
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService

from agents.root_agent import root_agent, root_agent_with_subs

import base64
from contextlib import asynccontextmanager
from google.cloud import storage as gcs

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50MB

GCS_BUCKET = "jazari-media"
_gcs_client = None

def get_gcs_client():
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = gcs.Client()
    return _gcs_client

def upload_to_gcs(user_id: str, data: bytes, ext: str) -> str:
    import uuid as _uuid
    blob_name = f"{user_id}/{_uuid.uuid4()}.{ext}"
    bucket = get_gcs_client().bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    content_type = "image/jpeg" if ext in ("jpg", "jpeg") else "audio/wav"
    blob.upload_from_string(data, content_type=content_type)
    return f"gs://{GCS_BUCKET}/{blob_name}"

@asynccontextmanager
async def lifespan(app):
    try:
        from memory.backup import restore_from_firestore
        result = restore_from_firestore()
        print(f"[startup] LanceDB restore: {result}")
    except Exception as e:
        print(f"[startup] LanceDB restore skipped: {e}")
    yield

app = FastAPI(title="Jazari Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/api/habits/{user_id}")
async def get_habits(user_id: str):
    """Get today's habits for the dashboard."""
    from tools.habit_tools import accountability_check, habit_streak
    try:
        check = await asyncio.to_thread(accountability_check, user_id=user_id)
        streaks = await asyncio.to_thread(habit_streak, user_id=user_id)
        return {
            "done": check.get("done_today", []),
            "missed": check.get("missed_today", []),
            "streaks": streaks.get("habits", []),
        }
    except Exception:
        return {"done": [], "missed": [], "streaks": []}


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile for the side panel."""
    from tools.memory_tools import get_user_profile
    try:
        profile = await asyncio.to_thread(get_user_profile, user_id=user_id)
        return profile
    except Exception:
        return None


@app.get("/api/memories/{user_id}")
async def get_recent_memories(user_id: str, limit: int = 10):
    """Get recent memories for the memory timeline."""
    from memory.store import MemoryStore
    try:
        store = MemoryStore()
        # Get recent memories by searching with a broad query
        results = await store.search(
            query="recent activities and goals",
            user_id=user_id,
            limit=limit,
        )
        return {"memories": results}
    except Exception:
        return {"memories": []}


@app.websocket("/ws")
async def websocket_text(websocket: WebSocket, userId: str = "anonymous"):
    """Text WebSocket — for testing without voice."""
    await websocket.accept()

    session = await session_service.create_session(
        app_name="jazari",
        user_id=userId,
    )

    # Send initial greeting
    try:
        greeting_content = types.Content(
            role="user",
            parts=[types.Part.from_text("I just connected. Greet me briefly and check if you remember anything about me using search_memory.")],
        )
        greeting_response = ""
        async for event in text_runner.run_async(
            user_id=userId,
            session_id=session.id,
            new_message=greeting_content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                greeting_response = event.content.parts[0].text or ""

        if greeting_response:
            await websocket.send_json({
                "type": "text",
                "content": greeting_response,
                "agent": "jazari",
            })
    except Exception:
        pass  # Don't block on greeting failure

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid message format.",
                })
                continue

            if msg.get("type") == "text":
                user_text = msg.get("content", "")

                if not user_text.strip():
                    await websocket.send_json({
                        "type": "error",
                        "content": "Empty message.",
                    })
                    continue

                if len(user_text) > 10000:
                    await websocket.send_json({
                        "type": "error",
                        "content": "Message too long. Please keep it under 10,000 characters.",
                    })
                    continue

                content = types.Content(
                    role="user",
                    parts=[types.Part.from_text(user_text)],
                )

                response_text = ""
                agent_name = "jazari"
                try:
                    async for event in text_runner.run_async(
                        user_id=userId,
                        session_id=session.id,
                        new_message=content,
                    ):
                        if event.is_final_response() and event.content and event.content.parts:
                            response_text = event.content.parts[0].text or ""
                            agent_name = event.author
                except Exception as e:
                    response_text = "Sorry, I encountered an issue. Please try again."
                    agent_name = "jazari"

                await websocket.send_json({
                    "type": "text",
                    "content": response_text,
                    "agent": agent_name,
                })

            elif msg.get("type") == "media":
                from tools.memory_tools import store_media_memory

                modality = msg.get("modality", "image")
                data_b64_ws = msg.get("data", "")

                # Size check before decoding
                estimated_bytes = len(data_b64_ws) * 3 // 4
                if estimated_bytes > MAX_UPLOAD_BYTES:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Upload too large ({estimated_bytes // (1024*1024)}MB). Max is {MAX_UPLOAD_BYTES // (1024*1024)}MB.",
                    })
                    continue

                media_bytes = base64.b64decode(data_b64_ws)
                description = msg.get("description", "")
                ext = "jpg" if modality == "image" else "wav"

                try:
                    media_uri = upload_to_gcs(userId, media_bytes, ext)
                except Exception:
                    media_uri = ""

                memory_type = "visual" if modality == "image" else "audio"
                result = await store_media_memory(
                    user_id=userId,
                    memory_type=memory_type,
                    content=description,
                    media_bytes=media_bytes,
                    modality=modality,
                    media_uri=media_uri,
                )

                await websocket.send_json({
                    "type": "media_stored",
                    "content": result.get("message", "Memory stored"),
                    "memory_id": result.get("memory_id"),
                    "description": result.get("content", ""),
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


@app.post("/api/media-memory")
async def upload_media_memory(request: Request):
    """Upload photo or audio and store as memory."""
    from tools.memory_tools import store_media_memory

    body = await request.json()
    user_id = body.get("user_id", "").strip()
    modality = body.get("modality", "").strip()
    data_b64 = body.get("data", "")

    if not user_id or not modality or not data_b64:
        return {"error": "Missing required fields: user_id, modality, data"}

    # base64 is ~1.33x original size; check before decoding
    estimated_bytes = len(data_b64) * 3 // 4
    if estimated_bytes > MAX_UPLOAD_BYTES:
        return {"error": f"Upload too large ({estimated_bytes // (1024*1024)}MB). Max is {MAX_UPLOAD_BYTES // (1024*1024)}MB."}

    if modality not in ("image", "audio"):
        return {"error": f"Invalid modality: {modality}. Must be 'image' or 'audio'."}

    try:
        media_bytes = base64.b64decode(data_b64)
    except Exception:
        return {"error": "Invalid base64 data"}

    description = body.get("description", "")
    ext = "jpg" if modality == "image" else "wav"

    try:
        media_uri = upload_to_gcs(user_id, media_bytes, ext)
    except Exception:
        media_uri = ""

    memory_type = "visual" if modality == "image" else "audio"
    result = await store_media_memory(
        user_id=user_id,
        memory_type=memory_type,
        content=description,
        media_bytes=media_bytes,
        modality=modality,
        media_uri=media_uri,
    )
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
