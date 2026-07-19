from datetime import datetime
from typing import Any, Dict, List

from services.ai.wakeword.session import WakeWordSession


class WakeWordStatistics:
    def __init__(self):
        self.total_activations: int = 0
        self.false_activations: int = 0
        self.rejected_activations: int = 0
        self.average_detection_time_ms: float = 0.0
        self.average_confidence: float = 0.0

        self.activation_timeline: List[Dict[str, Any]] = []
        self.rejected_timeline: List[Dict[str, Any]] = []
        self.cooldown_count: int = 0
        self.maximum_activations_reached: int = 0

        self.session_history: List[WakeWordSession] = []

    def record_activation(
        self, confidence: float, detection_time_ms: float, timestamp: datetime
    ):
        self.total_activations += 1
        self.activation_timeline.append(
            {
                "timestamp": timestamp.isoformat(),
                "confidence": confidence,
                "inference_time_ms": detection_time_ms,
            }
        )

        self.average_confidence = (
            self.average_confidence
            + (confidence - self.average_confidence) / self.total_activations
        )
        self.average_detection_time_ms = (
            self.average_detection_time_ms
            + (detection_time_ms - self.average_detection_time_ms)
            / self.total_activations
        )

    def record_rejection(self, confidence: float, timestamp: datetime):
        self.rejected_activations += 1
        self.rejected_timeline.append(
            {"timestamp": timestamp.isoformat(), "confidence": confidence}
        )

    def record_cooldown_hit(self):
        self.cooldown_count += 1

    def record_session_end(self, session: WakeWordSession):
        self.session_history.append(session)
