from typing import Any, Dict

from services.ai.wakeword.statistics import WakeWordStatistics
from services.ai.wakeword.types import WakeWordState


class WakeWordHealth:
    def __init__(self, stats: WakeWordStatistics):
        self.stats = stats
        self.current_state = WakeWordState.DISABLED
        self.loaded_model = "None"
        self.provider_name = "None"

        self.maximum_inference_time_ms: float = 0.0
        self.dropped_chunks: int = 0
        self.audio_queue_size: int = 0
        self.provider_health: str = "unknown"
        self.cpu_usage_estimate: float = 0.0

    def update_inference_time(self, time_ms: float):
        if time_ms > self.maximum_inference_time_ms:
            self.maximum_inference_time_ms = time_ms

    def get_health(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state.value,
            "loaded_model": self.loaded_model,
            "provider": self.provider_name,
            "provider_health": self.provider_health,
            "cpu_usage_estimate": self.cpu_usage_estimate,
            "average_inference_time_ms": self.stats.average_detection_time_ms,
            "maximum_inference_time_ms": self.maximum_inference_time_ms,
            "activation_count": self.stats.total_activations,
            "dropped_chunks": self.dropped_chunks,
            "audio_queue_size": self.audio_queue_size,
            "uptime_seconds": sum(
                s.duration_seconds() for s in self.stats.session_history
            ),
        }
