import threading
from typing import Optional

import numpy as np


class AudioBuffer:
    def __init__(
        self, sample_rate: int = 48000, channels: int = 1, retention_seconds: int = 10
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.retention_seconds = retention_seconds

        self.capacity = self.sample_rate * self.retention_seconds
        self.buffer = np.zeros((self.capacity, self.channels), dtype=np.float32)

        self.write_index = 0
        self.is_full = False
        self.lock = threading.Lock()

    def write(self, frames: np.ndarray) -> None:
        with self.lock:
            length = len(frames)
            if length >= self.capacity:
                self.buffer[:] = frames[-self.capacity :]
                self.write_index = 0
                self.is_full = True
                return

            end_idx = self.write_index + length
            if end_idx <= self.capacity:
                self.buffer[self.write_index : end_idx] = frames
            else:
                overflow = end_idx - self.capacity
                self.buffer[self.write_index :] = frames[:-overflow]
                self.buffer[:overflow] = frames[-overflow:]
                self.is_full = True

            self.write_index = (self.write_index + length) % self.capacity

    def read(self, num_frames: Optional[int] = None) -> np.ndarray:
        with self.lock:
            if not self.is_full and self.write_index == 0:
                return np.zeros((0, self.channels), dtype=np.float32)

            available = self.capacity if self.is_full else self.write_index
            if num_frames is None or num_frames > available:
                num_frames = available

            start_idx = (self.write_index - num_frames) % self.capacity

            if start_idx < self.write_index:
                return self.buffer[start_idx : self.write_index].copy()
            else:
                part1 = self.buffer[start_idx:]
                part2 = self.buffer[: self.write_index]
                return np.concatenate((part1, part2))

    def clear(self) -> None:
        with self.lock:
            self.buffer.fill(0)
            self.write_index = 0
            self.is_full = False
