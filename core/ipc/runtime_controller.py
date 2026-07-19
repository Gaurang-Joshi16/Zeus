import asyncio
from typing import Any, Dict

from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from core.ipc.adapter import ipc_adapter
from core.logging.logger import CoreLogger
from core.registry.registry import service_registry
from core.runtime.manager import runtime_manager


class RuntimeIPCController:
    def __init__(self):
        self._logger = CoreLogger.get_logger("zeus.ipc.runtime")

    async def initialize(self):
        # Register incoming command to manually fetch status if needed
        ipc_adapter.register_handler("GET_RUNTIME_STATUS", self.get_runtime_status)
        ipc_adapter.register_handler("GET_APP_STATE", self.get_app_state)

        # Subscribe to runtime events to forward them
        event_bus.subscribe(EventTypes.SERVICE_INITIALIZING, self._forward_event)
        event_bus.subscribe(EventTypes.SERVICE_READY, self._forward_event)
        event_bus.subscribe(EventTypes.SERVICE_BUSY, self._forward_event)
        event_bus.subscribe(EventTypes.SERVICE_DEGRADED, self._forward_event)
        event_bus.subscribe(EventTypes.SERVICE_FAILED, self._forward_event)
        event_bus.subscribe(EventTypes.SERVICE_STOPPED, self._forward_event)
        event_bus.subscribe(EventTypes.SERVICE_RECOVERING, self._forward_event)
        event_bus.subscribe(EventTypes.SERVICE_RECOVERED, self._forward_event)

    async def get_app_state(self, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        from core.setup.state_machine import setup_state_machine
        from core.conversation.manager import conversation_manager
        
        runtime_status = await self.get_runtime_status()
        active_conv = None
        
        if conversation_manager.active_conversation:
            active_conv = {
                "id": conversation_manager.active_conversation.id,
                "state": conversation_manager.active_conversation.state.value,
                "start_time": conversation_manager.active_conversation.start_time,
                "speaker_id": conversation_manager.active_conversation.speaker_id,
                "response": conversation_manager.active_conversation.response,
                "transcript": conversation_manager.active_conversation.metadata.get("final_transcript", "")
            }

        return {
            "setupState": setup_state_machine.current_state.value,
            "runtimeStatus": runtime_status,
            "activeConversation": active_conv
        }

    async def get_runtime_status(self, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        report = {}
        for name, service in service_registry._services.items():
            report[name] = await service.health()
        
        events = [
            {
                "timestamp": e.timestamp,
                "service": e.service,
                "eventType": e.event_type,
                "previousState": e.previous_state,
                "currentState": e.current_state,
                "details": e.details
            }
            for e in runtime_manager._event_history
        ]

        return {
            "services": report,
            "events": events
        }

    async def _forward_event(self, event: Event):
        # When a service changes state, forward a RUNTIME_UPDATE to frontend
        # Including the full health report to ensure the frontend is perfectly synced
        try:
            status = await self.get_runtime_status({})
            await ipc_adapter.emit_event("RUNTIME_UPDATE", status)
        except Exception as e:
            self._logger.error(f"Failed to forward runtime event: {e}")

runtime_ipc_controller = RuntimeIPCController()
