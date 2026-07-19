from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional

class ServiceState(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    BUSY = "BUSY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"

@dataclass
class RuntimeEvent:
    timestamp: float
    service: str
    event_type: str
    previous_state: str
    current_state: str
    details: Optional[Dict[str, Any]] = None
