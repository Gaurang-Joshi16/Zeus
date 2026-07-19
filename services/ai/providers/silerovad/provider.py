import asyncio
from typing import Any, Dict

from services.ai.interfaces.engine import IVADEngine
from services.ai.interfaces.provider import IAIProvider
from services.ai.models.manager import ModelManager
from services.ai.types.context import AIContext
from services.ai.types.enums import AIEngineType, ProviderLifecycleState
from services.ai.types.profile import (
    CapabilityDescriptor,
    ProviderCompatibility,
    ProviderProfile,
)


class SileroVADEngine(IVADEngine):
    async def detect(self, context: AIContext, audio_stream: Any) -> float:
        # Placeholder for actual inference logic.
        return 0.9


class SileroVADProvider(IAIProvider):
    def __init__(self, model_manager: ModelManager):
        self._model_manager = model_manager
        self._state = ProviderLifecycleState.UNINITIALIZED
        self._engine = SileroVADEngine()

    @property
    def provider_id(self) -> str:
        return "silerovad"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.VAD

    async def initialize(self) -> None:
        self._state = ProviderLifecycleState.INITIALIZING
        await asyncio.sleep(0.1)
        self._state = ProviderLifecycleState.READY

    async def load_model(self, model_id: str) -> None:
        self._state = ProviderLifecycleState.LOADING_MODEL
        await self._model_manager.load_model(model_id)
        self._state = ProviderLifecycleState.READY

    async def unload_model(self, model_id: str) -> None:
        self._state = ProviderLifecycleState.UNLOADING
        await self._model_manager.release_model(model_id)
        self._state = ProviderLifecycleState.READY

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "mocked": True}

    def status(self) -> ProviderLifecycleState:
        return self._state

    def version(self) -> str:
        return "0.1.0"

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            capability_name="Silero VAD",
            supported_languages=["any"],
            streaming_support=True,
            provides_confidence_scores=True,
        )

    def profile(self) -> ProviderProfile:
        return ProviderProfile(
            performance_tier="high",
            offline_support=True,
            gpu_requirement="none",
            recommended_use_case="general",
        )

    def compatibility(self) -> ProviderCompatibility:
        return ProviderCompatibility()

    async def shutdown(self) -> None:
        self._state = ProviderLifecycleState.STOPPED

    def get_engine(self) -> IVADEngine:
        return self._engine
