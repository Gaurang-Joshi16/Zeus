from dataclasses import dataclass


@dataclass
class EnrollmentProgress:
    current_sample: int
    required_samples: int
    current_phrase: str
    overall_progress: float
    estimated_time_remaining_sec: float
