from typing import Any, Dict, Type

from core.config.manager import ConfigManager
from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from services.ai.interfaces.provider import IAIProvider
from services.ai.models.manager import ModelManager

# Import dummy providers for registration
from services.ai.providers.dummy.dummy_providers import (
    DummyEmbeddingProvider,
    DummyLLMProvider,
    DummyOCRProvider,
    DummySpeakerVerificationProvider,
    DummySTTProvider,
    DummyTTSProvider,
    DummyVADProvider,
    DummyVisionProvider,
    DummyWakeWordProvider,
)
from services.ai.providers.ecapatdnn.provider import ECAPATDNNProvider
from services.ai.providers.openwakeword.provider import OpenWakeWordProvider
from services.ai.providers.resemblyzer.provider import ResemblyzerProvider
from services.ai.providers.silerovad.provider import SileroVADProvider
from services.ai.providers.faster_whisper.provider import FasterWhisperProvider
from services.ai.registry.manager import AIEngineRegistry
from services.ai.types.enums import AIEngineType


class AIProviderFactory(BaseService):
    def __init__(self, registry: AIEngineRegistry, model_manager: ModelManager):
        super().__init__(name="ai_factory", dependencies=["model_manager"])
        self.registry = registry
        self.model_manager = model_manager

        self._provider_classes: Dict[str, Type[IAIProvider]] = {}

        self.register_provider_class("dummy_stt", DummySTTProvider)
        self.register_provider_class("dummy_tts", DummyTTSProvider)
        self.register_provider_class("dummy_wake_word", DummyWakeWordProvider)
        self.register_provider_class(
            "dummy_speaker_verification", DummySpeakerVerificationProvider
        )
        self.register_provider_class("dummy_embedding", DummyEmbeddingProvider)
        self.register_provider_class("dummy_vision", DummyVisionProvider)
        self.register_provider_class("dummy_llm", DummyLLMProvider)
        self.register_provider_class("dummy_ocr", DummyOCRProvider)
        self.register_provider_class("dummy_vad", DummyVADProvider)
        self.register_provider_class("openwakeword", OpenWakeWordProvider)
        self.register_provider_class("silerovad", SileroVADProvider)
        self.register_provider_class("ecapatdnn", ECAPATDNNProvider)
        self.register_provider_class("resemblyzer", ResemblyzerProvider)
        self.register_provider_class("faster_whisper", FasterWhisperProvider)
        from services.ai.providers.ollama.provider import OllamaProvider
        self.register_provider_class("ollama", OllamaProvider)

    def register_provider_class(
        self, provider_id: str, provider_cls: Type[IAIProvider]
    ) -> None:
        self._provider_classes[provider_id] = provider_cls

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing AI Provider Factory...")
        await self._instantiate_and_register(
            AIEngineType.STT, ConfigManager.get("ZEUS_AI_PREFERRED_STT", "faster_whisper")
        )
        await self._instantiate_and_register(
            AIEngineType.TTS, ConfigManager.get("ZEUS_AI_PREFERRED_TTS", "dummy_tts")
        )
        await self._instantiate_and_register(
            AIEngineType.WAKE_WORD,
            ConfigManager.get("ZEUS_AI_PREFERRED_WAKE_WORD", "dummy_wake_word"),
        )
        await self._instantiate_and_register(
            AIEngineType.SPEAKER_VERIFICATION,
            ConfigManager.get(
                "ZEUS_AI_PREFERRED_SPEAKER_VERIFICATION", "dummy_speaker_verification"
            ),
        )
        await self._instantiate_and_register(
            AIEngineType.EMBEDDING,
            ConfigManager.get("ZEUS_AI_PREFERRED_EMBEDDING", "dummy_embedding"),
        )
        await self._instantiate_and_register(
            AIEngineType.VISION,
            ConfigManager.get("ZEUS_AI_PREFERRED_VISION", "dummy_vision"),
        )
        await self._instantiate_and_register(
            AIEngineType.LLM, ConfigManager.get("AI_LLM_PROVIDER", "ollama")
        )
        await self._instantiate_and_register(
            AIEngineType.OCR, ConfigManager.get("ZEUS_AI_PREFERRED_OCR", "dummy_ocr")
        )
        await self._instantiate_and_register(
            AIEngineType.VAD, ConfigManager.get("ZEUS_AI_PREFERRED_VAD", "silerovad")
        )
        await self._instantiate_and_register(
            AIEngineType.SPEAKER_VERIFICATION,
            ConfigManager.get("ZEUS_AI_PREFERRED_SPEAKER", "ecapatdnn"),
        )

    async def _do_start(self) -> None:
        self._logger.info("AI Provider Factory started.")

    async def _do_stop(self) -> None:
        self._logger.info("AI Provider Factory stopping...")
        for provider in self.registry.get_all_providers():
            await provider.shutdown()

    async def health(self) -> Dict[str, Any]:
        base_health = await super().health()
        base_health.update({"registered_classes": len(self._provider_classes)})
        return base_health

    async def _instantiate_and_register(
        self, engine_type: AIEngineType, provider_id: str
    ) -> None:
        if provider_id not in self._provider_classes:
            self._logger.error(
                f"Cannot instantiate provider {provider_id}: Not found in registration table."
            )
            return

        provider_cls = self._provider_classes[provider_id]

        try:
            provider_instance = provider_cls(model_manager=self.model_manager)

            if not self._validate_compatibility(provider_instance):
                self._logger.error(
                    f"Provider {provider_id} failed compatibility validation. Skipping."
                )
                return

            await provider_instance.initialize()
            await self.registry.register(provider_instance)
        except Exception as e:
            self._logger.error(f"Failed to instantiate provider {provider_id}: {e}")

    def _validate_compatibility(self, provider: IAIProvider) -> bool:
        compat = provider.compatibility()
        # Simulated validation check
        return True
