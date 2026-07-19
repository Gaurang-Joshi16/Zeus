from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import numpy as np


class VADState(str, Enum):
    DISABLED = "DISABLED"
    INITIALIZING = "INITIALIZING"
    MONITORING = "MONITORING"
    SPEECH_DETECTED = "SPEECH_DETECTED"
    SILENCE = "SILENCE"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


@dataclass
class PreprocessedAudio:
    frames: np.ndarray
    rms_energy: float
    peak_energy: float
    noise_floor: float
    sample_rate: int
    channel_count: int
    chunk_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SpeechActivityResult:
    speech_detected: bool
    confidence: float
    energy: float
    provider: str
    inference_time_ms: float
    chunk_id: str
    session_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class VoiceSegment:
    segment_id: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    average_energy: float
    peak_energy: float
    sample_count: int
    speech_ratio: float
