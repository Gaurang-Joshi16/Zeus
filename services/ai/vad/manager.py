from typing import Any, Dict

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from services.ai.registry.manager import AIEngineRegistry
from services.ai.types.enums import AIEngineType
from services.ai.vad.config import VADConfiguration
from services.ai.vad.detector import VADDetector
from services.ai.vad.health import VADHealth
from services.ai.vad.inference import VADInference
from services.ai.vad.pipeline import VADPipeline
from services.ai.vad.preprocessor import AudioPreprocessor
from services.ai.vad.session import VADSession
from services.ai.vad.statistics import VADStatistics
from services.ai.vad.types import VADState
from services.voice.audio.manager import AudioManager


class VADManager(BaseService):
    def __init__(self, audio_manager: AudioManager, ai_registry: AIEngineRegistry):
        super().__init__(name="vad_manager", dependencies=["audio_manager", "ai_registry"])
        self.audio_manager = audio_manager
        self.ai_registry = ai_registry

        self.config = VADConfiguration()
        self.stats = VADStatistics()
        self.health_tracker = VADHealth(self.stats)

        self.current_session = None
        self.detector = None

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing VAD Manager...")
        self.health_tracker.current_state = VADState.INITIALIZING

        provider = self.ai_registry.resolve(AIEngineType.VAD)
        if not provider:
            self.health_tracker.current_state = VADState.DISABLED
            raise RuntimeError("No VAD Provider found in registry.")

        self.health_tracker.provider_name = provider.provider_id

        model_name = "silerovad_model"
        try:
            await provider.load_model(model_name)
            self.health_tracker.loaded_model = model_name
        except Exception as e:
            self._logger.error(
                f"Failed to load model {model_name} for provider {provider.provider_id}: {e}"
            )
            self.health_tracker.current_state = VADState.FAILED
            raise

        engine = provider.get_engine()
        preprocessor = AudioPreprocessor(self.config)
        inference = VADInference(engine, provider.provider_id, self.config)
        pipeline = VADPipeline(preprocessor, inference)

        self.detector = VADDetector(
            stream=self.audio_manager.stream,
            pipeline=pipeline,
            config=self.config,
            stats=self.stats,
            health=self.health_tracker,
        )

        await event_bus.publish(Event(type="VAD_INITIALIZED", payload={}))

    async def _do_start(self) -> None:
        if not self.detector or self.health_tracker.current_state in [
            VADState.DISABLED,
            VADState.FAILED,
        ]:
            raise RuntimeError("VAD Manager cannot start. Detector not initialized or failed.")

        self._logger.info("Starting VAD Manager...")
        self.current_session = VADSession()
        await self.detector.start(self.current_session.session_id)

    async def _do_stop(self) -> None:
        self._logger.info("Stopping VAD Manager...")
        if self.detector:
            await self.detector.stop()

        if self.current_session:
            self.current_session.stop()
            self.stats.record_session_end(self.current_session)
            self.current_session = None

    async def health(self) -> Dict[str, Any]:
        base_health = await super().health()
        base_health.update(self.health_tracker.get_health())
        return base_health
