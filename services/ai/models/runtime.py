from typing import Any

from services.ai.models.metadata import ModelMetadata


class ModelRuntime:
    """
    Wraps the actual loaded model instance. Future frameworks will extend this.
    """

    def __init__(self, metadata: ModelMetadata, instance: Any):
        self.metadata = metadata
        self.instance = instance
        self.reference_count = 0

    def get_instance(self) -> Any:
        return self.instance
