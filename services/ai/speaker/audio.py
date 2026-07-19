import numpy as np

from services.voice.audio.stream import AudioStream


class VerificationAudioProvider:
    def __init__(self, stream: AudioStream):
        self.stream = stream

    def get_audio_window(self, window_ms: int) -> np.ndarray:
        sample_rate = self.stream.buffer.sample_rate
        frames_to_read = int(sample_rate * (window_ms / 1000.0))
        frames = self.stream.read_frames(frames_to_read)
        return frames
