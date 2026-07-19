from typing import Any, Dict

from services.ai.speaker.statistics import SpeakerStatistics
from services.ai.speaker.types import SpeakerState


class SpeakerHealth:
    def __init__(self, stats: SpeakerStatistics):
        self.stats = stats
        self.current_state = SpeakerState.UNINITIALIZED
        self.provider_name = "None"
        self.loaded_model = "None"
        self.memory_usage_estimate: float = 0.0
        self.provider_health: str = "unknown"

    def get_health(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state.value,
            "provider": self.provider_name,
            "loaded_model": self.loaded_model,
            "enrollment_status": (
                "READY" if self.current_state == SpeakerState.READY else "BUSY"
            ),
            "average_verification_time_ms": self.stats.average_verification_time_ms,
            "memory_usage_estimate": self.memory_usage_estimate,
            "provider_health": self.provider_health,
            "loaded_profiles": self.stats.profile_count,
        }
