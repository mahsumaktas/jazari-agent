"""MemoryStore — LanceDB + Gemini Embedding 2 for semantic multimodal memory."""

import uuid
import asyncio
import lancedb
import pyarrow as pa
import numpy as np
from datetime import datetime, timezone
from google import genai

from memory.scoring import score_importance
from memory.forgetting import effective_importance, FORGET_THRESHOLD

EMBEDDING_MODEL = "gemini-embedding-exp-03-07"
EMBEDDING_DIM = 768
TABLE_NAME = "memories"

SCHEMA = pa.schema([
    pa.field("id", pa.string()),
    pa.field("content", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
    pa.field("memory_type", pa.string()),
    pa.field("importance", pa.float32()),
    pa.field("modality", pa.string()),
    pa.field("media_uri", pa.string()),
    pa.field("created_at", pa.string()),
    pa.field("last_accessed", pa.string()),
    pa.field("decay_factor", pa.float32()),
    pa.field("user_id", pa.string()),
])


class MemoryStore:

    def __init__(self, db_path: str = "/tmp/lancedb"):
        self.db_path = db_path
        self.db = lancedb.connect(db_path)
        self._client = None
        self._lock = asyncio.Lock()
        self._ensure_table()

    def _ensure_table(self):
        try:
            self.db.open_table(TABLE_NAME)
        except Exception:
            self.db.create_table(TABLE_NAME, schema=SCHEMA)

    @property
    def client(self):
        if self._client is None:
            self._client = genai.Client()
        return self._client

    async def _embed_text(self, text: str) -> list[float]:
        from google.genai import types
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=text,
                    config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
                ),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            raise TimeoutError("Gemini embed_content (text) timed out after 15s")
        return response.embeddings[0].values

    async def _embed_image(self, image_bytes: bytes) -> list[float]:
        from google.genai import types
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=image_part,
                    config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
                ),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            raise TimeoutError("Gemini embed_content (image) timed out after 15s")
        return response.embeddings[0].values

    async def _embed_audio(self, audio_bytes: bytes) -> list[float]:
        from google.genai import types
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=audio_part,
                    config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
                ),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            raise TimeoutError("Gemini embed_content (audio) timed out after 15s")
        return response.embeddings[0].values

    async def _describe_image(self, image_bytes: bytes) -> str:
        from google.genai import types
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        "Describe this image in 1-2 sentences. Focus on what's visible: food, objects, people, activities.",
                        image_part,
                    ],
                ),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            raise TimeoutError("Gemini generate_content (describe image) timed out after 15s")
        return response.text.strip()

    async def _transcribe_audio(self, audio_bytes: bytes) -> str:
        from google.genai import types
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        "Transcribe this audio exactly. Return only the transcript text.",
                        audio_part,
                    ],
                ),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            raise TimeoutError("Gemini generate_content (transcribe audio) timed out after 15s")
        return response.text.strip()

    async def store(
        self,
        user_id: str,
        content: str,
        memory_type: str,
        modality: str = "text",
        media_bytes: bytes | None = None,
        media_uri: str = "",
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        memory_id = str(uuid.uuid4())

        if modality == "image" and media_bytes:
            description = await self._describe_image(media_bytes)
            content = f"{content}. {description}" if content else description
            vector = await self._embed_image(media_bytes)
        elif modality == "audio" and media_bytes:
            transcript = await self._transcribe_audio(media_bytes)
            content = f"{content}. {transcript}" if content else transcript
            vector = await self._embed_audio(media_bytes)
        else:
            vector = await self._embed_text(content)

        importance = await score_importance(content, memory_type)

        async with self._lock:
            table = self.db.open_table(TABLE_NAME)
            table.add([{
                "id": memory_id,
                "content": content,
                "vector": vector,
                "memory_type": memory_type,
                "importance": float(importance),
                "modality": modality,
                "media_uri": media_uri,
                "created_at": now,
                "last_accessed": now,
                "decay_factor": float(importance * 30),
                "user_id": user_id,
            }])

        # Backup single record to Firestore (fire-and-forget)
        try:
            from memory.backup import backup_single_record
            record_data = {
                "id": memory_id, "content": content,
                "vector": vector, "memory_type": memory_type,
                "importance": float(importance), "modality": modality,
                "media_uri": media_uri, "created_at": now,
                "last_accessed": now, "decay_factor": float(importance * 30),
                "user_id": user_id,
            }
            asyncio.create_task(backup_single_record(memory_id, record_data))
        except Exception:
            pass

        return {
            "memory_id": memory_id,
            "content": content[:100],
            "memory_type": memory_type,
            "importance": importance,
            "modality": modality,
            "message": f"Remembered: {content[:50]}...",
        }

    async def search(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        modality_filter: str | None = None,
    ) -> list[dict]:
        query_vector = await self._embed_text(query)
        table = self.db.open_table(TABLE_NAME)

        safe_user_id = user_id.replace("'", "")
        where_clause = f"user_id = '{safe_user_id}'"
        if modality_filter:
            safe_modality = modality_filter.replace("'", "")
            where_clause += f" AND modality = '{safe_modality}'"

        try:
            results = (
                table.search(query_vector)
                .where(where_clause)
                .limit(limit * 3)
                .to_pandas()
            )
        except Exception:
            return []

        if results.empty:
            return []

        now = datetime.now(timezone.utc)
        filtered = []
        for _, row in results.iterrows():
            try:
                last_accessed = datetime.fromisoformat(row["last_accessed"])
            except (ValueError, TypeError):
                last_accessed = now

            eff_imp = effective_importance(
                importance=float(row["importance"]),
                last_accessed=last_accessed,
                now=now,
            )
            if eff_imp >= FORGET_THRESHOLD:
                filtered.append({
                    "memory_id": row["id"],
                    "content": row["content"],
                    "memory_type": row["memory_type"],
                    "importance": float(row["importance"]),
                    "effective_importance": round(eff_imp, 3),
                    "modality": row["modality"],
                    "media_uri": row["media_uri"],
                    "created_at": row["created_at"],
                })

        # Update last_accessed
        now_iso = now.isoformat()
        async with self._lock:
            for mem in filtered[:limit]:
                try:
                    table.update(
                        where=f"id = '{mem['memory_id']}'",
                        values={"last_accessed": now_iso},
                    )
                except Exception:
                    pass

        filtered.sort(key=lambda m: m["effective_importance"], reverse=True)
        return filtered[:limit]

    async def get_decaying_goals(self, user_id: str, threshold: float = 0.3) -> list[dict]:
        table = self.db.open_table(TABLE_NAME)
        try:
            df = table.to_pandas()
            safe_uid = user_id.replace("'", "")
            goals = df[
                (df["user_id"] == safe_uid) &
                (df["memory_type"].isin(["goal", "habit"]))
            ]
        except Exception:
            return []

        now = datetime.now(timezone.utc)
        decaying = []
        for _, row in goals.iterrows():
            try:
                last_accessed = datetime.fromisoformat(row["last_accessed"])
            except (ValueError, TypeError):
                continue

            eff_imp = effective_importance(float(row["importance"]), last_accessed, now)
            if eff_imp < threshold and float(row["importance"]) >= 0.5:
                days_since = (now - last_accessed).days
                decaying.append({
                    "content": row["content"],
                    "original_importance": float(row["importance"]),
                    "effective_importance": round(eff_imp, 3),
                    "days_since_accessed": days_since,
                })

        return decaying
