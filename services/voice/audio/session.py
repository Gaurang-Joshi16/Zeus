from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AudioSession:
    session_id: str
    device_id: int
    sample_rate: int
    channels: int
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()
