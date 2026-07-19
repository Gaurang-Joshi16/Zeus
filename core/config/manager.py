import os
from typing import Any, Dict, Optional


class ConfigManager:
    _config: Dict[str, Any] = {}

    @classmethod
    def load(cls, env_path: Optional[str] = None) -> None:
        """Loads configuration from environment variables (or .env if available)"""
        if env_path and os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, _, value = line.partition("=")
                        os.environ[key.strip()] = value.strip()

        cls._config = dict(os.environ)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return cls._config.get(key, default)

    @classmethod
    def require(cls, key: str) -> str:
        if key not in cls._config:
            raise KeyError(f"Missing required configuration key: {key}")
        return str(cls._config[key])
