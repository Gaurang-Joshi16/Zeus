import time
from typing import Optional

import numpy as np

from services.ai.interfaces.engine import IWakeWordEngine
from services.ai.types.context import AIContext
from services.ai.wakeword.config import WakeWordConfiguration
from services.ai.wakeword.types import DetectionResult


class WakeWordInference:
    def __init__(
        self,
        engine: Optional[IWakeWordEngine],
        provider_id: str,
        config: WakeWordConfiguration,
    ):
        self.engine = engine
        self.provider_id = provider_id
        self.config = config
        self.model_version = "1.0.0"

    async def run(
        self, context: AIContext, frames: np.ndarray, chunk_id: str
    ) -> DetectionResult:
        start_time = time.time()

        probability = 0.0
        if self.engine:
            detected = await self.engine.detect(context, frames)
            probability = 1.0 if detected else 0.0

        inference_time_ms = (time.time() - start_time) * 1000

        status = (
            "DETECTED" if probability >= self.config.profile.threshold else "REJECTED"
        )

        return DetectionResult(
            status=status,
            probability=probability,
            threshold=self.config.profile.threshold,
            inference_time_ms=inference_time_ms,
            wake_word=self.config.profile.wake_words[0],
            provider=self.provider_id,
            model_version=self.model_version,
            chunk_id=chunk_id,
            session_id=context.session_id,
        )
