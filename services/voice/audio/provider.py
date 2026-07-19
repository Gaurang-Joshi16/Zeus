from typing import Any, Dict, List, Optional

from services.voice.audio.capture import AudioCapture
from services.voice.audio.device import AudioDeviceManager
from services.voice.audio.interfaces import IAudioProvider


class SoundDeviceProvider(IAudioProvider):
    def __init__(self, capture: AudioCapture):
        self.capture = capture
        self.current_device_id: Optional[int] = None

    def start_capture(self) -> None:
        if self.current_device_id is None:
            self.current_device_id = AudioDeviceManager.get_default_device_id()
        self.capture.start(self.current_device_id)

    def stop_capture(self) -> None:
        self.capture.stop()

    def get_current_device(self) -> Optional[Dict[str, Any]]:
        devices = self.get_available_devices()
        if self.current_device_id is not None:
            for d in devices:
                if d["id"] == self.current_device_id:
                    return d
        return None

    def set_device(self, device_id: int) -> None:
        self.current_device_id = device_id
        if self.capture.stream is not None:
            # Restart if running
            self.stop_capture()
            self.start_capture()

    def get_available_devices(self) -> List[Dict[str, Any]]:
        return AudioDeviceManager.get_input_devices()
