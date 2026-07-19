import collections
from typing import Optional

from core.logging.logger import CoreLogger
from services.ai.models.runtime import ModelRuntime


class ModelCache:
    def __init__(self, max_size: int = 10):
        self._logger = CoreLogger.get_logger("zeus.models.cache")
        self.max_size = max_size
        self._cache: collections.OrderedDict[str, ModelRuntime] = (
            collections.OrderedDict()
        )

    def get(self, model_id: str) -> Optional[ModelRuntime]:
        if model_id in self._cache:
            self._cache.move_to_end(model_id)
            return self._cache[model_id]
        return None

    def put(self, model_id: str, runtime: ModelRuntime) -> None:
        if model_id in self._cache:
            self._cache.move_to_end(model_id)
        self._cache[model_id] = runtime
        self._logger.debug(f"Added {model_id} to cache.")
        if len(self._cache) > self.max_size:
            self.evict()

    def evict(self) -> None:
        for key in list(self._cache.keys()):
            runtime = self._cache[key]
            if runtime.reference_count <= 0:
                del self._cache[key]
                self._logger.info(f"Evicted model {key} from cache.")
                return
        self._logger.warning("Cache is full but no unreferenced models to evict!")

    def remove(self, model_id: str) -> None:
        if model_id in self._cache:
            del self._cache[model_id]
            self._logger.info(f"Removed {model_id} from cache.")
