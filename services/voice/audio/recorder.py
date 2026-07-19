import numpy as np

from core.logging.logger import CoreLogger
from services.voice.audio.capture import AudioCapture


class AudioRecorder:
    """
    Optional recording component that consumes AudioCapture.
    Future responsibilities include saving to files (WAV/FLAC).
    """

    def __init__(self, capture: AudioCapture):
        self.capture = capture
        self.capture.add_callback(self.on_frames)
        self._logger = CoreLogger.get_logger("zeus.audio.recorder")
        self.is_recording = False

    def on_frames(self, frames: np.ndarray) -> None:
        if self.is_recording:
            # Future: write frames to file buffer
            pass

    def start_recording(self, filepath: str) -> None:
        self.is_recording = True
        self._logger.info(f"Started recording to {filepath}")

    def stop_recording(self) -> None:
        self.is_recording = False
        self._logger.info("Stopped recording")
