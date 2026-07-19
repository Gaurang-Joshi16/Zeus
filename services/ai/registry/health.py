from datetime import datetime, timezone
from typing import Any, Dict

from core.logging.logger import CoreLogger
from services.ai.interfaces.provider import IAIProvider
from services.ai.types.enums import ProviderLifecycleState


class AIHealthManager:
    def __init__(self):
        self._logger = CoreLogger.get_logger("zeus.ai.health")
        self._health_data: Dict[str, Dict[str, Any]] = {}

    def report_heartbeat(
        self, provider_id: str, status: ProviderLifecycleState
    ) -> None:
        if provider_id not in self._health_data:
            self._health_data[provider_id] = {
                "failures": 0,
                "uptime_seconds": 0.0,
                "model_load_durations_ms": [],
                "last_seen": None,
            }
        self._health_data[provider_id]["last_seen"] = datetime.now(
            timezone.utc
        ).isoformat()
        self._health_data[provider_id]["current_status"] = status.value

    def report_failure(self, provider_id: str, error: str) -> None:
        if provider_id in self._health_data:
            self._health_data[provider_id]["failures"] += 1
            self._health_data[provider_id]["last_error"] = error
            self._logger.error(f"Provider {provider_id} reported failure: {error}")

    def report_load_duration(self, provider_id: str, duration_ms: int) -> None:
        if provider_id in self._health_data:
            self._health_data[provider_id]["model_load_durations_ms"].append(
                duration_ms
            )
            if len(self._health_data[provider_id]["model_load_durations_ms"]) > 10:
                self._health_data[provider_id]["model_load_durations_ms"].pop(0)

    def get_provider_health(self, provider: IAIProvider) -> Dict[str, Any]:
        base_health = provider.health()
        internal_health = self._health_data.get(provider.provider_id, {})
        return {"provider": base_health, "metrics": internal_health}
