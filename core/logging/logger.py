import logging
import sys
from typing import Optional


class CoreLogger:
    _instance: Optional[logging.Logger] = None

    @classmethod
    def get_logger(cls, name: str = "zeus.core") -> logging.Logger:
        if cls._instance is None:
            cls.initialize()
        return logging.getLogger(name)

    @classmethod
    def initialize(cls, level: int = logging.INFO) -> None:
        logger = logging.getLogger("zeus")
        logger.setLevel(level)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        cls._instance = logger
