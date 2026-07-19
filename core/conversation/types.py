from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ConversationState(str, Enum):
    IDLE = "IDLE"
    WAKE_WORD_DETECTED = "WAKE_WORD_DETECTED"
    VERIFYING_SPEAKER = "VERIFYING_SPEAKER"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    THINKING = "THINKING"
    GENERATING_RESPONSE = "GENERATING_RESPONSE"
    SPEAKING = "SPEAKING"
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class Conversation(BaseModel):
    id: str = Field(..., description="Unique UUID for this conversation")
    state: ConversationState = Field(default=ConversationState.IDLE)
    start_time: float = Field(..., description="Timestamp when the conversation started")
    end_time: Optional[float] = None
    speaker_id: Optional[str] = None
    response: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
