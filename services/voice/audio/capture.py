import asyncio
import time
from typing import Callable, List, Optional

import numpy as np
import sounddevice as sd

from core.logging.logger import CoreLogger


class AudioCapture:
    """
    Owns the microphone stream. Reads raw PCM frames and places them into an async queue
    for processing on the main event loop.
    """

    def __init__(self, sample_rate: int = 48000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream: Optional[sd.InputStream] = None
        self.callbacks: List[Callable[[np.ndarray], None]] = []
        self.device_id: Optional[int] = None
        self._logger = CoreLogger.get_logger("zeus.audio.capture")
        
        self.metrics = {
            "queue_depth": 0,
            "fps": 0.0,
            "dropped_frames": 0,
            "latency_ms": 0.0
        }
        self.frame_queue: Optional[asyncio.Queue] = None
        self._process_task: Optional[asyncio.Task] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._last_fps_time = time.time()
        self._frames_processed = 0

    def add_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        self.callbacks.append(callback)

    def start(self, device_id: Optional[int] = None) -> None:
        if self.stream is not None:
            self.stop()

        self.device_id = device_id
        
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self._logger.error("AudioCapture must be started from an active asyncio event loop.")
            raise
            
        self.frame_queue = asyncio.Queue(maxsize=100)
        self._process_task = self.loop.create_task(self._process_queue())
        self._last_fps_time = time.time()
        self._frames_processed = 0
        
        def try_put(data, ts):
            try:
                self.frame_queue.put_nowait((data, ts))
            except asyncio.QueueFull:
                self.metrics["dropped_frames"] += 1

        def _audio_callback(indata, frames, time_info, status):
            if status:
                self._logger.warning(f"Audio status: {status}")
            copied_data = indata.copy()
            ts = time.time()
            if self.loop and not self.loop.is_closed():
                self.loop.call_soon_threadsafe(try_put, copied_data, ts)

        try:
            self.stream = sd.InputStream(
                device=self.device_id,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=_audio_callback,
            )
            self.stream.start()
            self._logger.info("Audio capture started.")
        except Exception as e:
            self._logger.error(f"Failed to start audio capture: {e}")

    async def _process_queue(self):
        while True:
            try:
                data, ts = await self.frame_queue.get()
                self.metrics["queue_depth"] = self.frame_queue.qsize()
                
                # Execute callbacks
                for cb in self.callbacks:
                    try:
                        if asyncio.iscoroutinefunction(cb):
                            await cb(data)
                        else:
                            cb(data)
                    except Exception as e:
                        self._logger.error(f"Callback error: {e}")
                
                # Update metrics
                process_end = time.time()
                latency = (process_end - ts) * 1000
                self.metrics["latency_ms"] = round(latency, 2)
                
                self._frames_processed += 1
                now = time.time()
                if now - self._last_fps_time >= 1.0:
                    self.metrics["fps"] = round(self._frames_processed / (now - self._last_fps_time), 2)
                    self._frames_processed = 0
                    self._last_fps_time = now
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Queue processing error: {e}")

    def stop(self) -> None:
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        if self._process_task and not self._process_task.done():
            self._process_task.cancel()
            
        self._logger.info("Audio capture stopped.")
