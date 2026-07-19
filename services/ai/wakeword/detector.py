import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from services.ai.types.context import AIContext
from services.ai.wakeword.config import WakeWordConfiguration
from services.ai.wakeword.health import WakeWordHealth
from services.ai.wakeword.pipeline import WakeWordPipeline
from services.ai.wakeword.statistics import WakeWordStatistics
from services.ai.wakeword.types import WakeWordState
from services.voice.audio.stream import AudioStream


class WakeWordDetector:
    def __init__(
        self,
        stream: AudioStream,
        pipeline: WakeWordPipeline,
        config: WakeWordConfiguration,
        stats: WakeWordStatistics,
        health: WakeWordHealth,
    ):
        self._logger = CoreLogger.get_logger("zeus.wakeword.detector")
        self.stream = stream
        self.pipeline = pipeline
        self.config = config
        self.stats = stats
        self.health = health

        self._running = False
        self._task: Optional[asyncio.Task] = None

        self.last_activation_time = 0.0
        self._vad_speech_active = False

    async def start(self, session_id: str):
        self.session_id = session_id
        self._running = True
        self.health.current_state = WakeWordState.LISTENING
        event_bus.subscribe("VAD_SPEECH_STARTED", self._on_vad_started)
        event_bus.subscribe("VAD_SPEECH_ENDED", self._on_vad_ended)
        self._task = asyncio.create_task(self._detection_loop())
        await event_bus.publish(
            Event(type="WAKEWORD_STARTED", payload={"session_id": session_id})
        )

    async def stop(self):
        self._running = False
        event_bus.unsubscribe("VAD_SPEECH_STARTED", self._on_vad_started)
        event_bus.unsubscribe("VAD_SPEECH_ENDED", self._on_vad_ended)
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.health.current_state = WakeWordState.STOPPED
        await event_bus.publish(
            Event(type="WAKEWORD_STOPPED", payload={"session_id": self.session_id})
        )

    async def _on_vad_started(self, event: Event):
        self._vad_speech_active = True

    async def _on_vad_ended(self, event: Event):
        self._vad_speech_active = False

    async def _detection_loop(self):
        sample_rate = self.stream.buffer.sample_rate
        frames_to_read = int(sample_rate * (self.config.chunk_size_ms / 1000.0))

        while self._running:
            try:
                if not self._vad_speech_active:
                    await asyncio.sleep(0.05)
                    continue

                frames = self.stream.read_frames(frames_to_read)

                if len(frames) < frames_to_read:
                    await asyncio.sleep(0.05)
                    continue

                chunk_id = str(uuid.uuid4())
                context = AIContext(session_id=self.session_id, user_id="system")

                now = datetime.now(timezone.utc).timestamp()
                in_cooldown = (
                    now - self.last_activation_time
                ) < self.config.profile.cooldown_seconds

                if in_cooldown:
                    self.health.current_state = WakeWordState.COOLDOWN
                    await asyncio.sleep(self.config.inference_interval_ms / 1000.0)
                    continue

                self.health.current_state = WakeWordState.DETECTING

                result = await self.pipeline.process(context, frames, chunk_id)
                self.health.update_inference_time(result.inference_time_ms)

                if result.status == "DETECTED":
                    self.last_activation_time = now
                    self.stats.record_activation(
                        result.probability, result.inference_time_ms, result.timestamp
                    )

                    await event_bus.publish(
                        Event(
                            type="WAKEWORD_DETECTED",
                            payload={
                                "timestamp": result.timestamp.isoformat(),
                                "probability": result.probability,
                                "threshold": result.threshold,
                                "inference_time_ms": result.inference_time_ms,
                                "wake_word": result.wake_word,
                                "provider": result.provider,
                                "session_id": result.session_id,
                            },
                        )
                    )
                else:
                    if result.probability > 0.0:
                        self.stats.record_rejection(
                            result.probability, result.timestamp
                        )
                        await event_bus.publish(
                            Event(
                                type="WAKEWORD_REJECTED",
                                payload={
                                    "timestamp": result.timestamp.isoformat(),
                                    "probability": result.probability,
                                },
                            )
                        )

                self.health.current_state = WakeWordState.LISTENING
                await asyncio.sleep(self.config.inference_interval_ms / 1000.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Detector loop error: {e}")
                await asyncio.sleep(1)
