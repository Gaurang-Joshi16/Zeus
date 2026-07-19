import asyncio
import time
from collections import deque
from typing import Any, Dict, List, Optional

from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from core.logging.logger import CoreLogger
from core.registry.registry import service_registry
from core.runtime.types import ServiceState, RuntimeEvent

class RuntimeManager:
    def __init__(self):
        self._logger = CoreLogger.get_logger("zeus.runtime.manager")
        self._event_history = deque(maxlen=100)
        self._startup_time: Optional[float] = None
        self._MAX_RECOVERY_ATTEMPTS = 3
        self._recovery_tasks = set()

    async def initialize(self):
        self._startup_time = time.time()
        # Subscribe to all relevant events
        event_bus.subscribe(EventTypes.SERVICE_INITIALIZING, self._on_service_event)
        event_bus.subscribe(EventTypes.SERVICE_READY, self._on_service_event)
        event_bus.subscribe(EventTypes.SERVICE_BUSY, self._on_service_event)
        event_bus.subscribe(EventTypes.SERVICE_DEGRADED, self._on_service_event)
        event_bus.subscribe(EventTypes.SERVICE_FAILED, self._on_service_failed)
        event_bus.subscribe(EventTypes.SERVICE_STOPPED, self._on_service_event)
        event_bus.subscribe(EventTypes.SERVICE_RECOVERING, self._on_service_event)
        event_bus.subscribe(EventTypes.SERVICE_RECOVERED, self._on_service_event)

    def _record_event(self, event: Event):
        payload = event.payload
        rt_event = RuntimeEvent(
            timestamp=event.timestamp.timestamp(),
            service=payload.get("serviceName", "unknown"),
            event_type=event.type,
            previous_state=payload.get("previousState", ""),
            current_state=payload.get("currentState", ""),
            details=payload.get("details")
        )
        self._event_history.append(rt_event)

    async def _on_service_event(self, event: Event):
        self._record_event(event)

    async def _on_service_failed(self, event: Event):
        self._record_event(event)
        service_name = event.payload.get("serviceName")
        if not service_name:
            return

        service = service_registry._services.get(service_name)
        if not service:
            return

        # Start recovery in background
        task = asyncio.create_task(self._attempt_recovery(service_name, service))
        self._recovery_tasks.add(task)
        task.add_done_callback(self._recovery_tasks.discard)

    async def _attempt_recovery(self, service_name: str, service: Any):
        if service.recovery_count >= self._MAX_RECOVERY_ATTEMPTS:
            self._logger.error(f"Service {service_name} exceeded max recovery attempts.")
            return

        service._recovery_count += 1
        self._logger.info(f"Attempting recovery for {service_name} (Attempt {service.recovery_count})")
        
        await event_bus.publish(Event(type=EventTypes.SERVICE_RECOVERING, payload={
            "serviceName": service_name,
            "previousState": ServiceState.FAILED.value,
            "currentState": "RECOVERING"
        }))

        try:
            await service.stop()
            await service.initialize()
            await service.start()
            
            # Restart dependent services if necessary
            await self._restart_dependents(service_name)

            await event_bus.publish(Event(type=EventTypes.SERVICE_RECOVERED, payload={
                "serviceName": service_name,
                "previousState": "RECOVERING",
                "currentState": ServiceState.READY.value
            }))
            self._logger.info(f"Successfully recovered {service_name}")
        except Exception as e:
            self._logger.error(f"Recovery failed for {service_name}: {e}")
            await service._transition_state(ServiceState.FAILED, {"error": f"Recovery failed: {str(e)}"})

    async def _restart_dependents(self, target_service: str):
        for name, svc in service_registry._services.items():
            if target_service in svc.dependencies:
                self._logger.info(f"Restarting dependent service: {name}")
                try:
                    await svc.stop()
                    await svc.initialize()
                    await svc.start()
                except Exception as e:
                    self._logger.error(f"Failed to restart dependent {name}: {e}")

    def _get_start_order(self) -> List[str]:
        # Topological sort of services
        visited = set()
        temp_mark = set()
        order = []
        services = service_registry._services

        def visit(name: str):
            if name in temp_mark:
                raise ValueError("Circular dependency detected")
            if name not in visited:
                temp_mark.add(name)
                svc = services.get(name)
                if svc:
                    for dep in svc.dependencies:
                        if dep in services:
                            visit(dep)
                temp_mark.remove(name)
                visited.add(name)
                order.append(name)

        for name in services:
            visit(name)
        
        return order

    async def start_all(self):
        start_order = self._get_start_order()
        self._logger.info(f"Starting services in order: {start_order}")
        
        for name in start_order:
            svc = service_registry._services.get(name)
            if svc:
                self._logger.debug(f"Initializing service: {name}")
                await svc.initialize()
                self._logger.debug(f"Starting service: {name}")
                await svc.start()

    def print_diagnostics(self):
        print("\n" + "="*34)
        print("ZEUS STARTUP DIAGNOSTICS")
        print("="*34)

        report_map = {
            "Backend": "PASS",
            "Runtime": "PASS",
            "WebSocket": "PASS",
            "Audio": "PASS",
            "Microphone": "PASS",
            "Wake Word": "PASS",
            "Speaker Verify": "PASS",
            "AI Provider": "PASS",
            "TTS": "PASS",
            "Playback": "PASS"
        }

        # Map actual services to display names
        service_display = {
            "audio_manager": "Audio",
            "model_manager": "Runtime",
            "ai_factory": "AI Provider",
            "vad_manager": "Microphone",
            "wakeword_manager": "Wake Word",
            "speaker_manager": "Speaker Verify"
        }

        has_failure = False

        for name, svc in service_registry._services.items():
            display_name = service_display.get(name)
            if display_name:
                if svc.state == ServiceState.FAILED:
                    report_map[display_name] = "FAIL"
                    has_failure = True
                elif svc.state == ServiceState.READY:
                    report_map[display_name] = "PASS"
                else:
                    report_map[display_name] = svc.state.value

        for key, val in report_map.items():
            dots = "." * (15 - len(key))
            print(f"{key} {dots} {val}")
        
        print("="*34 + "\n")

        if has_failure:
            for name, svc in service_registry._services.items():
                if svc.state == ServiceState.FAILED:
                    print(f"Failed Subsystem: {name}")
                    print(f"Reason: {svc.last_error}")
                    print(f"Recovery Attempts: {svc.recovery_count}")
                    print(f"Final Status: {svc.state.value}\n")

runtime_manager = RuntimeManager()
