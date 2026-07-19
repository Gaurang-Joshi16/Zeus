from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class EnrollmentProgressTracker:
    required_samples: int
    accepted_samples: int = 0
    rejected_samples: int = 0
    retries: int = 0
    elapsed_time: float = 0.0

    @property
    def completion_percentage(self) -> float:
        if self.required_samples == 0:
            return 0.0
        return min(100.0, (self.accepted_samples / self.required_samples) * 100.0)

    @property
    def estimated_remaining_time(self) -> float:
        remaining = self.required_samples - self.accepted_samples
        if remaining <= 0:
            return 0.0
        # Assume 3 seconds per sample on average
        return remaining * 3.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted_samples": self.accepted_samples,
            "rejected_samples": self.rejected_samples,
            "retries": self.retries,
            "elapsed_time": self.elapsed_time,
            "estimated_remaining_time": self.estimated_remaining_time,
            "completion_percentage": self.completion_percentage,
            "required_samples": self.required_samples,
        }
