from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IAudioProvider(ABC):
    @abstractmethod
    def start_capture(self) -> None:
        pass

    @abstractmethod
    def stop_capture(self) -> None:
        pass

    @abstractmethod
    def get_current_device(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def set_device(self, device_id: int) -> None:
        pass

    @abstractmethod
    def get_available_devices(self) -> list[Dict[str, Any]]:
        pass
