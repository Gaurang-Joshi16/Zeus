from typing import Optional

import numpy as np

from services.voice.audio.buffer import AudioBuffer


class AudioStream:
    """
    Audio Stream abstraction that consumes from the AudioBuffer.
    Future modules (like Wake Word or Whisper) will use this instead of accessing the microphone directly.
    """

    def __init__(self, audio_buffer: AudioBuffer):
        self.buffer = audio_buffer

    def read_frames(self, num_frames: Optional[int] = None) -> np.ndarray:
        return self.buffer.read(num_frames)

    def write_frames(self, frames: np.ndarray) -> None:
        self.buffer.write(frames)
