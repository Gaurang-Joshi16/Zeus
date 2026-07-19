from typing import Any, Dict

from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from core.logging.logger import CoreLogger
from core.registry.interfaces import IService
from core.runtime.container import container


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, IService] = {}
        self._logger = CoreLogger.get_logger("zeus.registry.services")

    def register(self, name: str, service: IService) -> None:
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered.")

        self._services[name] = service
        container.register_singleton(type(service), service)
        self._logger.info(f"Registered service: {name}")

    async def initialize_all(self) -> None:
        for name, service in self._services.items():
            self._logger.debug(f"Initializing service: {name}")
            await service.initialize()
            await event_bus.publish(
                Event(type=EventTypes.SERVICE_REGISTERED, payload={"service": name})
            )

    async def start_all(self) -> None:
        for name, service in self._services.items():
            self._logger.debug(f"Starting service: {name}")
            await service.start()
            await event_bus.publish(
                Event(type=EventTypes.SERVICE_STARTED, payload={"service": name})
            )

    async def stop_all(self) -> None:
        for name, service in self._services.items():
            self._logger.debug(f"Stopping service: {name}")
            await service.stop()
            await event_bus.publish(
                Event(type=EventTypes.SERVICE_STOPPED, payload={"service": name})
            )

    async def health_report(self) -> Dict[str, Any]:
        report = {}
        for name, service in self._services.items():
            try:
                report[name] = await service.health()
            except Exception as e:
                report[name] = {"status": "error", "error": str(e)}
        return report


service_registry = ServiceRegistry()
