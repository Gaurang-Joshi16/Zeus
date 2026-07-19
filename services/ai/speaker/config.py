from core.config.manager import ConfigManager


class SpeakerConfiguration:
    def __init__(self):
        self._load_from_config()

    def _load_from_config(self):
        self.verification_threshold = float(
            ConfigManager.get("ZEUS_SPEAKER_THRESHOLD", "0.75")
        )
        self.verification_window_ms = int(
            ConfigManager.get("ZEUS_SPEAKER_VERIFICATION_WINDOW_MS", "2000")
        )
        self.enrollment_samples = int(
            ConfigManager.get("ZEUS_SPEAKER_ENROLLMENT_SAMPLES", "5")
        )
        self.min_audio_length_ms = int(
            ConfigManager.get("ZEUS_SPEAKER_MIN_AUDIO_MS", "1500")
        )
        self.max_audio_length_ms = int(
            ConfigManager.get("ZEUS_SPEAKER_MAX_AUDIO_MS", "5000")
        )
        self.min_quality = float(ConfigManager.get("ZEUS_SPEAKER_MIN_QUALITY", "0.8"))
        self.embedding_size = int(
            ConfigManager.get("ZEUS_SPEAKER_EMBEDDING_SIZE", "192")
        )
        self.encryption_enabled = (
            ConfigManager.get("ZEUS_SPEAKER_ENCRYPTION", "True").lower() == "true"
        )
        self.auto_save = (
            ConfigManager.get("ZEUS_SPEAKER_AUTO_SAVE", "True").lower() == "true"
        )
        self.preferred_provider = ConfigManager.get(
            "ZEUS_AI_PREFERRED_SPEAKER", "ecapatdnn"
        )
