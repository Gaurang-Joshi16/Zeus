import asyncio
from typing import Any, Dict

from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from core.ipc.adapter import ipc_adapter
from core.logging.logger import CoreLogger


class ConversationIPCController:
    def __init__(self):
        self._logger = CoreLogger.get_logger("zeus.ipc.conversation")

    async def initialize(self):
        # Subscribe to all conversation events
        events_to_forward = [
            EventTypes.CONVERSATION_STARTED,
            EventTypes.WAKEWORD_DETECTED,
            EventTypes.SPEAKER_VERIFICATION_STARTED,
            EventTypes.SPEAKER_VERIFIED,
            EventTypes.SPEAKER_REJECTED,
            EventTypes.LISTENING_STARTED,
            EventTypes.LISTENING_STOPPED,
            EventTypes.TRANSCRIPTION_STARTED,
            EventTypes.TRANSCRIPTION_COMPLETED,
            EventTypes.AI_PROCESSING_STARTED,
            EventTypes.AI_PROCESSING_COMPLETED,
            EventTypes.RESPONSE_GENERATION_STARTED,
            EventTypes.RESPONSE_GENERATION_COMPLETED,
            EventTypes.SPEAKING_STARTED,
            EventTypes.SPEAKING_COMPLETED,
            EventTypes.CONVERSATION_INTERRUPTED,
            EventTypes.CONVERSATION_TIMEOUT,
            EventTypes.CONVERSATION_FAILED,
            EventTypes.CONVERSATION_COMPLETED,
            "TRANSCRIPTION_PARTIAL",
            "RECORDING_STARTED",
            "RECORDING_STOPPED",
            "VAD_SPEECH_STARTED",
            "VAD_SPEECH_ENDED",
            "AI_PROCESSING_STARTED",
            "AI_STREAM_DELTA",
            "AI_PROCESSING_COMPLETED",
            "AI_PROCESSING_FAILED",
        ]

        for event_type in events_to_forward:
            event_bus.subscribe(event_type, self._forward_event)

    async def _forward_event(self, event: Event):
        try:
            await ipc_adapter.emit_event(event.type, event.payload)
        except Exception as e:
            self._logger.error(f"Failed to forward conversation event {event.type}: {e}")


conversation_ipc_controller = ConversationIPCController()
