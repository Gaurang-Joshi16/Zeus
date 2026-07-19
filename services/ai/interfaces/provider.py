from abc import ABC, abstractmethod
from typing import Any, Dict, TypeVar

from services.ai.models.manager import ModelManager
from services.ai.types.enums import AIEngineType, ProviderLifecycleState
from services.ai.types.profile import (
    CapabilityDescriptor,
    ProviderCompatibility,
    ProviderProfile,
)

T = TypeVar("T")


class IAIProvider(ABC):
    @abstractmethod
    def __init__(self, model_manager: ModelManager):
        pass

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider (e.g., 'whisper_local')"""
        pass

    @property
    @abstractmethod
    def engine_type(self) -> AIEngineType:
        """The capability this provider fulfills"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def load_model(self, model_id: str) -> None:
        pass

    @abstractmethod
    async def unload_model(self, model_id: str) -> None:
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def status(self) -> ProviderLifecycleState:
        pass

    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def capabilities(self) -> CapabilityDescriptor:
        pass

    @abstractmethod
    def profile(self) -> ProviderProfile:
        pass

    @abstractmethod
    def compatibility(self) -> ProviderCompatibility:
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        pass

    @abstractmethod
    def get_engine(self) -> Any:
        """Returns the specific Engine interface implementation"""
        pass
