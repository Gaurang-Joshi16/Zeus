import numpy as np

from services.ai.types.context import AIContext
from services.ai.vad.inference import VADInference
from services.ai.vad.preprocessor import AudioPreprocessor
from services.ai.vad.types import SpeechActivityResult


class VADPipeline:
    def __init__(self, preprocessor: AudioPreprocessor, inference: VADInference):
        self.preprocessor = preprocessor
        self.inference = inference

    async def process(
        self, context: AIContext, frames: np.ndarray, sample_rate: int, chunk_id: str
    ) -> SpeechActivityResult:
        preprocessed = self.preprocessor.process(frames, sample_rate, chunk_id)
        result = await self.inference.run(context, preprocessed)
        return result
