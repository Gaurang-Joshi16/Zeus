import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from core.logging.logger import CoreLogger

logger = CoreLogger.get_logger("zeus.ipc.adapter")


class IIPCAdapter(ABC):
    @abstractmethod
    def register_handler(self, command_name: str, handler: Callable[..., Any]) -> None:
        pass

    @abstractmethod
    async def emit_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        pass


class WebSocketIPCAdapter(IIPCAdapter):
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._connections: List[Any] = []

    def register_handler(self, command_name: str, handler: Callable[..., Any]) -> None:
        logger.info(f"Registering IPC handler: {command_name}")
        self._handlers[command_name] = handler

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.info(
            f"WebSocket client connected. Total connections: {len(self._connections)}"
        )

    def disconnect(self, websocket: Any) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
            logger.info(
                f"WebSocket client disconnected. Total connections: {len(self._connections)}"
            )

    async def emit_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        if not self._connections:
            return

        disconnected = []
        for connection in self._connections:
            try:
                await connection.send_json({"event": event_name, "payload": payload})
            except Exception as e:
                logger.error(f"Failed to send event {event_name} to client: {e}")
                disconnected.append(connection)

        for d in disconnected:
            self.disconnect(d)

    async def invoke(self, command_name: str, payload: Dict[str, Any]) -> Any:
        logger.info(f"[Backend] IPCAdapter receives command: {command_name}")
        if command_name in self._handlers:
            handler = self._handlers[command_name]
            logger.info(f"[Backend] Command router dispatches command: {command_name}")
            if asyncio.iscoroutinefunction(handler):
                return await handler(payload)
            return handler(payload)

        logger.error(f"[Backend] Unknown IPC command: {command_name}")
        logger.error("[Backend] IPC routing failure")
        return {"error": f"Unknown IPC command: {command_name}"}


ipc_adapter = WebSocketIPCAdapter()
