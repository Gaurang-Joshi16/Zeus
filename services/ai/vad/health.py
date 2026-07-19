from typing import Any, Dict

from services.ai.vad.statistics import VADStatistics
from services.ai.vad.types import VADState


class VADHealth:
    def __init__(self, stats: VADStatistics):
        self.stats = stats
        self.current_state = VADState.DISABLED
        self.loaded_model = "None"
        self.provider_name = "None"

        self.current_threshold: float = 0.0
        self.cpu_usage_estimate: float = 0.0

    def get_health(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state.value,
            "provider": self.provider_name,
            "loaded_model": self.loaded_model,
            "inference_time_ms": self.stats.average_inference_time_ms,
            "average_cpu_usage": self.cpu_usage_estimate,
            "current_threshold": self.current_threshold,
            "segments_processed": len(self.stats.speech_segments),
            "dropped_frames": self.stats.dropped_frames,
            "speech_time_ms": self.stats.speech_time_ms,
            "silence_time_ms": self.stats.silence_time_ms,
            "uptime_seconds": sum(
                s.duration_seconds() for s in self.stats.session_history
            ),
        }
