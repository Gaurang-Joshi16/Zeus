import asyncio
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from core.events.bus import event_bus
from core.events.types import Event


class AudioLevelMonitor:
    def __init__(self, silence_threshold: float = 0.01):
        self.silence_threshold = silence_threshold
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    def process_frames_sync(
        self, frames: np.ndarray, device_id: Optional[int], session_id: Optional[str]
    ) -> None:
        if len(frames) == 0:
            return

        rms = float(np.sqrt(np.mean(np.square(frames))))
        peak = float(np.max(np.abs(frames)))
        is_silent = rms < self.silence_threshold

        event = Event(
            type="LEVEL_CHANGED",
            payload={
                "rms": rms,
                "peak": peak,
                "is_silent": is_silent,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "device_id": device_id,
                "session_id": session_id,
            },
        )

        if self.loop and not self.loop.is_closed():
            try:
                asyncio.run_coroutine_threadsafe(event_bus.publish(event), self.loop)
            except RuntimeError:
                pass
