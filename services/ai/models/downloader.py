import asyncio
import os
from datetime import datetime, timezone
from typing import Dict

from core.config.manager import ConfigManager
from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from services.ai.models.interfaces import IModelProvider
from services.ai.models.metadata import ModelManifest, ModelMetadata
from services.ai.models.registry import ModelRegistry
from services.ai.models.storage import ModelStorage
from services.ai.models.storage_quota import StorageQuotaManager
from services.ai.models.types import DownloadState, ModelStatus
from services.ai.models.validator import ModelValidator


class DownloadTask:
    def __init__(self, manifest: ModelManifest):
        self.manifest = manifest
        self.state: DownloadState = DownloadState.QUEUED
        self.progress: float = 0.0
        self.error: str = ""
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None


class DownloadManager:
    def __init__(
        self,
        provider: IModelProvider,
        storage: ModelStorage,
        registry: ModelRegistry,
        validator: ModelValidator,
        quota: StorageQuotaManager,
    ):
        self._logger = CoreLogger.get_logger("zeus.models.downloader")
        self.provider = provider
        self.storage = storage
        self.registry = registry
        self.validator = validator
        self.quota = quota

        self.max_concurrent = int(
            ConfigManager.get("ZEUS_MODEL_MAX_CONCURRENT_DOWNLOADS", 2)
        )
        self.auto_validate = (
            ConfigManager.get("ZEUS_MODEL_AUTO_VALIDATE", "True").lower() == "true"
        )

        self.tasks: Dict[str, DownloadTask] = {}
        self.queue = asyncio.Queue()
        self.workers = []
        self._running = False

    async def start(self):
        self._running = True
        for _ in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker_loop())
            self.workers.append(worker)

    async def stop(self):
        self._running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)

    async def queue_download(self, manifest: ModelManifest):
        if manifest.id in self.tasks and self.tasks[manifest.id].state in [
            DownloadState.QUEUED,
            DownloadState.DOWNLOADING,
        ]:
            self._logger.warning(f"Download for {manifest.id} is already in progress.")
            return

        task = DownloadTask(manifest)
        self.tasks[manifest.id] = task
        await self._update_state(manifest.id, DownloadState.QUEUED)
        await self.queue.put(manifest.id)

    async def _update_state(
        self,
        model_id: str,
        state: DownloadState,
        progress: float = 0.0,
        error: str = "",
    ):
        if model_id not in self.tasks:
            return

        task = self.tasks[model_id]
        task.state = state
        task.progress = progress
        task.error = error

        event_name = f"MODEL_DOWNLOAD_{state.value}"
        await event_bus.publish(
            Event(
                type=event_name,
                payload={
                    "model_id": model_id,
                    "category": task.manifest.category.value,
                    "version": task.manifest.version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "progress": progress,
                    "status": state.value,
                    "error": error,
                },
            )
        )

    async def _worker_loop(self):
        while self._running:
            try:
                model_id = await self.queue.get()
                await self._process_download(model_id)
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Download worker error: {e}")

    async def _process_download(self, model_id: str):
        task = self.tasks.get(model_id)
        if not task:
            return

        manifest = task.manifest
        task.start_time = datetime.now(timezone.utc)

        estimated_size = 50 * 1024 * 1024
        if self.quota.check_insufficient_space(
            self.storage.get_base_path(), estimated_size
        ):
            await self._update_state(
                model_id, DownloadState.FAILED, error="Insufficient storage space"
            )
            return

        final_path = self.storage.get_model_path(
            manifest.category, f"{manifest.id}.bin"
        )
        temp_path = f"{final_path}.tmp"

        await self._update_state(model_id, DownloadState.CONNECTING)
        try:
            await self._update_state(model_id, DownloadState.DOWNLOADING)
            async for progress in self.provider.download_model(manifest, temp_path):
                await self._update_state(
                    model_id, DownloadState.DOWNLOADING, progress=progress
                )

            await self._update_state(model_id, DownloadState.VERIFYING, progress=1.0)
            if self.auto_validate:
                is_valid = self.validator.validate_model(manifest, temp_path)
                if not is_valid:
                    os.remove(temp_path)
                    await self._update_state(
                        model_id, DownloadState.FAILED, error="Validation failed"
                    )
                    return

            os.replace(temp_path, final_path)

            metadata = ModelMetadata(
                id=manifest.id,
                name=manifest.name,
                category=manifest.category,
                framework=manifest.framework,
                version=manifest.version,
                sha256=manifest.checksum,
                install_path=final_path,
                status=ModelStatus.READY,
                installed_date=datetime.now(timezone.utc),
            )
            self.registry.register_model(metadata)

            await self._update_state(model_id, DownloadState.COMPLETED, progress=1.0)
            await event_bus.publish(
                Event(
                    type="MODEL_REGISTERED",
                    payload={"model_id": manifest.id, "status": "READY"},
                )
            )

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            await self._update_state(model_id, DownloadState.FAILED, error=str(e))
