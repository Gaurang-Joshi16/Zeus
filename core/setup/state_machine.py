from enum import Enum

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger


class SetupState(str, Enum):
    UNKNOWN = "UNKNOWN"
    CHECKING = "CHECKING"
    OWNER_NOT_FOUND = "OWNER_NOT_FOUND"
    MIC_CHECK = "MIC_CHECK"
    ENROLLMENT = "ENROLLMENT"
    VERIFYING = "VERIFYING"
    READY = "READY"
    FAILED = "FAILED"


class SetupStateMachine:
    def __init__(self):
        self._state = SetupState.UNKNOWN
        self._logger = CoreLogger.get_logger("zeus.setup")

    @property
    def current_state(self) -> SetupState:
        return self._state

    async def transition_to(self, new_state: SetupState, payload: dict = None) -> None:
        self._logger.info(
            f"Setup transitioning: {self._state.value} -> {new_state.value}"
        )
        self._state = new_state
        await event_bus.publish(Event(type=new_state.value, payload=payload or {}))


setup_state_machine = SetupStateMachine()
