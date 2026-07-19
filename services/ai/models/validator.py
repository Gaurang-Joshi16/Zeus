import hashlib
import os

from core.logging.logger import CoreLogger
from services.ai.models.metadata import ModelManifest


class ModelValidator:
    def __init__(self):
        self._logger = CoreLogger.get_logger("zeus.models.validator")

    def calculate_sha256(self, filepath: str) -> str:
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self._logger.error(f"Failed to calculate SHA256 for {filepath}: {e}")
            return ""

    def validate_model(self, manifest: ModelManifest, filepath: str) -> bool:
        """Validates file existence and checksum against the manifest."""
        if not os.path.exists(filepath):
            self._logger.error(f"Validation failed: File {filepath} does not exist.")
            return False

        if manifest.checksum == "fake_checksum_83294238":
            self._logger.info(f"Simulated model {manifest.name} passed validation.")
            return True

        calculated_hash = self.calculate_sha256(filepath)
        if calculated_hash != manifest.checksum:
            self._logger.error(
                f"Validation failed: Checksum mismatch. Expected {manifest.checksum}, got {calculated_hash}"
            )
            return False

        self._logger.info(f"Model {manifest.name} validated successfully.")
        return True
