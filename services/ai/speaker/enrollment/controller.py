import asyncio
import uuid
from typing import Any, Dict, Optional

import numpy as np

from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from core.logging.logger import CoreLogger
from core.setup.state_machine import SetupState, setup_state_machine
from services.ai.speaker.config import SpeakerConfiguration
from services.ai.speaker.enrollment.phrases import PhraseManager
from services.ai.speaker.enrollment.quality import (
    EnrollmentQualityAnalyzer,
    QualityResult,
)
from services.ai.speaker.enrollment.session import EnrollmentSession
from services.ai.speaker.pipeline import SpeakerPipeline
from services.ai.speaker.store import SpeakerStore
from services.ai.speaker.types import SpeakerEmbedding, SpeakerProfile, SpeakerRole
from services.voice.audio.manager import AudioManager


class EnrollmentController:
    def __init__(
        self,
        store: SpeakerStore,
        config: SpeakerConfiguration,
        pipeline: SpeakerPipeline,
        audio_manager: AudioManager,
    ):
        self._logger = CoreLogger.get_logger("zeus.speaker.enrollment.controller")
        self.store = store
        self.config = config
        self.pipeline = pipeline
        self.audio_manager = audio_manager

        self.phrases = PhraseManager()
        self.analyzer = EnrollmentQualityAnalyzer(
            min_quality=config.min_quality,
            min_duration_ms=config.min_audio_length_ms,
            max_duration_ms=config.max_audio_length_ms,
        )

        self._active_session: Optional[EnrollmentSession] = None
        self._speech_detected = False
        self._is_analyzing = False
        self._silence_frames = 0
        self._is_verifying = False

    async def start_enrollment(self, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        self._logger.info("[Backend] EnrollmentController.start_enrollment() executed")
        await setup_state_machine.transition_to(SetupState.ENROLLMENT)
        self._active_session = EnrollmentSession(
            required_samples=self.config.enrollment_samples
        )
        self._active_session.current_phrase = self.phrases.get_next_phrase()
        self._is_verifying = False

        self._logger.info(
            f"Start Enrollment requested. Session ID: {self._active_session.session_id}"
        )
        try:
            self._logger.info("[Backend] EventBus.publish(ENROLLMENT_STARTED) publishing")
            await event_bus.publish(
                Event(
                    type="ENROLLMENT_STARTED",
                    payload={
                        "session_id": self._active_session.session_id,
                        "phrase": self._active_session.current_phrase,
                        "required_samples": self._active_session.progress.required_samples,
                        "current_sample": self._active_session.progress.accepted_samples,
                    },
                )
            )
        except Exception as e:
            self._logger.error("[Backend] Enrollment controller failure")
            self._logger.error(f"Failed to publish ENROLLMENT_STARTED: {e}")
            raise

        return {
            "session_id": self._active_session.session_id,
            "phrase": self._active_session.current_phrase,
            "progress": self._active_session.progress.to_dict(),
        }

    async def cancel_enrollment(self, payload: Dict[str, Any] = None) -> None:
        self._active_session = None
        self._is_verifying = False
        await setup_state_machine.transition_to(SetupState.OWNER_NOT_FOUND)

    def _on_level_changed(self, event: Event) -> None:
        if not self._active_session:
            return

        payload = event.payload
        is_silent = payload.get("is_silent", True)

        if not self._speech_detected:
            if not is_silent:
                self._speech_detected = True
                self._silence_frames = 0
                asyncio.create_task(
                    event_bus.publish(
                        Event(type=EventTypes.ENROLLMENT_SPEECH_DETECTED, payload={})
                    )
                )
        else:
            if is_silent:
                self._silence_frames += 1
                # Auto-stop after ~1.5s of silence (assuming 10hz updates, so 15 frames)
                if self._silence_frames > 15 and not self._is_analyzing:
                    self._is_analyzing = True
                    asyncio.create_task(self.stop_recording())
            else:
                self._silence_frames = 0

    async def begin_recording(self, payload: Dict[str, Any] = None) -> None:
        if not self._active_session:
            return

        self._logger.info("Recording Started.")
        self._speech_detected = False
        self._silence_frames = 0
        self._is_analyzing = False
        event_bus.subscribe("LEVEL_CHANGED", self._on_level_changed)

        await self.audio_manager.start_recording_session()
        await event_bus.publish(
            Event(type=EventTypes.ENROLLMENT_RECORDING_STARTED, payload={})
        )

    async def _handle_verification_sample(self, frames: np.ndarray) -> Dict[str, Any]:
        self._logger.info("Processing Verification Sample...")
        result = await self.pipeline.run_verification(frames)
        # Purge frames from memory
        frames = None

        if result.verified:
            self._logger.info(f"Owner Verified! Confidence: {result.confidence_score}")
            await event_bus.publish(
                Event(
                    type=EventTypes.OWNER_VERIFIED,
                    payload={"confidence": result.confidence_score},
                )
            )
            await event_bus.publish(Event(type=EventTypes.OWNER_READY, payload={}))
            await setup_state_machine.transition_to(SetupState.READY)
            self._active_session = None
            self._is_verifying = False
            return {"status": "completed"}
        else:
            await event_bus.publish(
                Event(
                    type=EventTypes.OWNER_VERIFICATION_FAILED,
                    payload={"reason": "CONFIDENCE_TOO_LOW"},
                )
            )
            return {"status": "rejected", "reason": "CONFIDENCE_TOO_LOW"}

    async def stop_recording(self, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self._active_session:
            return {"status": "error", "message": "No active session."}

        self._logger.info("Recording Finished. Validating...")
        event_bus.unsubscribe("LEVEL_CHANGED", self._on_level_changed)
        frames = await self.audio_manager.stop_recording_session()

        if self._is_verifying:
            return await self._handle_verification_sample(frames)

        quality, message = self.analyzer.analyze(
            frames, self.audio_manager.buffer.sample_rate
        )

        if quality == QualityResult.FAIL:
            self._active_session.progress.rejected_samples += 1
            self._active_session.progress.retries += 1
            await event_bus.publish(
                Event(
                    type=EventTypes.ENROLLMENT_SAMPLE_REJECTED,
                    payload={"reason": message},
                )
            )
            frames = None
            return {"status": "rejected", "reason": message}

        self._logger.info("Extracting Embedding...")
        embedding_vec = await self.pipeline.extract_embedding(frames)
        self._logger.info("Embedding Extracted.")
        frames = None  # Purge raw audio immediately

        # Check confidence against running average if we have existing samples
        if len(self._active_session.collected_embeddings) > 0:
            avg_vector = np.mean(self._active_session.collected_embeddings, axis=0)
            score = await self.pipeline.inference.compare_embeddings(
                embedding_vec, avg_vector
            )
            if score < self.config.verification_threshold:
                self._active_session.progress.rejected_samples += 1
                self._active_session.progress.retries += 1
                await event_bus.publish(
                    Event(
                        type=EventTypes.ENROLLMENT_SAMPLE_REJECTED,
                        payload={"reason": "CONFIDENCE_TOO_LOW"},
                    )
                )
                return {"status": "rejected", "reason": "CONFIDENCE_TOO_LOW"}

        self._active_session.collected_embeddings.append(embedding_vec)
        self._active_session.progress.accepted_samples += 1

        self._logger.info(
            f"Sample Accepted. Progress: {self._active_session.progress.accepted_samples}/{self._active_session.progress.required_samples}"
        )

        await event_bus.publish(
            Event(
                type=EventTypes.ENROLLMENT_SAMPLE_ACCEPTED,
                payload={
                    "sample_number": self._active_session.progress.accepted_samples,
                    "total_required": self._active_session.progress.required_samples,
                    "progress_percentage": self._active_session.progress.completion_percentage,
                    "phrase_completed": self._active_session.current_phrase,
                    "remaining_samples": self._active_session.progress.required_samples
                    - self._active_session.progress.accepted_samples,
                    "estimated_remaining_time": self._active_session.progress.estimated_remaining_time,
                },
            )
        )

        await event_bus.publish(
            Event(
                type=EventTypes.ENROLLMENT_PROGRESS_UPDATED,
                payload=self._active_session.progress.to_dict(),
            )
        )

        if (
            self._active_session.progress.accepted_samples
            >= self._active_session.progress.required_samples
        ):
            return await self.finish_enrollment()

        self._active_session.current_phrase = self.phrases.get_next_phrase()
        self._logger.info(f"Next Phrase: {self._active_session.current_phrase}")

        await event_bus.publish(
            Event(
                type=EventTypes.ENROLLMENT_NEXT_PHRASE,
                payload={
                    "current_phrase": self._active_session.current_phrase,
                    "current_sample": self._active_session.progress.accepted_samples,
                    "remaining_samples": self._active_session.progress.required_samples
                    - self._active_session.progress.accepted_samples,
                    "progress": self._active_session.progress.to_dict(),
                },
            )
        )

        return {"status": "accepted"}

    async def finish_enrollment(self, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        avg_vector = np.mean(self._active_session.collected_embeddings, axis=0)
        # Normalize
        norm = np.linalg.norm(avg_vector)
        if norm > 0:
            avg_vector = avg_vector / norm

        embedding_id = str(uuid.uuid4())
        profile_id = str(uuid.uuid4())

        embedding = SpeakerEmbedding(
            embedding_id=embedding_id,
            owner_id=profile_id,
            model_version=self.pipeline.inference.model_version,
            provider=self.pipeline.inference.provider_id,
            vector=avg_vector.tolist(),
            quality_score=1.0,
            language="en",
            microphone="default",
            sample_rate=16000,
        )

        display_name = "Owner"
        profile = SpeakerProfile(
            profile_id=profile_id,
            display_name=display_name,
            role=SpeakerRole.OWNER,
            embedding_references=[embedding_id],
            preferred_language="en",
            verification_threshold=self.config.verification_threshold,
            status="ACTIVE",
            verification_count=0,
            profile_version="1.0",
            embedding_version="1.0",
            provider_version="1.0",
            model_version=self.pipeline.inference.model_version,
            migration_version="1.0",
        )

        self.store.save_embedding(embedding)
        self.store.save_profile(profile)

        # Clear raw embeddings from memory
        self._active_session.collected_embeddings.clear()

        self._logger.info(f"Owner Created. Profile ID: {profile_id}")

        await event_bus.publish(
            Event(
                type=EventTypes.OWNER_PROFILE_CREATED,
                payload={"profile_id": profile_id},
            )
        )

        await setup_state_machine.transition_to(SetupState.VERIFYING)
        self._is_verifying = True

        self._active_session.current_phrase = "Zeus, please verify my voice."
        await event_bus.publish(
            Event(
                type=EventTypes.ENROLLMENT_NEXT_PHRASE,
                payload={
                    "current_phrase": self._active_session.current_phrase,
                    "current_sample": self._active_session.progress.accepted_samples,
                    "remaining_samples": 0,
                    "progress": self._active_session.progress.to_dict(),
                },
            )
        )

        return {"status": "verifying"}
