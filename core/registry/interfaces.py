from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from core.runtime.types import ServiceState

class IService(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def state(self) -> ServiceState:
        pass

    @property
    @abstractmethod
    def critical(self) -> bool:
        pass

    @property
    @abstractmethod
    def uptime(self) -> float:
        pass

    @property
    @abstractmethod
    def last_heartbeat(self) -> Optional[float]:
        pass

    @property
    @abstractmethod
    def startup_duration(self) -> Optional[float]:
        pass

    @property
    @abstractmethod
    def recovery_count(self) -> int:
        pass

    @property
    @abstractmethod
    def last_error(self) -> Optional[str]:
        pass

    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        pass
