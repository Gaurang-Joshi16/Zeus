import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from services.ai.types.context import AIContext
from services.ai.vad.config import VADConfiguration
from services.ai.vad.health import VADHealth
from services.ai.vad.pipeline import VADPipeline
from services.ai.vad.statistics import VADStatistics
from services.ai.vad.types import VADState, VoiceSegment
from services.voice.audio.stream import AudioStream


class VADDetector:
    def __init__(
        self,
        stream: AudioStream,
        pipeline: VADPipeline,
        config: VADConfiguration,
        stats: VADStatistics,
        health: VADHealth,
    ):
        self._logger = CoreLogger.get_logger("zeus.vad.detector")
        self.stream = stream
        self.pipeline = pipeline
        self.config = config
        self.stats = stats
        self.health = health

        self._running = False
        self._task: Optional[asyncio.Task] = None

        self._speech_active = False
        self._current_segment: Optional[VoiceSegment] = None
        self._silence_start: Optional[datetime] = None

    async def start(self, session_id: str):
        self.session_id = session_id
        self._running = True
        self.health.current_state = VADState.MONITORING
        self._task = asyncio.create_task(self._detection_loop())
        await event_bus.publish(
            Event(type="VAD_STARTED", payload={"session_id": session_id})
        )

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.health.current_state = VADState.STOPPED
        await event_bus.publish(
            Event(type="VAD_STOPPED", payload={"session_id": self.session_id})
        )

    async def _detection_loop(self):
        sample_rate = self.stream.buffer.sample_rate
        frames_to_read = int(sample_rate * (self.config.chunk_size_ms / 1000.0))

        while self._running:
            try:
                frames = self.stream.read_frames(frames_to_read)

                if len(frames) < frames_to_read:
                    await asyncio.sleep(0.05)
                    continue

                chunk_id = str(uuid.uuid4())
                context = AIContext(session_id=self.session_id, user_id="system")

                result = await self.pipeline.process(
                    context, frames, sample_rate, chunk_id
                )
                self.stats.record_inference(result.confidence, result.inference_time_ms)

                now = datetime.now(timezone.utc)

                if result.speech_detected:
                    self._silence_start = None
                    if not self._speech_active:
                        self._speech_active = True
                        self.health.current_state = VADState.SPEECH_DETECTED
                        self._current_segment = VoiceSegment(
                            segment_id=str(uuid.uuid4()),
                            start_time=now,
                            end_time=now,
                            duration_ms=0,
                            average_energy=result.energy,
                            peak_energy=result.energy,
                            sample_count=frames_to_read,
                            speech_ratio=1.0,
                        )
                        await event_bus.publish(
                            Event(
                                type="VAD_SPEECH_STARTED",
                                payload={
                                    "timestamp": result.timestamp.isoformat(),
                                    "session_id": self.session_id,
                                },
                            )
                        )
                    else:
                        if self._current_segment:
                            self._current_segment.end_time = now
                            self._current_segment.duration_ms = (
                                now - self._current_segment.start_time
                            ).total_seconds() * 1000
                            self._current_segment.sample_count += frames_to_read
                            self._current_segment.average_energy = (
                                self._current_segment.average_energy + result.energy
                            ) / 2
                            if result.energy > self._current_segment.peak_energy:
                                self._current_segment.peak_energy = result.energy
                else:
                    if self._speech_active:
                        if not self._silence_start:
                            self._silence_start = now

                        silence_duration_ms = (
                            now - self._silence_start
                        ).total_seconds() * 1000

                        if silence_duration_ms >= self.config.min_silence_duration_ms:
                            self._speech_active = False
                            self.health.current_state = VADState.SILENCE

                            if self._current_segment:
                                self.stats.record_segment(self._current_segment)
                                await event_bus.publish(
                                    Event(
                                        type="VAD_SPEECH_ENDED",
                                        payload={
                                            "timestamp": result.timestamp.isoformat(),
                                            "session_id": self.session_id,
                                            "segment_id": self._current_segment.segment_id,
                                            "duration_ms": self._current_segment.duration_ms,
                                        },
                                    )
                                )
                                self._current_segment = None
                    else:
                        self.stats.record_silence(self.config.inference_interval_ms)

                await asyncio.sleep(self.config.inference_interval_ms / 1000.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"VAD Detector loop error: {e}")
                await asyncio.sleep(1)
