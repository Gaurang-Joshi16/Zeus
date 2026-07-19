from typing import Any, Dict

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from services.ai.registry.manager import AIEngineRegistry
from services.ai.types.enums import AIEngineType
from services.ai.wakeword.config import WakeWordConfiguration
from services.ai.wakeword.detector import WakeWordDetector
from services.ai.wakeword.health import WakeWordHealth
from services.ai.wakeword.inference import WakeWordInference
from services.ai.wakeword.pipeline import WakeWordPipeline
from services.ai.wakeword.preprocessor import AudioPreprocessor
from services.ai.wakeword.session import WakeWordSession
from services.ai.wakeword.statistics import WakeWordStatistics
from services.ai.wakeword.types import WakeWordState
from services.voice.audio.manager import AudioManager


class WakeWordManager(BaseService):
    def __init__(self, audio_manager: AudioManager, ai_registry: AIEngineRegistry):
        super().__init__(name="wakeword_manager", dependencies=["audio_manager", "ai_registry"])
        self.audio_manager = audio_manager
        self.ai_registry = ai_registry

        self.config = WakeWordConfiguration()
        self.stats = WakeWordStatistics()
        self.health_tracker = WakeWordHealth(self.stats)

        self.current_session = None
        self.detector = None

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing Wake Word Manager...")
        self.health_tracker.current_state = WakeWordState.INITIALIZING

        provider = self.ai_registry.resolve(AIEngineType.WAKE_WORD)
        if not provider:
            self.health_tracker.current_state = WakeWordState.DISABLED
            raise RuntimeError("No Wake Word Provider found in registry.")

        self.health_tracker.provider_name = provider.provider_id

        model_name = self.config.profile.supported_model
        try:
            await provider.load_model(model_name)
            self.health_tracker.loaded_model = model_name
        except Exception as e:
            self._logger.error(
                f"Failed to load model {model_name} for provider {provider.provider_id}: {e}"
            )
            self.health_tracker.current_state = WakeWordState.FAILED
            raise

        engine = provider.get_engine()
        preprocessor = AudioPreprocessor()
        inference = WakeWordInference(engine, provider.provider_id, self.config)
        pipeline = WakeWordPipeline(preprocessor, inference)

        self.detector = WakeWordDetector(
            stream=self.audio_manager.stream,
            pipeline=pipeline,
            config=self.config,
            stats=self.stats,
            health=self.health_tracker,
        )

        await event_bus.publish(Event(type="WAKEWORD_INITIALIZED", payload={}))

    async def _do_start(self) -> None:
        if not self.detector or self.health_tracker.current_state in [
            WakeWordState.DISABLED,
            WakeWordState.FAILED,
        ]:
            raise RuntimeError("Wake Word Manager cannot start. Detector not initialized or failed.")

        self._logger.info("Starting Wake Word Manager...")
        self.current_session = WakeWordSession()
        await self.detector.start(self.current_session.session_id)

    async def _do_stop(self) -> None:
        self._logger.info("Stopping Wake Word Manager...")
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
