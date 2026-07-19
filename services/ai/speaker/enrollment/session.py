import uuid
from typing import List

import numpy as np

from services.ai.speaker.enrollment.progress_tracker import EnrollmentProgressTracker


class EnrollmentSession:
    def __init__(self, required_samples: int):
        self.session_id = str(uuid.uuid4())
        self.required_samples = required_samples
        self.collected_embeddings: List[np.ndarray] = []
        self.current_phrase: str = ""
        self.is_active = True
        self.progress = EnrollmentProgressTracker(required_samples=required_samples)
