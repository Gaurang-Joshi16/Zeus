from datetime import datetime, timezone

import numpy as np

from services.ai.vad.config import VADConfiguration
from services.ai.vad.types import PreprocessedAudio


class AudioPreprocessor:
    def __init__(self, config: VADConfiguration):
        self.config = config
        self._noise_floor = config.noise_floor

    def process(
        self, frames: np.ndarray, sample_rate: int, chunk_id: str
    ) -> PreprocessedAudio:
        if len(frames) == 0:
            rms_energy = 0.0
            peak_energy = 0.0
            channels = 1
        else:
            flat_frames = frames.flatten()
            rms_energy = float(np.sqrt(np.mean(flat_frames**2)))
            peak_energy = float(np.max(np.abs(flat_frames)))
            channels = frames.shape[1] if len(frames.shape) > 1 else 1

            if self.config.adaptive_threshold:
                if rms_energy < self._noise_floor * 2:
                    self._noise_floor = 0.99 * self._noise_floor + 0.01 * rms_energy

        return PreprocessedAudio(
            frames=frames,
            rms_energy=rms_energy,
            peak_energy=peak_energy,
            noise_floor=self._noise_floor,
            sample_rate=sample_rate,
            channel_count=channels,
            chunk_id=chunk_id,
            timestamp=datetime.now(timezone.utc),
        )
