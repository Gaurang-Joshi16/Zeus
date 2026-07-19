from enum import Enum
from typing import Tuple

import numpy as np


class QualityResult(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class EnrollmentQualityAnalyzer:
    def __init__(
        self,
        min_quality: float = 0.8,
        min_duration_ms: int = 1500,
        max_duration_ms: int = 5000,
    ):
        self.min_quality = min_quality
        self.min_duration_ms = min_duration_ms
        self.max_duration_ms = max_duration_ms

    def analyze(
        self, frames: np.ndarray, sample_rate: int = 16000
    ) -> Tuple[QualityResult, str]:
        if len(frames) == 0:
            return QualityResult.FAIL, "NO_SPEECH_DETECTED"

        duration_ms = (len(frames) / sample_rate) * 1000
        if duration_ms < self.min_duration_ms:
            return (
                QualityResult.FAIL,
                "RECORDING_TOO_SHORT",
            )
        if duration_ms > self.max_duration_ms:
            return QualityResult.FAIL, "RECORDING_TOO_LONG"

        rms_energy = float(np.sqrt(np.mean(frames.flatten() ** 2)))
        if rms_energy < 0.01:
            return QualityResult.FAIL, "MICROPHONE_TOO_QUIET"

        peak = float(np.max(np.abs(frames)))
        if peak > 0.99:
            return QualityResult.WARNING, "AUDIO_CLIPPING"

        if rms_energy < self.min_quality * 0.1:
            return QualityResult.WARNING, "TOO_MUCH_BACKGROUND_NOISE"

        return QualityResult.PASS, "PASS"
