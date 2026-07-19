from typing import Any, Dict, List

from services.ai.speaker.types import SpeakerAuthenticationSession


class SpeakerStatistics:
    def __init__(self):
        self.enrollment_count: int = 0
        self.successful_verifications: int = 0
        self.rejected_verifications: int = 0
        self.average_confidence: float = 0.0
        self.average_verification_time_ms: float = 0.0
        self.profile_count: int = 0
        self.session_count: int = 0
        self.verification_timeline: List[Dict[str, Any]] = []
        self.session_history: List[SpeakerAuthenticationSession] = []

    def record_verification(
        self, verified: bool, confidence: float, time_ms: float, timestamp: str
    ):
        if verified:
            self.successful_verifications += 1
        else:
            self.rejected_verifications += 1

        total_verifications = (
            self.successful_verifications + self.rejected_verifications
        )
        self.average_confidence = (
            self.average_confidence
            + (confidence - self.average_confidence) / total_verifications
        )
        self.average_verification_time_ms = (
            self.average_verification_time_ms
            + (time_ms - self.average_verification_time_ms) / total_verifications
        )

        self.verification_timeline.append(
            {
                "timestamp": timestamp,
                "verified": verified,
                "confidence": confidence,
                "time_ms": time_ms,
            }
        )

    def record_enrollment(self):
        self.enrollment_count += 1
