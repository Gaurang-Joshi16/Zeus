import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from services.ai.speaker.config import SpeakerConfiguration
from services.ai.speaker.health import SpeakerHealth
from services.ai.speaker.pipeline import SpeakerPipeline
from services.ai.speaker.statistics import SpeakerStatistics
from services.ai.speaker.types import (
    SessionState,
    SpeakerAuthenticationSession,
    SpeakerState,
)


class SpeakerDetector:
    def __init__(
        self,
        pipeline: SpeakerPipeline,
        config: SpeakerConfiguration,
        stats: SpeakerStatistics,
        health: SpeakerHealth,
    ):
        self._logger = CoreLogger.get_logger("zeus.speaker.detector")
        self.pipeline = pipeline
        self.config = config
        self.stats = stats
        self.health = health
        self._active_auth_session: Optional[SpeakerAuthenticationSession] = None

    async def start(self):
        self.health.current_state = SpeakerState.READY
        event_bus.subscribe("SPEAKER_VERIFICATION_STARTED", self._on_verification_started)

    async def stop(self):
        event_bus.unsubscribe("SPEAKER_VERIFICATION_STARTED", self._on_verification_started)
        self.health.current_state = SpeakerState.STOPPED

    async def _on_verification_started(self, event: Event):
        self._logger.info("Speaker verification started, running verification window.")
        self.health.current_state = SpeakerState.VERIFYING

        window_ms = self.config.verification_window_ms
        await asyncio.sleep(window_ms / 1000.0)

        try:
            result = await self.pipeline.run_verification()

            self.stats.record_verification(
                verified=result.verified,
                confidence=result.confidence_score,
                time_ms=result.inference_time_ms,
                timestamp=result.timestamp.isoformat(),
            )

            if result.verified:
                self._active_auth_session = SpeakerAuthenticationSession(
                    session_id=result.session_id,
                    status=SessionState.AUTHENTICATED,
                    verification_attempts=1,
                    confidence_history=[result.confidence_score],
                    provider_used=result.provider,
                    model_used=result.model_version,
                    expiration_time=datetime.now(timezone.utc) + timedelta(hours=1),
                )
                self.stats.session_history.append(self._active_auth_session)

                await event_bus.publish(
                    Event(
                        type="SPEAKER_VERIFIED",
                        payload={
                            "speaker_id": result.speaker_id,
                            "confidence_band": result.confidence_band.value,
                            "confidence_score": result.confidence_score,
                            "session_id": result.session_id,
                        },
                    )
                )
            else:
                await event_bus.publish(
                    Event(
                        type="SPEAKER_REJECTED",
                        payload={
                            "confidence_band": result.confidence_band.value,
                            "confidence_score": result.confidence_score,
                        },
                    )
                )

        except Exception as e:
            self._logger.error(f"Error during speaker verification: {e}")

        finally:
            self.health.current_state = SpeakerState.READY
