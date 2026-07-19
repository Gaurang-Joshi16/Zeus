import asyncio
from typing import AsyncGenerator

from services.ai.models.interfaces import IModelProvider
from services.ai.models.metadata import ModelManifest


class LocalModelProvider(IModelProvider):
    """
    Simulates finding and downloading a local model for the placeholder requirement.
    """

    async def get_model_manifest(self, model_id: str) -> ModelManifest:
        from services.ai.models.types import ModelCategory, ModelFramework

        return ModelManifest(
            id=model_id,
            name=f"Simulated {model_id}",
            version="1.0.0",
            checksum="fake_checksum_83294238",
            framework=ModelFramework.CUSTOM,
            category=ModelCategory.OTHER,
            entry_file="model.bin",
            download_url="local://simulate",
        )

    async def download_model(
        self, manifest: ModelManifest, dest_path: str
    ) -> AsyncGenerator[float, None]:
        """Simulates a download and writes a dummy file"""
        total_steps = 10
        for i in range(total_steps):
            await asyncio.sleep(0.2)  # Simulate network IO
            yield (i + 1) / total_steps

        with open(dest_path, "w") as f:
            f.write("SIMULATED_MODEL_CONTENT")
