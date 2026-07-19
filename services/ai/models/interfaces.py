from abc import ABC, abstractmethod
from typing import AsyncGenerator

from services.ai.models.metadata import ModelManifest


class IModelProvider(ABC):
    @abstractmethod
    async def get_model_manifest(self, model_id: str) -> ModelManifest:
        """Fetch the manifest for a model"""
        pass

    @abstractmethod
    async def download_model(
        self, manifest: ModelManifest, dest_path: str
    ) -> AsyncGenerator[float, None]:
        """Downloads the model and yields progress percentage (0.0 to 1.0)"""
        pass
