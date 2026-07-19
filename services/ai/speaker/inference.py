from typing import Optional

import numpy as np

from services.ai.interfaces.engine import ISpeakerVerificationEngine
from services.ai.speaker.config import SpeakerConfiguration
from services.ai.types.context import AIContext


class SpeakerInference:
    def __init__(
        self,
        engine: Optional[ISpeakerVerificationEngine],
        provider_id: str,
        config: SpeakerConfiguration,
    ):
        self.engine = engine
        self.provider_id = provider_id
        self.config = config
        self.model_version = "1.0.0"

    async def extract_embedding(self, frames: np.ndarray) -> np.ndarray:
        if not self.engine:
            return np.random.rand(self.config.embedding_size)
        context = AIContext(session_id="inference", user_id="system")
        return await self.engine.extract_embedding(context, frames)

    async def compare_embeddings(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        if not self.engine:
            return 0.0
        context = AIContext(session_id="inference", user_id="system")
        return await self.engine.compare_embeddings(context, emb1, emb2)
