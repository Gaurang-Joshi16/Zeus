import os

from core.config.manager import ConfigManager
from services.ai.models.types import ModelCategory


class ModelStorage:
    def __init__(self):
        self.base_path = ConfigManager.get(
            "ZEUS_MODEL_STORAGE_PATH", os.path.join(os.getcwd(), "models")
        )
        self._ensure_directory(self.base_path)

    def _ensure_directory(self, path: str) -> None:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    def get_category_path(self, category: ModelCategory) -> str:
        """Returns the safe, absolute path for a specific model category."""
        category_dir = os.path.join(self.base_path, category.value.lower())
        self._ensure_directory(category_dir)
        return category_dir

    def get_model_path(self, category: ModelCategory, model_id: str) -> str:
        """Returns the specific path for a model, preventing path traversal."""
        safe_id = os.path.basename(model_id)  # Prevent traversal
        return os.path.join(self.get_category_path(category), safe_id)

    def get_base_path(self) -> str:
        return self.base_path
