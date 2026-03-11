"""Audio bridge — uses ADK's run_live() for full agent pipeline in voice mode."""

import asyncio
from google.genai import types


class AudioBridge:
    """Manages a live voice session through the ADK Runner.

    Unlike a raw Gemini Live connection, this routes through the full ADK
    agent pipeline — sub-agent routing and tool calling work in voice mode.
    """

    def __init__(self, runner, user_id: str):
        self.runner = runner
        self.user_id = user_id
        self.live_queue = None
        self._running = False

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
                        voice_name="Aoede"
                    )
                )
            ),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            input_audio_transcription=types.AudioTranscriptionConfig(),
        )

        async def consume_events():
            try:
                async for event in self.runner.run_live(
                    user_id=self.user_id,
                    live_request_queue=self.live_queue,
                    run_config=run_config,
                ):
                    if not self._running:
                        break
                    # Audio output from Jazari
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.inline_data and on_audio:
                                await on_audio(part.inline_data.data)
                            if part.text and on_transcript:
                                await on_transcript(part.text)
                    # Transcriptions
                    if event.partial and on_transcript:
                        if hasattr(event, "text") and event.text:
                            await on_transcript(event.text)
            except Exception as e:
                if self._running:
                    raise

        return asyncio.create_task(consume_events())

    async def send_audio(self, audio_data: bytes):
        """Send audio chunk from browser to ADK live session."""
        if self.live_queue and self._running:
            self.live_queue.send_realtime(
                types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
            )

    async def close(self):
        """Clean up session."""
        self._running = False
        if self.live_queue:
            self.live_queue.close()
            self.live_queue = None
