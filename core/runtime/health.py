from typing import Any, Dict

from core.logging.logger import CoreLogger
from core.registry.registry import service_registry
from core.runtime.lifecycle import lifecycle_manager


class HealthManager:
    def __init__(self):
        self._logger = CoreLogger.get_logger("zeus.runtime.health")

    async def get_system_health(self) -> Dict[str, Any]:
        self._logger.debug("Generating system health report")

        services_health = await service_registry.health_report()

        all_ok = True
        if services_health:
            all_ok = all(
                status.get("status") == "ok"
                for status in services_health.values()
                if isinstance(status, dict)
            )

        overall_status = "ok" if all_ok else "degraded"

        return {
            "status": overall_status,
            "runtime_state": lifecycle_manager.state.name,
            "services": services_health,
        }


health_manager = HealthManager()
