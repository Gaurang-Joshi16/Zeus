import numpy as np


class AudioPreprocessor:
    """
    Passes audio through unchanged initially.
    Future: Noise Reduction, Gain Normalization, VAD, Sample Conversion.
    """

    def process(self, frames: np.ndarray) -> np.ndarray:
        return frames
