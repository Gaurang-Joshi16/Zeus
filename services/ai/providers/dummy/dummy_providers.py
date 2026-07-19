import asyncio
from typing import Any, AsyncGenerator, Dict, List

from services.ai.interfaces.engine import (
    IEmbeddingEngine,
    ILLMEngine,
    IOCREngine,
    ISpeakerVerificationEngine,
    ISpeechToTextEngine,
    ITextToSpeechEngine,
    IVADEngine,
    IVisionEngine,
    IWakeWordEngine,
)
from services.ai.interfaces.provider import IAIProvider
from services.ai.models.manager import ModelManager
from services.ai.types.context import AIContext
from services.ai.types.request import AIRequestContext
from services.ai.types.enums import AIEngineType, ProviderLifecycleState
from services.ai.types.profile import (
    CapabilityDescriptor,
    ProviderCompatibility,
    ProviderProfile,
)


class BaseDummyProvider(IAIProvider):
    def __init__(self, model_manager: ModelManager):
        self._model_manager = model_manager
        self._state = ProviderLifecycleState.UNINITIALIZED
        self._engine = None

    async def initialize(self) -> None:
        self._state = ProviderLifecycleState.INITIALIZING
        await asyncio.sleep(0.1)
        self._state = ProviderLifecycleState.READY

    async def load_model(self, model_id: str) -> None:
        self._state = ProviderLifecycleState.LOADING_MODEL
        await asyncio.sleep(0.1)
        self._state = ProviderLifecycleState.READY

    async def unload_model(self, model_id: str) -> None:
        self._state = ProviderLifecycleState.UNLOADING
        await asyncio.sleep(0.1)
        self._state = ProviderLifecycleState.READY

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "mocked": True}

    def status(self) -> ProviderLifecycleState:
        return self._state

    def version(self) -> str:
        return "1.0.0"

    def profile(self) -> ProviderProfile:
        return ProviderProfile(performance_tier="low_power", offline_support=True)

    def compatibility(self) -> ProviderCompatibility:
        return ProviderCompatibility()

    async def shutdown(self) -> None:
        self._state = ProviderLifecycleState.STOPPED

    def get_engine(self) -> Any:
        return self._engine


# STT
class DummySTTEngine(ISpeechToTextEngine):
    async def transcribe(
        self, context: AIContext, audio_stream: Any
    ) -> AsyncGenerator[str, None]:
        yield "This is a simulated transcription."


class DummySTTProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummySTTEngine()

    @property
    def provider_id(self) -> str:
        return "dummy_stt"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.STT

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            capability_name="Simulated STT", supported_languages=["en"]
        )


# TTS
class DummyTTSEngine(ITextToSpeechEngine):
    async def synthesize(
        self, context: AIContext, text: str
    ) -> AsyncGenerator[bytes, None]:
        yield b"simulated_audio_data"


class DummyTTSProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummyTTSEngine()

    @property
    def provider_id(self) -> str:
        return "dummy_tts"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.TTS

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            capability_name="Simulated TTS", supported_languages=["en"]
        )


# Wake Word
class DummyWakeWordEngine(IWakeWordEngine):
    async def detect(self, context: AIContext, audio_stream: Any) -> bool:
        from core.config.manager import ConfigManager
        if ConfigManager.get("ZEUS_SIMULATE_WAKEWORD", "true").lower() == "true":
            return True
        return False


class DummyWakeWordProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummyWakeWordEngine()

    @property
    def provider_id(self) -> str:
        return "dummy_wake_word"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.WAKE_WORD

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(capability_name="Simulated Wake Word")


# Speaker Verification
import numpy as np


class DummySpeakerVerificationEngine(ISpeakerVerificationEngine):
    async def extract_embedding(
        self, context: AIContext, audio_stream: Any
    ) -> np.ndarray:
        return np.random.rand(192)

    async def compare_embeddings(
        self, context: AIContext, emb1: np.ndarray, emb2: np.ndarray
    ) -> float:
        return 0.99


class DummySpeakerVerificationProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummySpeakerVerificationEngine()

    @property
    def provider_id(self) -> str:
        return "dummy_speaker_verification"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.SPEAKER_VERIFICATION

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(capability_name="Simulated Speaker Verification")


# Embedding
class DummyEmbeddingEngine(IEmbeddingEngine):
    async def embed(self, context: AIContext, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]


class DummyEmbeddingProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummyEmbeddingEngine()

    @property
    def provider_id(self) -> str:
        return "dummy_embedding"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.EMBEDDING

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(capability_name="Simulated Embedding")


# Vision
class DummyVisionEngine(IVisionEngine):
    async def analyze(self, context: AIContext, image_data: bytes) -> Dict[str, Any]:
        return {"description": "A simulated image."}


class DummyVisionProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummyVisionEngine()

    @property
    def provider_id(self) -> str:
        return "dummy_vision"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.VISION

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(capability_name="Simulated Vision")


# LLM
class DummyLLMEngine(ILLMEngine):
    async def generate(
        self, context: 'AIRequestContext', prompt: str
    ) -> AsyncGenerator[str, None]:
        response = f"This is a simulated response to: '{prompt}'."
        words = response.split(" ")
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)


class DummyLLMProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummyLLMEngine()

    @property
    def provider_id(self) -> str:
        return "dummy_llm"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.LLM

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(capability_name="Simulated LLM")


# OCR
class DummyOCREngine(IOCREngine):
    async def extract_text(self, context: AIContext, image_data: bytes) -> str:
        return "Simulated Extracted Text"


class DummyOCRProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummyOCREngine()

    @property
    def provider_id(self) -> str:
        return "dummy_ocr"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.OCR

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(capability_name="Simulated OCR")


# VAD
class DummyVADEngine(IVADEngine):
    async def detect(self, context: AIContext, audio_stream: Any) -> float:
        # Simulate alternating speech/silence or just return random confidence
        return 0.8


class DummyVADProvider(BaseDummyProvider):
    def __init__(self, model_manager: ModelManager):
        super().__init__(model_manager)
        self._engine = DummyVADEngine()

    @property
    def provider_id(self) -> str:
        return "dummy_vad"

    @property
    def engine_type(self) -> AIEngineType:
        return AIEngineType.VAD

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(capability_name="Simulated VAD")
