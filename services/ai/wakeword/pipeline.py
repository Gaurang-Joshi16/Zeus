import numpy as np

from services.ai.types.context import AIContext
from services.ai.wakeword.inference import WakeWordInference
from services.ai.wakeword.preprocessor import AudioPreprocessor
from services.ai.wakeword.types import DetectionResult


class WakeWordPipeline:
    def __init__(self, preprocessor: AudioPreprocessor, inference: WakeWordInference):
        self.preprocessor = preprocessor
        self.inference = inference

    async def process(
        self, context: AIContext, frames: np.ndarray, chunk_id: str
    ) -> DetectionResult:
        processed_frames = self.preprocessor.process(frames)
        result = await self.inference.run(context, processed_frames, chunk_id)
        return result
