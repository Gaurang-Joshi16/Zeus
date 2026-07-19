from typing import Any, AsyncGenerator

from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from services.ai.factory.manager import AIProviderFactory
from services.ai.types.context import AIContext
from services.ai.types.enums import AIEngineType


class STTManager(BaseService):
    def __init__(self, ai_factory: AIProviderFactory):
        super().__init__(name="stt_manager", dependencies=["ai_factory"])
        self.ai_factory = ai_factory
        self._engine = None

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing STT Manager...")
        provider = self.ai_factory.registry.resolve(AIEngineType.STT)
        if not provider:
            self._logger.warning("No STT providers registered!")
            return
            
        self.provider = provider
        self._engine = self.provider.get_engine()
        self._logger.info(f"STT Manager bound to {self.provider.provider_id}")

    async def _do_start(self) -> None:
        pass

    async def _do_stop(self) -> None:
        pass

    async def transcribe_stream(
        self, context: AIContext, audio_stream: Any
    ) -> AsyncGenerator[str, None]:
        """
        Takes an audio buffer/stream and yields partial transcripts.
        """
        if not self._engine:
            self._logger.error("No STT engine available to transcribe.")
            yield ""
            return

        async for partial_text in self._engine.transcribe(context, audio_stream):
            yield partial_text
