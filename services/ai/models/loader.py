import asyncio
from typing import Optional

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from services.ai.models.cache import ModelCache
from services.ai.models.registry import ModelRegistry
from services.ai.models.runtime import ModelRuntime


class ModelLoader:
    def __init__(self, registry: ModelRegistry, cache: ModelCache):
        self._logger = CoreLogger.get_logger("zeus.models.loader")
        self.registry = registry
        self.cache = cache

    async def load_model(self, model_id: str) -> Optional[ModelRuntime]:
        runtime = self.cache.get(model_id)
        if runtime:
            runtime.reference_count += 1
            return runtime

        metadata = self.registry.get_model(model_id)
        if not metadata:
            self._logger.error(f"Cannot load {model_id}: Not found in registry.")
            return None

        self._logger.info(f"Loading model {model_id}...")

        await asyncio.sleep(0.5)

        dummy_instance = object()
        runtime = ModelRuntime(metadata, dummy_instance)
        runtime.reference_count += 1

        self.cache.put(model_id, runtime)

        await event_bus.publish(
            Event(
                type="MODEL_LOADED",
                payload={"model_id": model_id, "category": metadata.category.value},
            )
        )

        return runtime

    async def unload_model(self, model_id: str) -> None:
        runtime = self.cache.get(model_id)
        if runtime:
            runtime.reference_count = max(0, runtime.reference_count - 1)
            if runtime.reference_count == 0:
                self.cache.remove(model_id)
                await event_bus.publish(
                    Event(type="MODEL_UNLOADED", payload={"model_id": model_id})
                )
