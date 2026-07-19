from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class AIContext:
    session_id: str
    user_id: str
    language: str = "en"
    current_model: Optional[str] = None
    audio_session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    memory_reference_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
