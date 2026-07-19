from core.config.manager import ConfigManager


class VADConfiguration:
    def __init__(self):
        self._load_from_config()

    def _load_from_config(self):
        self.energy_threshold = float(
            ConfigManager.get("ZEUS_VAD_ENERGY_THRESHOLD", "0.01")
        )
        self.min_speech_duration_ms = int(
            ConfigManager.get("ZEUS_VAD_MIN_SPEECH_DUR_MS", "250")
        )
        self.min_silence_duration_ms = int(
            ConfigManager.get("ZEUS_VAD_MIN_SILENCE_DUR_MS", "1000")
        )
        self.chunk_size_ms = int(ConfigManager.get("ZEUS_VAD_CHUNK_SIZE_MS", "30"))
        self.inference_interval_ms = int(
            ConfigManager.get("ZEUS_VAD_INFERENCE_INTERVAL_MS", "30")
        )
        self.noise_floor = float(ConfigManager.get("ZEUS_VAD_NOISE_FLOOR", "0.001"))
        self.adaptive_threshold = (
            ConfigManager.get("ZEUS_VAD_ADAPTIVE_THRESHOLD", "True").lower() == "true"
        )
        self.maximum_segment_length_ms = int(
            ConfigManager.get("ZEUS_VAD_MAX_SEGMENT_LENGTH_MS", "30000")
        )
