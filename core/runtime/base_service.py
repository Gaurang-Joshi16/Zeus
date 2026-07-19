import time
from typing import Any, Dict, List, Optional

from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from core.logging.logger import CoreLogger
from core.registry.interfaces import IService
from core.runtime.types import ServiceState

class BaseService(IService):
    def __init__(self, name: str, dependencies: List[str] = None, critical: bool = True):
        self._name = name
        self._dependencies = dependencies or []
        self._critical = critical
        self._state = ServiceState.UNINITIALIZED
        self._start_time: Optional[float] = None
        self._last_heartbeat: Optional[float] = None
        self._startup_duration: Optional[float] = None
        self._recovery_count = 0
        self._last_error: Optional[str] = None
        self._logger = CoreLogger.get_logger(f"zeus.service.{name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List[str]:
        return self._dependencies

    @property
    def state(self) -> ServiceState:
        return self._state

    @property
    def critical(self) -> bool:
        return self._critical

    @property
    def uptime(self) -> float:
        if self._state in (ServiceState.UNINITIALIZED, ServiceState.INITIALIZING, ServiceState.STOPPED):
            return 0.0
        return time.time() - (self._start_time or time.time())

    @property
    def last_heartbeat(self) -> Optional[float]:
        return self._last_heartbeat

    @property
    def startup_duration(self) -> Optional[float]:
        return self._startup_duration

    @property
    def recovery_count(self) -> int:
        return self._recovery_count

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    async def _transition_state(self, new_state: ServiceState, details: Optional[Dict[str, Any]] = None):
        if self._state == new_state:
            return

        previous_state = self._state
        self._state = new_state

        event_map = {
            ServiceState.INITIALIZING: EventTypes.SERVICE_INITIALIZING,
            ServiceState.READY: EventTypes.SERVICE_READY,
            ServiceState.BUSY: EventTypes.SERVICE_BUSY,
            ServiceState.DEGRADED: EventTypes.SERVICE_DEGRADED,
            ServiceState.FAILED: EventTypes.SERVICE_FAILED,
            ServiceState.STOPPED: EventTypes.SERVICE_STOPPED,
        }
        
        event_type = event_map.get(new_state)
        if event_type:
            payload = {
                "serviceName": self.name,
                "previousState": previous_state.value,
                "currentState": new_state.value,
                "details": details or {}
            }
            if new_state == ServiceState.FAILED:
                self._last_error = details.get("error", "Unknown error") if details else "Unknown error"
            
            await event_bus.publish(Event(type=event_type, payload=payload))

    async def heartbeat(self) -> None:
        self._last_heartbeat = time.time()

    async def initialize(self) -> None:
        start_time = time.time()
        await self._transition_state(ServiceState.INITIALIZING)
        try:
            await self._do_initialize()
        except Exception as e:
            self._logger.error(f"Failed to initialize {self.name}: {e}", exc_info=True)
            await self._transition_state(ServiceState.FAILED, {"error": str(e)})
            raise
        self._startup_duration = time.time() - start_time

    async def _do_initialize(self) -> None:
        pass

    async def start(self) -> None:
        self._start_time = time.time()
        await self._transition_state(ServiceState.READY)
        try:
            await self._do_start()
        except Exception as e:
            self._logger.error(f"Failed to start {self.name}: {e}", exc_info=True)
            await self._transition_state(ServiceState.FAILED, {"error": str(e)})
            raise

    async def _do_start(self) -> None:
        pass

    async def stop(self) -> None:
        try:
            await self._do_stop()
        except Exception as e:
            self._logger.error(f"Error while stopping {self.name}: {e}", exc_info=True)
        finally:
            await self._transition_state(ServiceState.STOPPED)
            self._start_time = None

    async def _do_stop(self) -> None:
        pass

    async def health(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.state.value,
            "uptime": self.uptime,
            "lastHeartbeat": self.last_heartbeat,
            "lastError": self.last_error,
            "dependencies": self.dependencies,
            "startupDuration": self.startup_duration,
            "recoveryCount": self.recovery_count,
            "critical": self.critical
        }
