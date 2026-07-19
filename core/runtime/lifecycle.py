from enum import Enum

from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from core.logging.logger import CoreLogger


class AppState(Enum):
    BOOTING = "BOOTING"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    STOPPED = "STOPPED"


class LifecycleManager:
    def __init__(self):
        self._state = AppState.BOOTING
        self._logger = CoreLogger.get_logger("zeus.runtime.lifecycle")

    @property
    def state(self) -> AppState:
        return self._state

    async def transition_to(self, new_state: AppState) -> None:
        if self._state != new_state:
            self._logger.info(
                f"Lifecycle transition: {self._state.name} -> {new_state.name}"
            )
            self._state = new_state

            event_type_map = {
                AppState.BOOTING: None,
                AppState.INITIALIZING: None,
                AppState.READY: EventTypes.APP_READY,
                AppState.DEGRADED: None,
                AppState.SHUTTING_DOWN: EventTypes.APP_STOPPING,
                AppState.STOPPED: EventTypes.APP_STOPPED,
            }

            event_type = event_type_map.get(new_state)
            if event_type:
                await event_bus.publish(
                    Event(type=event_type, payload={"state": new_state.name})
                )


lifecycle_manager = LifecycleManager()
