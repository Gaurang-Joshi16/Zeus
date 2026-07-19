from typing import Any, Dict

from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from services.ai.registry.manager import AIEngineRegistry
from services.ai.speaker.audio import VerificationAudioProvider
from services.ai.speaker.config import SpeakerConfiguration
from services.ai.speaker.detector import SpeakerDetector
from services.ai.speaker.health import SpeakerHealth
from services.ai.speaker.inference import SpeakerInference
from services.ai.speaker.pipeline import SpeakerPipeline
from services.ai.speaker.statistics import SpeakerStatistics
from services.ai.speaker.store import SpeakerStore
from services.ai.speaker.types import SpeakerState
from services.ai.speaker.verifier import SpeakerVerifier
from services.ai.types.enums import AIEngineType
from services.voice.audio.manager import AudioManager


class SpeakerManager(BaseService):
    def __init__(self, audio_manager: AudioManager, ai_registry: AIEngineRegistry):
        super().__init__(name="speaker_manager", dependencies=["audio_manager", "ai_registry"])
        self.audio_manager = audio_manager
        self.ai_registry = ai_registry

        self.config = SpeakerConfiguration()
        self.stats = SpeakerStatistics()
        self.health_tracker = SpeakerHealth(self.stats)
        self.store = SpeakerStore(encryption_enabled=self.config.encryption_enabled)

        self.enrollment = None
        self.detector = None

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing Speaker Manager...")
        self.health_tracker.current_state = SpeakerState.UNINITIALIZED

        provider = self.ai_registry.resolve(AIEngineType.SPEAKER_VERIFICATION)
        if not provider:
            self.health_tracker.current_state = SpeakerState.DISABLED
            raise RuntimeError("No Speaker Provider found in registry.")

        self.health_tracker.provider_name = provider.provider_id

        model_name = "speaker_model"
        try:
            await provider.load_model(model_name)
            self.health_tracker.loaded_model = model_name
        except Exception as e:
            self._logger.error(
                f"Failed to load model {model_name} for provider {provider.provider_id}: {e}"
            )
            self.health_tracker.current_state = SpeakerState.FAILED
            raise

        engine = provider.get_engine()
        inference = SpeakerInference(engine, provider.provider_id, self.config)
        verifier = SpeakerVerifier(self.store, inference, self.config)
        audio_provider = VerificationAudioProvider(self.audio_manager.stream)
        pipeline = SpeakerPipeline(audio_provider, inference, verifier)

        from services.ai.speaker.enrollment.controller import EnrollmentController
        from services.ai.speaker.enrollment.wizard import EnrollmentWizard

        self.enrollment_controller = EnrollmentController(
            self.store, self.config, pipeline, self.audio_manager
        )
        self.enrollment_wizard = EnrollmentWizard(self.enrollment_controller)

        self.detector = SpeakerDetector(
            pipeline=pipeline,
            config=self.config,
            stats=self.stats,
            health=self.health_tracker,
        )

        self.health_tracker.current_state = SpeakerState.READY

    async def _do_start(self) -> None:
        if not self.detector or self.health_tracker.current_state in [
            SpeakerState.DISABLED,
            SpeakerState.FAILED,
        ]:
            raise RuntimeError("Speaker Manager cannot start. Detector not initialized or failed.")

        self._logger.info("Starting Speaker Manager...")
        await self.detector.start()

    async def _do_stop(self) -> None:
        self._logger.info("Stopping Speaker Manager...")
        if self.detector:
            await self.detector.stop()

    async def health(self) -> Dict[str, Any]:
        base_health = await super().health()
        base_health.update(self.health_tracker.get_health())
        return base_health
