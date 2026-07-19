from typing import Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AIRequestContext:
    conversationId: str
    timestamp: datetime
    transcript: str
    provider: str
    model: str
    sessionId: str
    speakerId: Optional[str] = None
