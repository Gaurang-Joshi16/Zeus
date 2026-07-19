from typing import Any, Callable, Dict, Type, TypeVar

from core.logging.logger import CoreLogger

T = TypeVar("T")


class DependencyContainer:
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._transients: Dict[Type, Callable[[], Any]] = {}
        self._logger = CoreLogger.get_logger("zeus.runtime.container")

    def register_singleton(self, interface: Type[T], instance: T) -> None:
        self._singletons[interface] = instance
        self._logger.debug(f"Registered singleton: {interface.__name__}")

    def register_transient(self, interface: Type[T], factory: Callable[[], T]) -> None:
        self._transients[interface] = factory
        self._logger.debug(f"Registered transient: {interface.__name__}")

    def resolve(self, interface: Type[T]) -> T:
        if interface in self._singletons:
            return self._singletons[interface]
        if interface in self._transients:
            return self._transients[interface]()
        raise KeyError(f"Type {interface.__name__} not registered in container.")


# Global Container
container = DependencyContainer()
