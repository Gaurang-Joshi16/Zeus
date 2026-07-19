from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.events.bus import event_bus
from core.events.types import Event
from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from services.ai.interfaces.provider import IAIProvider
from services.ai.registry.health import AIHealthManager
from services.ai.types.enums import AIEngineType, ProviderLifecycleState


class AIEngineRegistry(BaseService):
    def __init__(self):
        super().__init__(name="ai_registry", dependencies=[])
        self._providers: Dict[AIEngineType, IAIProvider] = {}
        self.health_manager = AIHealthManager()

    async def _do_initialize(self) -> None:
        pass

    async def _do_start(self) -> None:
        pass

    async def _do_stop(self) -> None:
        for provider in self._providers.values():
            await provider.shutdown()
        self._providers.clear()

    async def health(self) -> Dict[str, Any]:
        base_health = await super().health()
        base_health.update({"status": "ok", "provider_count": len(self._providers)})
        return base_health

    async def register(self, provider: IAIProvider) -> None:
        engine_type = provider.engine_type
        if engine_type in self._providers:
            existing = self._providers[engine_type]
            if existing.provider_id == provider.provider_id:
                self._logger.warning(
                    f"Provider {provider.provider_id} is already registered for {engine_type.value}"
                )
                return
            self._logger.info(
                f"Replacing provider for {engine_type.value}: {existing.provider_id} -> {provider.provider_id}"
            )
            await existing.shutdown()

        self._providers[engine_type] = provider
        self.health_manager.report_heartbeat(provider.provider_id, provider.status())

        await event_bus.publish(
            Event(
                type="AI_PROVIDER_REGISTERED",
                payload={
                    "provider_id": provider.provider_id,
                    "provider_type": type(provider).__name__,
                    "engine_type": engine_type.value,
                    "lifecycle_state": provider.status().value,
                    "version": provider.version(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        )
        self._logger.info(
            f"Successfully registered provider {provider.provider_id} for {engine_type.value}"
        )

    def resolve(self, engine_type: AIEngineType) -> Optional[IAIProvider]:
        return self._providers.get(engine_type)

    def get_all_providers(self) -> List[IAIProvider]:
        return list(self._providers.values())

    async def publish_state_change(
        self, provider: IAIProvider, state: ProviderLifecycleState, error: str = ""
    ) -> None:
        self.health_manager.report_heartbeat(provider.provider_id, state)
        if state == ProviderLifecycleState.FAILED:
            self.health_manager.report_failure(provider.provider_id, error)

        await event_bus.publish(
            Event(
                type="AI_PROVIDER_CHANGED",
                payload={
                    "provider_id": provider.provider_id,
                    "provider_type": type(provider).__name__,
                    "engine_type": provider.engine_type.value,
                    "lifecycle_state": state.value,
                    "health_status": (
                        "ok" if state != ProviderLifecycleState.FAILED else "error"
                    ),
                    "error_details": error,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        )
