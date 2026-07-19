import asyncio
import uuid
from typing import Any, Dict

import numpy as np

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from services.voice.audio.buffer import AudioBuffer
from services.voice.audio.capture import AudioCapture
from services.voice.audio.interfaces import IAudioProvider
from services.voice.audio.monitor import AudioLevelMonitor
from services.voice.audio.permissions import AudioPermissions
from services.voice.audio.provider import SoundDeviceProvider
from services.voice.audio.recorder import AudioRecorder
from services.voice.audio.session import AudioSession
from services.voice.audio.store import audio_store
from services.voice.audio.stream import AudioStream


class AudioManager(BaseService):
    def __init__(self):
        super().__init__(name="audio_manager", dependencies=[])
        self.buffer = AudioBuffer(retention_seconds=10)
        self.stream = AudioStream(self.buffer)

        self.capture = AudioCapture()
        self.recorder = AudioRecorder(self.capture)
        self.level_monitor = AudioLevelMonitor()

        self.provider: IAudioProvider = SoundDeviceProvider(self.capture)

        self.capture.add_callback(self.buffer.write)
        self.capture.add_callback(self._on_frames_for_monitor)

        self.current_session = None

    def _on_frames_for_monitor(self, frames) -> None:
        session_id = self.current_session.session_id if self.current_session else None
        dev = self.provider.get_current_device()
        dev_id = dev["id"] if dev else None
        self.level_monitor.process_frames_sync(frames, dev_id, session_id)
        # Update heartbeat since audio is flowing
        if self._state == self.state.READY or self._state == self.state.BUSY:
            asyncio.create_task(self.heartbeat())

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing Audio Manager...")
        self.level_monitor.set_loop(asyncio.get_running_loop())

        has_permission = AudioPermissions.check_permission()
        audio_store.update_state(
            {"permission_status": "GRANTED" if has_permission else "DENIED"}
        )

        await event_bus.publish(
            Event(type="AUDIO_INITIALIZED", payload={"permission": has_permission})
        )
        if not has_permission:
            raise RuntimeError("Audio permission denied")

    async def _do_start(self) -> None:
        self._logger.info("Starting Audio Manager...")
        self.provider.start_capture()

        dev = self.provider.get_current_device()
        dev_id = dev["id"] if dev else 0

        self.current_session = AudioSession(
            session_id=str(uuid.uuid4()),
            device_id=dev_id,
            sample_rate=self.buffer.sample_rate,
            channels=self.buffer.channels,
        )

        audio_store.update_state(
            {
                "recording": True,
                "current_device": dev_id,
                "active_session_id": self.current_session.session_id,
            }
        )

        await event_bus.publish(
            Event(
                type="AUDIO_STARTED",
                payload={"session_id": self.current_session.session_id},
            )
        )

    async def _do_stop(self) -> None:
        self._logger.info("Stopping Audio Manager...")
        self.provider.stop_capture()

        if self.current_session:
            from datetime import datetime, timezone

            self.current_session.end_time = datetime.now(timezone.utc)

        audio_store.update_state({"recording": False, "active_session_id": None})
        await event_bus.publish(
            Event(
                type="AUDIO_STOPPED",
                payload={
                    "session_id": (
                        self.current_session.session_id
                        if self.current_session
                        else None
                    )
                },
            )
        )
        self.current_session = None

    async def start_recording_session(self) -> None:
        await self.start()

    async def stop_recording_session(self) -> np.ndarray:
        if not self.current_session:
            return __import__("numpy").array([])

        session = self.current_session
        duration_sec = session.duration
        frames_to_read = int(self.buffer.sample_rate * duration_sec)
        frames = self.buffer.read(frames_to_read)

        await self.stop()
        return frames

    async def health(self) -> Dict[str, Any]:
        base_health = await super().health()
        dev = self.provider.get_current_device()
        
        diagnostics = self.capture.metrics.copy() if hasattr(self.capture, "metrics") else {}
        
        base_health.update({
            "recording": audio_store.recording,
            "device": dev["name"] if dev else "None",
            "permission": audio_store.permission_status,
            "diagnostics": diagnostics
        })
        return base_health
