import asyncio
import uuid
import time
from typing import Optional

from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from core.runtime.lifecycle import lifecycle_manager, AppState
from core.conversation.types import ConversationState, Conversation
from services.ai.types.context import AIContext
from core.registry.registry import service_registry


class ConversationManager(BaseService):
    def __init__(self):
        # ConversationManager sits at the top and depends on all other sub-managers
        super().__init__(
            name="conversation_manager",
            dependencies=["audio_manager", "wakeword_manager", "speaker_manager", "stt_manager", "ai_processing_manager"]
        )
        self.active_conversation: Optional[Conversation] = None
        self._state_task: Optional[asyncio.Task] = None

        # Configurable timeouts
        self.VERIFICATION_TIMEOUT = 5.0
        self.LISTENING_TIMEOUT = 30.0
        self.TRANSCRIBING_TIMEOUT = 60.0
        self.THINKING_TIMEOUT = 30.0
        self.SPEAKING_TIMEOUT = 30.0

        # State tracking for VAD
        self._vad_speech_active = False
        self._vad_speech_ended_event = asyncio.Event()
        self._last_speech_duration_ms = 0
        
        # Overall voice state
        self._voice_state = "IDLE"

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing Conversation Manager...")
        event_bus.subscribe(EventTypes.WAKEWORD_DETECTED, self._on_wake_word_detected)
        event_bus.subscribe(EventTypes.SPEAKER_VERIFIED, self._on_speaker_verified)
        event_bus.subscribe(EventTypes.SPEAKER_REJECTED, self._on_speaker_rejected)
        event_bus.subscribe("VAD_SPEECH_STARTED", self._on_vad_started)
        event_bus.subscribe("VAD_SPEECH_ENDED", self._on_vad_ended)

    async def _do_start(self) -> None:
        self._logger.info("Conversation Manager started.")

    async def _do_stop(self) -> None:
        self._logger.info("Stopping Conversation Manager...")
        event_bus.unsubscribe(EventTypes.WAKEWORD_DETECTED, self._on_wake_word_detected)
        event_bus.unsubscribe(EventTypes.SPEAKER_VERIFIED, self._on_speaker_verified)
        event_bus.unsubscribe(EventTypes.SPEAKER_REJECTED, self._on_speaker_rejected)
        event_bus.unsubscribe("VAD_SPEECH_STARTED", self._on_vad_started)
        event_bus.unsubscribe("VAD_SPEECH_ENDED", self._on_vad_ended)
        
        if self._state_task and not self._state_task.done():
            self._state_task.cancel()
        
        if self.active_conversation:
            await self._transition_conversation(ConversationState.INTERRUPTED, "Service stopping")

    async def _publish_state_event(self, event_type: str, details: dict = None):
        if not self.active_conversation:
            return
            
        payload = {
            "conversationId": self.active_conversation.id,
            "currentState": self.active_conversation.state.value,
            "timestamp": time.time(),
            "details": details or {}
        }
        await event_bus.publish(Event(type=event_type, payload=payload))

    async def _transition_conversation(self, new_state: ConversationState, reason: str = "", details: dict = None):
        if not self.active_conversation:
            return

        previous_state = self.active_conversation.state
        self.active_conversation.state = new_state
        self._logger.info(f"[Conversation {self.active_conversation.id}] {previous_state.value} -> {new_state.value} ({reason})")

        payload = {
            "conversationId": self.active_conversation.id,
            "previousState": previous_state.value,
            "currentState": new_state.value,
            "timestamp": time.time(),
            "details": details or {"reason": reason}
        }

        if new_state == ConversationState.INTERRUPTED:
            await event_bus.publish(Event(type=EventTypes.CONVERSATION_INTERRUPTED, payload=payload))
            self._cleanup_conversation()
            await self._set_voice_state("IDLE")
        elif new_state == ConversationState.FAILED:
            await event_bus.publish(Event(type=EventTypes.CONVERSATION_FAILED, payload=payload))
            self._cleanup_conversation()
            await self._set_voice_state("ERROR")
            # Return to IDLE after a brief error display
            asyncio.create_task(self._reset_to_idle_after_delay(2.0))
        elif new_state == ConversationState.TIMEOUT:
            await event_bus.publish(Event(type=EventTypes.CONVERSATION_TIMEOUT, payload=payload))
            self._cleanup_conversation()
            await self._set_voice_state("ERROR")
            asyncio.create_task(self._reset_to_idle_after_delay(2.0))
        elif new_state == ConversationState.COMPLETED:
            await event_bus.publish(Event(type=EventTypes.CONVERSATION_COMPLETED, payload=payload))
            self._cleanup_conversation()
            await self._set_voice_state("IDLE")
        else:
            # Map intermediate states
            state_map = {
                ConversationState.WAKE_WORD_DETECTED: "WAKE_WORD_DETECTED",
                ConversationState.VERIFYING_SPEAKER: "PROCESSING",
                ConversationState.LISTENING: "LISTENING",
                ConversationState.TRANSCRIBING: "PROCESSING",
                ConversationState.THINKING: "PROCESSING",
                ConversationState.GENERATING_RESPONSE: "PROCESSING",
                ConversationState.SPEAKING: "SPEAKING"
            }
            if new_state in state_map:
                await self._set_voice_state(state_map[new_state])

    async def _reset_to_idle_after_delay(self, delay: float):
        await asyncio.sleep(delay)
        if not self.active_conversation:
            await self._set_voice_state("IDLE")

    async def _set_voice_state(self, state: str):
        if self._voice_state != state:
            self._logger.info(f"[Voice State] {self._voice_state} -> {state}")
            self._voice_state = state
            await event_bus.publish(Event(type="VOICE_STATE_CHANGED", payload={"state": state}))

    def _cleanup_conversation(self):
        if self.active_conversation:
            self.active_conversation.end_time = time.time()
            duration = self.active_conversation.end_time - self.active_conversation.start_time
            self._logger.info(f"[Conversation] ID: {self.active_conversation.id} ended. Duration: {duration:.2f} seconds.")
            self.active_conversation = None

    async def _on_vad_started(self, event: Event):
        self._vad_speech_active = True
        self._vad_speech_ended_event.clear()
        if not self.active_conversation and self._voice_state == "IDLE":
            await self._set_voice_state("WAKE_WORD_LISTENING")

    async def _on_vad_ended(self, event: Event):
        self._vad_speech_active = False
        self._last_speech_duration_ms = event.payload.get("duration_ms", 0)
        self._vad_speech_ended_event.set()
        if not self.active_conversation and self._voice_state == "WAKE_WORD_LISTENING":
            await self._set_voice_state("IDLE")

    async def _on_wake_word_detected(self, event: Event):
        if lifecycle_manager.state != AppState.READY:
            self._logger.debug("Wake word detected but system is not READY. Ignoring.")
            return

        if self.active_conversation:
            if self._state_task and not self._state_task.done():
                self._state_task.cancel()
            await self._transition_conversation(ConversationState.INTERRUPTED, "New wake word detected")

        conv_id = str(uuid.uuid4())
        self.active_conversation = Conversation(id=conv_id, start_time=time.time())
        self._vad_speech_ended_event.clear()
        
        self._logger.info(f"Starting new conversation: {conv_id}")
        await self._publish_state_event(EventTypes.CONVERSATION_STARTED)
        await self._transition_conversation(ConversationState.WAKE_WORD_DETECTED, "Wake word detected")
        await self._publish_state_event(EventTypes.WAKEWORD_DETECTED) 

        self._state_task = asyncio.create_task(self._run_state_machine())

    async def _run_state_machine(self):
        try:
            # 1. VERIFYING_SPEAKER
            await self._transition_conversation(ConversationState.VERIFYING_SPEAKER, "Starting verification")
            await self._publish_state_event(EventTypes.SPEAKER_VERIFICATION_STARTED)
            
            start_wait = time.time()
            while self.active_conversation and self.active_conversation.state == ConversationState.VERIFYING_SPEAKER:
                if time.time() - start_wait > self.VERIFICATION_TIMEOUT:
                    await self._transition_conversation(ConversationState.TIMEOUT, "Speaker verification timeout")
                    return
                await asyncio.sleep(0.1)

            if not self.active_conversation or self.active_conversation.state != ConversationState.LISTENING:
                return

            # 2. LISTENING
            await self._publish_state_event(EventTypes.LISTENING_STARTED)
            await event_bus.publish(Event(type="RECORDING_STARTED", payload={"conversationId": self.active_conversation.id}))

            # Wait for VAD speech to end (or if it never started, just timeout)
            try:
                await asyncio.wait_for(self._vad_speech_ended_event.wait(), timeout=self.LISTENING_TIMEOUT)
            except asyncio.TimeoutError:
                await self._transition_conversation(ConversationState.TIMEOUT, "VAD Timeout")
                return

            await self._publish_state_event(EventTypes.LISTENING_STOPPED)
            await event_bus.publish(Event(type="RECORDING_STOPPED", payload={"conversationId": self.active_conversation.id}))

            if not self.active_conversation: return

            # 3. TRANSCRIBING
            await self._transition_conversation(ConversationState.TRANSCRIBING, "Starting transcription")
            await self._publish_state_event(EventTypes.TRANSCRIPTION_STARTED)
            
            # Fetch audio frames from AudioManager based on VAD duration
            audio_manager = service_registry.get("audio_manager")
            frames_to_read = int(audio_manager.buffer.sample_rate * (self._last_speech_duration_ms / 1000.0))
            # Pad with 1 second to make sure we got everything
            frames_to_read += audio_manager.buffer.sample_rate
            audio_frames = audio_manager.buffer.read(frames_to_read)

            stt_manager = service_registry.get("stt_manager")
            context = AIContext(session_id=self.active_conversation.id, user_id=self.active_conversation.speaker_id or "unknown")
            
            final_text = ""
            start_transcription_time = time.time()
            
            # Use STT manager to stream partials
            async for partial in stt_manager.transcribe_stream(context, audio_frames):
                final_text = partial
                await event_bus.publish(Event(type=EventTypes.TRANSCRIPTION_PARTIAL, payload={
                    "conversationId": self.active_conversation.id,
                    "text": partial
                }))

            processing_time = int((time.time() - start_transcription_time) * 1000)

            await event_bus.publish(Event(type=EventTypes.TRANSCRIPTION_COMPLETED, payload={
                "conversationId": self.active_conversation.id,
                "text": final_text,
                "confidence": 0.95,  # Dummy confidence for now
                "language": "en",
                "processingTime": processing_time
            }))

            if self.active_conversation:
                self.active_conversation.metadata["final_transcript"] = final_text

            if not self.active_conversation: return

            # 4. THINKING
            await self._transition_conversation(ConversationState.THINKING, "Starting AI processing")
            
            ai_manager = service_registry.get("ai_processing_manager")
            if ai_manager:
                from datetime import datetime, timezone
                from services.ai.types.request import AIRequestContext
                from core.config.manager import ConfigManager
                
                request_context = AIRequestContext(
                    conversationId=self.active_conversation.id,
                    timestamp=datetime.now(timezone.utc),
                    transcript=final_text,
                    provider=ConfigManager.get("AI_LLM_PROVIDER", "ollama"),
                    model=ConfigManager.get("AI_MODEL", "llama3"),
                    sessionId=self.active_conversation.id,
                    speakerId=self.active_conversation.speaker_id
                )
                
                response_payload = await ai_manager.process_prompt(request_context)
                
                if not self.active_conversation: return

                if "error" in response_payload:
                    await self._transition_conversation(ConversationState.FAILED, "AI Processing Failed")
                    return
                else:
                    self.active_conversation.response = response_payload.get("response", "")
            
            await self._transition_conversation(ConversationState.GENERATING_RESPONSE, "AI processing completed")
            
            # Sprint 2.3 ends here.
            await asyncio.sleep(1.0)
            await self._transition_conversation(ConversationState.COMPLETED, "Sprint 2.3 pipeline finished")

        except asyncio.CancelledError:
            self._logger.info("Conversation state machine cancelled due to interruption.")
        except Exception as e:
            self._logger.error(f"Error in conversation state machine: {e}")
            if self.active_conversation:
                await self._transition_conversation(ConversationState.FAILED, str(e))

    async def _on_speaker_verified(self, event: Event):
        if self.active_conversation and self.active_conversation.state == ConversationState.VERIFYING_SPEAKER:
            self._logger.info("Speaker verified successfully.")
            self.active_conversation.speaker_id = event.payload.get("speaker_id")
            await self._transition_conversation(ConversationState.LISTENING, "Speaker verified")

    async def _on_speaker_rejected(self, event: Event):
        if self.active_conversation and self.active_conversation.state == ConversationState.VERIFYING_SPEAKER:
            self._logger.info("Speaker rejected.")
            await self._transition_conversation(ConversationState.FAILED, "Speaker rejected")

conversation_manager = ConversationManager()
