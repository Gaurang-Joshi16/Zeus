import time
from typing import Optional

from services.ai.interfaces.engine import IVADEngine
from services.ai.types.context import AIContext
from services.ai.vad.config import VADConfiguration
from services.ai.vad.types import PreprocessedAudio, SpeechActivityResult


class VADInference:
    def __init__(
        self, engine: Optional[IVADEngine], provider_id: str, config: VADConfiguration
    ):
        self.engine = engine
        self.provider_id = provider_id
        self.config = config

    async def run(
        self, context: AIContext, audio: PreprocessedAudio
    ) -> SpeechActivityResult:
        start_time = time.time()

        confidence = 0.0
        if audio.rms_energy < self.config.energy_threshold:
            confidence = 0.0
        elif self.engine:
            confidence = await self.engine.detect(context, audio.frames)

        inference_time_ms = (time.time() - start_time) * 1000

        speech_detected = confidence > 0.5

        return SpeechActivityResult(
            speech_detected=speech_detected,
            confidence=confidence,
            energy=audio.rms_energy,
            provider=self.provider_id,
            inference_time_ms=inference_time_ms,
            chunk_id=audio.chunk_id,
            session_id=context.session_id,
            timestamp=audio.timestamp,
        )
