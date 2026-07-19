from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List


class WakeWordState(str, Enum):
    DISABLED = "DISABLED"
    INITIALIZING = "INITIALIZING"
    LISTENING = "LISTENING"
    DETECTING = "DETECTING"
    COOLDOWN = "COOLDOWN"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass
class DetectionResult:
    status: str
    probability: float
    threshold: float
    inference_time_ms: float
    wake_word: str
    provider: str
    model_version: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    chunk_id: str = ""
    session_id: str = ""


@dataclass
class WakeWordProfile:
    wake_words: List[str] = field(default_factory=lambda: ["Zeus"])
    language: str = "en"
    sensitivity: float = 0.5
    threshold: float = 0.8
    cooldown_seconds: float = 2.0
    detection_window_ms: int = 1500
    maximum_rate_per_minute: int = 10
    supported_model: str = "openwakeword_model"
