from typing import List

from core.logging.logger import CoreLogger
from core.registry.interfaces import IService


class IModule(IService):
    """Marker interface for Modules (which act like large Services)"""

    pass


class ModuleLoader:
    def __init__(self):
        self._modules: List[IModule] = []
        self._logger = CoreLogger.get_logger("zeus.runtime.modules")

    def register_module(self, module: IModule) -> None:
        self._modules.append(module)
        self._logger.info(f"Registered module: {module.__class__.__name__}")

    async def initialize_all(self) -> None:
        for module in self._modules:
            self._logger.debug(f"Initializing module: {module.__class__.__name__}")
            await module.initialize()

    async def start_all(self) -> None:
        for module in self._modules:
            self._logger.debug(f"Starting module: {module.__class__.__name__}")
            await module.start()

    async def stop_all(self) -> None:
        for module in reversed(self._modules):
            self._logger.debug(f"Stopping module: {module.__class__.__name__}")
            await module.stop()


module_loader = ModuleLoader()
