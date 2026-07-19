from typing import List

from services.ai.vad.session import VADSession
from services.ai.vad.types import VoiceSegment


class VADStatistics:
    def __init__(self):
        self.speech_time_ms: float = 0.0
        self.silence_time_ms: float = 0.0
        self.speech_segments: List[VoiceSegment] = []

        self.average_confidence: float = 0.0
        self.dropped_frames: int = 0
        self.average_inference_time_ms: float = 0.0
        self.total_inferences: int = 0

        self.session_history: List[VADSession] = []

    def record_inference(self, confidence: float, inference_time_ms: float):
        self.total_inferences += 1
        self.average_confidence = (
            self.average_confidence
            + (confidence - self.average_confidence) / self.total_inferences
        )
        self.average_inference_time_ms = (
            self.average_inference_time_ms
            + (inference_time_ms - self.average_inference_time_ms)
            / self.total_inferences
        )

    def record_segment(self, segment: VoiceSegment):
        self.speech_segments.append(segment)
        self.speech_time_ms += segment.duration_ms

    def record_silence(self, duration_ms: float):
        self.silence_time_ms += duration_ms

    def record_dropped_frames(self, count: int):
        self.dropped_frames += count

    def record_session_end(self, session: VADSession):
        self.session_history.append(session)

    @property
    def average_segment_length_ms(self) -> float:
        if not self.speech_segments:
            return 0.0
        return sum(s.duration_ms for s in self.speech_segments) / len(
            self.speech_segments
        )
