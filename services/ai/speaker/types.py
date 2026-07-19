from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class SpeakerState(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    DISABLED = "DISABLED"
    ENROLLING = "ENROLLING"
    READY = "READY"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class SpeakerRole(str, Enum):
    OWNER = "OWNER"
    ADMINISTRATOR = "ADMINISTRATOR"
    FAMILY = "FAMILY"
    GUEST = "GUEST"
    UNKNOWN = "UNKNOWN"


class ConfidenceBand(str, Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    REJECTED = "REJECTED"


class SessionState(str, Enum):
    CREATED = "CREATED"
    WAITING_AUDIO = "WAITING_AUDIO"
    VERIFYING = "VERIFYING"
    AUTHENTICATED = "AUTHENTICATED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


@dataclass
class SpeakerEmbedding:
    embedding_id: str
    owner_id: str
    model_version: str
    provider: str
    vector: List[float]
    quality_score: float
    language: str
    microphone: str
    sample_rate: int
    created_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SpeakerProfile:
    profile_id: str
    display_name: str
    role: SpeakerRole
    embedding_references: List[str]
    preferred_language: str
    verification_threshold: float
    status: str
    verification_count: int
    profile_version: str
    embedding_version: str
    provider_version: str
    model_version: str
    migration_version: str
    enrollment_date: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_verification: Optional[datetime] = None


@dataclass
class SpeakerAuthenticationSession:
    session_id: str
    status: SessionState
    verification_attempts: int
    confidence_history: List[float]
    provider_used: str
    model_used: str
    expiration_time: datetime
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EnrollmentQualityMetrics:
    background_noise: float
    snr: float
    clipping: float
    speech_duration_ms: float
    speaking_rate: float
    sample_completeness: float


@dataclass
class SpeakerResult:
    verified: bool
    confidence_band: ConfidenceBand
    confidence_score: float
    threshold: float
    speaker_id: Optional[str]
    provider: str
    model_version: str
    inference_time_ms: float
    embedding_version: str
    session_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
