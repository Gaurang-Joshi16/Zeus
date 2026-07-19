import asyncio
import json
from typing import Any, AsyncGenerator, Dict

import httpx

from core.logging.logger import CoreLogger
from services.ai.interfaces.engine import ILLMEngine
from services.ai.interfaces.provider import IAIProvider
from services.ai.models.manager import ModelManager
from services.ai.types.request import AIRequestContext
from services.ai.types.enums import AIEngineType, ProviderLifecycleState
from services.ai.types.profile import (
    CapabilityDescriptor,
    ProviderCompatibility,
    ProviderProfile,
)


class OllamaEngine(ILLMEngine):
    def __init__(self, logger: CoreLogger):
        self._logger = logger
        self.endpoint = "http://localhost:11434/api/generate"

    async def generate(
        self, context: AIRequestContext, prompt: str
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": context.model,
            "prompt": prompt,
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", self.endpoint, json=payload, timeout=60.0) as response:
                    if response.status_code != 200:
                        err = await response.aread()
                        self._logger.error(f"Ollama error: {err}")
                        yield "I'm sorry, I'm having trouble connecting to my brain right now."
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            self._logger.error(f"Ollama connection error: {e}")
            yield "I am currently offline or unable to reach my language model."


class OllamaProvider(IAIProvider):
    def __init__(self, model_manager: ModelManager):
        self._model_manager = model_manager
        self._state = ProviderLifecycleState.UNINITIALIZED
        self._logger = CoreLogger.get_logger("zeus.llm.ollama")
        self._engine = None

    async def initialize(self) -> None:
        self._state = ProviderLifecycleState.INITIALIZING
        self._engine = OllamaEngine(self._logger)
        self._state = ProviderLifecycleState.READY

    async def load_model(self, model_id: str) -> None:
        self._state = ProviderLifecycleState.LOADING_MODEL
        # Optional: could trigger Ollama pull here if needed
        self._state = ProviderLifecycleState.READY

    async def unload_model(self, model_id: str) -> None:
        self._state = ProviderLifecycleState.READY

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "provider": "ollama", "state": self._state.value}

    def status(self) -> ProviderLifecycleState:
        return self._state

    def version(self) -> str:
        return "1.0.0"

    def profile(self) -> ProviderProfile:
        return ProviderProfile(performance_tier="high_performance", offline_support=True)

    def compatibility(self) -> ProviderCompatibility:
        return ProviderCompatibility()

    async def shutdown(self) -> None:
        self._state = ProviderLifecycleState.STOPPED

    def get_engine(self) -> Any:
        return self._engine

    @property
    def provider_id(self) -> str:
        return "ollama"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.LLM

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            capability_name="Ollama LLM Generation", supported_languages=["en"]
        )
