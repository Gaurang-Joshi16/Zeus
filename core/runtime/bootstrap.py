from core.config.manager import ConfigManager
from core.logging.logger import CoreLogger
from core.registry.registry import service_registry
from core.runtime.lifecycle import AppState, lifecycle_manager
from core.runtime.module_loader import module_loader


async def bootstrap_runtime(env_path: str = ".env") -> None:
    """
    Orchestrates the startup flow.
    Can be called from any host (FastAPI, CLI, Desktop).
    """

    # 1. Load Configuration
    ConfigManager.load(env_path)

    # 2. Initialize Logger
    log_level_str = ConfigManager.get("LOG_LEVEL", "INFO")
    import logging

    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    CoreLogger.initialize(level=log_level)
    logger = CoreLogger.get_logger("zeus.runtime.bootstrap")

    logger.info("Starting Zeus Runtime Bootstrap...")
    await lifecycle_manager.transition_to(AppState.BOOTING)

    # 3. Initialize Event Bus (Global instance ready)
    logger.debug("Event Bus initialized.")

    # 4. Initialize Dependency Container (Global instance ready)
    logger.debug("Dependency Container initialized.")

    # 5. Initialize Service Registry & Runtime Manager
    await lifecycle_manager.transition_to(AppState.INITIALIZING)
    from core.runtime.manager import runtime_manager
    await runtime_manager.initialize()

    # 6. Initialize Module Loader
    await module_loader.initialize_all()

    # 7. Register Core Services
    from services.ai.factory.manager import AIProviderFactory
    from services.ai.models.manager import ModelManager
    from services.ai.registry.manager import AIEngineRegistry
    from services.voice.audio.manager import AudioManager

    audio_manager = AudioManager()
    service_registry.register("audio_manager", audio_manager)

    model_manager = ModelManager()
    service_registry.register("model_manager", model_manager)

    ai_registry = AIEngineRegistry()
    service_registry.register("ai_registry", ai_registry)

    ai_factory = AIProviderFactory(registry=ai_registry, model_manager=model_manager)
    service_registry.register("ai_factory", ai_factory)

    from services.ai.vad.manager import VADManager
    from services.ai.wakeword.manager import WakeWordManager

    vad_manager = VADManager(audio_manager=audio_manager, ai_registry=ai_registry)
    service_registry.register("vad_manager", vad_manager)

    wakeword_manager = WakeWordManager(
        audio_manager=audio_manager, ai_registry=ai_registry
    )
    service_registry.register("wakeword_manager", wakeword_manager)

    from services.ai.speaker.manager import SpeakerManager

    speaker_manager = SpeakerManager(
        audio_manager=audio_manager, ai_registry=ai_registry
    )
    service_registry.register("speaker_manager", speaker_manager)

    from core.conversation.manager import conversation_manager
    service_registry.register("conversation_manager", conversation_manager)

    from services.ai.stt.manager import STTManager
    stt_manager = STTManager(ai_factory=ai_factory)
    service_registry.register("stt_manager", stt_manager)

    from services.ai.processing.manager import AIProcessingManager
    ai_processing_manager = AIProcessingManager(ai_factory=ai_factory)
    service_registry.register("ai_processing_manager", ai_processing_manager)

    # 8. Start Services via Runtime Manager
    await runtime_manager.start_all()

    # Initialize Runtime IPC Controller to start broadcasting
    from core.ipc.runtime_controller import runtime_ipc_controller
    await runtime_ipc_controller.initialize()

    from core.ipc.conversation_controller import conversation_ipc_controller
    await conversation_ipc_controller.initialize()

    from core.events.bus import event_bus
    from core.events.types import Event
    from core.setup.state_machine import SetupState, setup_state_machine

    if not speaker_manager.store.owner_exists():
        logger.info("No owner profile detected. Launching first-time setup.")
        await setup_state_machine.transition_to(SetupState.OWNER_NOT_FOUND)
    else:
        logger.info("Owner profile detected.")
        await setup_state_machine.transition_to(SetupState.READY)
        await event_bus.publish(Event(type="OWNER_READY", payload={}))

    # 9. Start Modules
    await module_loader.start_all()

    # 10. Publish APP_READY & Print Diagnostics
    await lifecycle_manager.transition_to(AppState.READY)
    runtime_manager.print_diagnostics()

    logger.info("Zeus Runtime Bootstrap Complete.")


async def shutdown_runtime() -> None:
    logger = CoreLogger.get_logger("zeus.runtime.bootstrap")
    logger.info("Shutting down Zeus Runtime...")

    await lifecycle_manager.transition_to(AppState.SHUTTING_DOWN)

    await module_loader.stop_all()
    await service_registry.stop_all()

    await lifecycle_manager.transition_to(AppState.STOPPED)
    logger.info("Zeus Runtime gracefully stopped.")
