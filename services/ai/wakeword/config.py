from core.config.manager import ConfigManager
from services.ai.wakeword.types import WakeWordProfile


class WakeWordConfiguration:
    def __init__(self):
        self.profile = WakeWordProfile()
        self._load_from_config()

    def _load_from_config(self):
        wake_word = ConfigManager.get("ZEUS_WAKE_WORD", "Zeus")
        self.profile.wake_words = [wake_word]
        self.profile.sensitivity = float(
            ConfigManager.get("ZEUS_WAKE_WORD_SENSITIVITY", "0.5")
        )
        self.profile.threshold = float(
            ConfigManager.get("ZEUS_WAKE_WORD_THRESHOLD", "0.8")
        )
        self.profile.cooldown_seconds = float(
            ConfigManager.get("ZEUS_WAKE_WORD_COOLDOWN", "2.0")
        )
        self.profile.detection_window_ms = int(
            ConfigManager.get("ZEUS_WAKE_WORD_WINDOW_MS", "1500")
        )
        self.profile.maximum_rate_per_minute = int(
            ConfigManager.get("ZEUS_WAKE_WORD_MAX_RATE", "10")
        )

        self.chunk_size_ms = int(
            ConfigManager.get("ZEUS_WAKE_WORD_CHUNK_SIZE_MS", "200")
        )
        self.inference_interval_ms = int(
            ConfigManager.get("ZEUS_WAKE_WORD_INFERENCE_INTERVAL_MS", "200")
        )
        self.enable_logging = (
            ConfigManager.get("ZEUS_WAKE_WORD_LOGGING", "True").lower() == "true"
        )
