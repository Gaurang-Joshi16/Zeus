from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List

from services.ai.types.context import AIContext
from services.ai.types.request import AIRequestContext


class IWakeWordEngine(ABC):
    @abstractmethod
    async def detect(self, context: AIContext, audio_stream: Any) -> bool:
        pass


class ISpeechToTextEngine(ABC):
    @abstractmethod
    async def transcribe(
        self, context: AIContext, audio_stream: Any
    ) -> AsyncGenerator[str, None]:
        pass


class ITextToSpeechEngine(ABC):
    @abstractmethod
    async def synthesize(
        self, context: AIContext, text: str
    ) -> AsyncGenerator[bytes, None]:
        pass


import numpy as np


class ISpeakerVerificationEngine(ABC):
    @abstractmethod
    async def extract_embedding(
        self, context: AIContext, audio_stream: Any
    ) -> np.ndarray:
        pass

    @abstractmethod
    async def compare_embeddings(
        self, context: AIContext, emb1: np.ndarray, emb2: np.ndarray
    ) -> float:
        pass


class IEmbeddingEngine(ABC):
    @abstractmethod
    async def embed(self, context: AIContext, text: str) -> List[float]:
        pass


class IVisionEngine(ABC):
    @abstractmethod
    async def analyze(self, context: AIContext, image_data: bytes) -> Dict[str, Any]:
        pass


class ILLMEngine(ABC):
    @abstractmethod
    async def generate(
        self, context: 'AIRequestContext', prompt: str
    ) -> AsyncGenerator[str, None]:
        pass


class IOCREngine(ABC):
    @abstractmethod
    async def extract_text(self, context: AIContext, image_data: bytes) -> str:
        pass


class IVADEngine(ABC):
    @abstractmethod
    async def detect(self, context: AIContext, audio_stream: Any) -> float:
        pass
