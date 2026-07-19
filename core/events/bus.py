import asyncio
from typing import Callable, Dict, List

from core.events.types import Event
from core.logging.logger import CoreLogger


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._logger = CoreLogger.get_logger("zeus.events.bus")

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self._logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                self._logger.debug(f"Unsubscribed from event: {event_type}")
            except ValueError:
                pass

    async def publish(self, event: Event) -> None:
        self._logger.info(f"Publishing event: {event.type}")

        # Forward to WebSocket IPC bridge
        from core.ipc.adapter import ipc_adapter

        asyncio.create_task(ipc_adapter.emit_event(event.type, event.payload))

        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    self._logger.error(f"Error handling event {event.type}: {e}")


# Global Event Bus Instance
event_bus = EventBus()
