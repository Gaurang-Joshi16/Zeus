from typing import Any, Dict, List

from core.config.manager import ConfigManager
from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from services.ai.models.cache import ModelCache
from services.ai.models.downloader import DownloadManager
from services.ai.models.loader import ModelLoader
from services.ai.models.metadata import ModelManifest, ModelMetadata
from services.ai.models.providers.local import LocalModelProvider
from services.ai.models.registry import ModelRegistry
from services.ai.models.storage import ModelStorage
from services.ai.models.storage_quota import StorageQuotaManager
from services.ai.models.validator import ModelValidator


class ModelManager(BaseService):
    def __init__(self):
        super().__init__(name="model_manager", dependencies=[])

        self.storage = ModelStorage()
        self.quota = StorageQuotaManager()
        self.registry = ModelRegistry(self.storage)
        self.validator = ModelValidator()
        self.provider = LocalModelProvider()

        self.downloader = DownloadManager(
            provider=self.provider,
            storage=self.storage,
            registry=self.registry,
            validator=self.validator,
            quota=self.quota,
        )

        max_cache = int(ConfigManager.get("ZEUS_MODEL_CACHE_SIZE", 10))
        self.cache = ModelCache(max_size=max_cache)
        self.loader = ModelLoader(registry=self.registry, cache=self.cache)

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing Model Manager...")
        
        # Seed default models for providers
        from services.ai.models.metadata import ModelMetadata
        from services.ai.models.types import ModelCategory, ModelFramework, ModelStatus

        default_models = [
            ("silerovad_model", ModelCategory.OTHER, ModelFramework.CUSTOM),
            ("openwakeword_model", ModelCategory.WAKE_WORD, ModelFramework.ONNX),
            ("speaker_model", ModelCategory.SPEAKER_VERIFICATION, ModelFramework.ONNX),
        ]
        
        for mid, cat, fw in default_models:
            if not self.registry.get_model(mid):
                self.registry.register_model(ModelMetadata(
                    id=mid,
                    name=mid,
                    category=cat,
                    framework=fw,
                    version="1.0.0",
                    sha256="",
                    install_path="dummy",
                    status=ModelStatus.READY
                ))
                
        await self.downloader.start()

    async def _do_start(self) -> None:
        self._logger.info("Started Model Manager.")

    async def _do_stop(self) -> None:
        self._logger.info("Stopping Model Manager...")
        await self.downloader.stop()

    async def health(self) -> Dict[str, Any]:
        base_health = await super().health()
        base_health.update({
            "models_installed": len(self.registry.get_all_models()),
            "downloads_active": len(
                [
                    t
                    for t in self.downloader.tasks.values()
                    if t.state.value
                    in ["QUEUED", "CONNECTING", "DOWNLOADING", "VERIFYING"]
                ]
            ),
        })
        return base_health

    def get_installed_models(self) -> List[ModelMetadata]:
        return self.registry.get_all_models()

    async def queue_download(self, manifest: ModelManifest) -> None:
        await self.downloader.queue_download(manifest)

    async def load_model(self, model_id: str) -> Any:
        runtime = await self.loader.load_model(model_id)
        return runtime.get_instance() if runtime else None

    async def release_model(self, model_id: str) -> None:
        await self.loader.unload_model(model_id)
