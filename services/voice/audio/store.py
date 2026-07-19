from typing import Any, Dict, Optional


class AudioStore:
    def __init__(self):
        self.current_device: Optional[int] = None
        self.permission_status: str = "UNKNOWN"
        self.recording: bool = False
        self.muted: bool = False
        self.sample_rate: int = 48000
        self.current_rms: float = 0.0
        self.current_peak: float = 0.0
        self.is_silent: bool = True
        self.active_session_id: Optional[str] = None

    def update_state(self, updates: Dict[str, Any]) -> None:
        for k, v in updates.items():
            if getattr(self, k, None) != v:
                setattr(self, k, v)


audio_store = AudioStore()
