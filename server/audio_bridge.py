"""Audio bridge — uses ADK's run_live() for full agent pipeline in voice mode."""

import asyncio
import wave
from google.genai import types


class AudioBridge:
    """Manages a live voice session through the ADK Runner."""

    def __init__(self, runner, user_id: str, session_id: str):
        self.runner = runner
        self.user_id = user_id
        self.session_id = session_id
        self.live_queue = None
        self._running = False
        self._debug_chunks = []

    async def start(self, on_audio=None, on_transcript=None):
        """Start the live session and return the event stream task."""
        from google.adk.agents.live_request_queue import LiveRequestQueue
        from google.adk.agents.run_config import RunConfig

        self.live_queue = LiveRequestQueue()
        self._running = True

        run_config = RunConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Kore"
                    )
                )
            ),
            output_audio_transcription=True,
            input_audio_transcription=True,
        )

        async def consume_events():
            try:
                print("[bridge] Starting run_live...")
                async for event in self.runner.run_live(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    live_request_queue=self.live_queue,
                    run_config=run_config,
                ):
                    if not self._running:
                        break
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if getattr(part, 'thought', False):
                                continue
                            if part.inline_data and on_audio:
                                data = part.inline_data.data
                                self._debug_chunks.append(data if isinstance(data, bytes) else bytes(data))
                                await on_audio(data)
                    if on_transcript and hasattr(event, 'partial') and event.partial:
                        if hasattr(event, 'text') and event.text:
                            await on_transcript(event.text)
                print("[bridge] run_live ended normally")
            except Exception as e:
                print(f"[bridge] run_live error: {type(e).__name__}: {e}")
                if self._running:
                    raise

        return asyncio.create_task(consume_events())

    async def send_audio(self, audio_data: bytes):
        """Send audio chunk from browser to ADK live session."""
        if self.live_queue and self._running:
            self.live_queue.send_realtime(
                types.Blob(data=audio_data, mime_type="audio/pcm;rate=24000")
            )

    async def close(self):
        """Clean up session."""
        self._running = False
        if self.live_queue:
            self.live_queue.close()
            self.live_queue = None
        # Debug: save captured audio to compare with direct API output
        if self._debug_chunks:
            all_audio = b''.join(self._debug_chunks)
            with wave.open("/tmp/pipeline_debug.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(all_audio)
            print(f"[bridge] Debug saved: /tmp/pipeline_debug.wav ({len(all_audio)} bytes, {len(self._debug_chunks)} chunks)")
