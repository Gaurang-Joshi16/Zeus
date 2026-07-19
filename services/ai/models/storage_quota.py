import shutil

from core.logging.logger import CoreLogger


class StorageQuotaManager:
    def __init__(self):
        self._logger = CoreLogger.get_logger("zeus.models.quota")

    def get_total_storage(self, path: str) -> int:
        """Returns total disk size in bytes."""
        try:
            total, _, _ = shutil.disk_usage(path)
            return total
        except Exception as e:
            self._logger.error(f"Failed to get total storage: {e}")
            return 0

    def get_available_storage(self, path: str) -> int:
        """Returns available disk size in bytes."""
        try:
            _, _, free = shutil.disk_usage(path)
            return free
        except Exception as e:
            self._logger.error(f"Failed to get available storage: {e}")
            return 0

    def check_insufficient_space(self, path: str, estimated_size: int) -> bool:
        """Warns and returns True if insufficient disk space."""
        available = self.get_available_storage(path)
        if available < estimated_size:
            self._logger.warning(
                f"Insufficient disk space. Required: {estimated_size}, Available: {available}"
            )
            return True
        return False
