import time
from typing import AsyncGenerator, Dict

from core.logging.logger import CoreLogger
from core.runtime.base_service import BaseService
from core.events.bus import event_bus
from core.events.types import Event, EventTypes
from services.ai.factory.manager import AIProviderFactory
from services.ai.types.enums import AIEngineType
from services.ai.types.request import AIRequestContext


class AIProcessingManager(BaseService):
    def __init__(self, ai_factory: AIProviderFactory):
        super().__init__(name="ai_processing_manager", dependencies=["ai_factory"])
        self.ai_factory = ai_factory
        self._provider = None
        self._engine = None

    async def _do_initialize(self) -> None:
        self._logger.info("Initializing AI Processing Manager...")
        provider = self.ai_factory.registry.resolve(AIEngineType.LLM)
        if not provider:
            self._logger.warning("No LLM provider registered!")
            return
            
        self._provider = provider
        self._engine = self._provider.get_engine()
        self._logger.info(f"AI Processing Manager bound to {self._provider.provider_id}")

    async def _do_start(self) -> None:
        pass

    async def _do_stop(self) -> None:
        pass

    async def process_prompt(self, request: AIRequestContext) -> Dict:
        """
        Takes an AIRequestContext, sends it to the LLM Engine, streams deltas, 
        and returns the final response along with metrics.
        """
        if not self._engine:
            error_msg = "No LLM engine available."
            self._logger.error(error_msg)
            await event_bus.publish(Event(type="AI_PROCESSING_FAILED", payload={
                "conversationId": request.conversationId,
                "provider": request.provider,
                "error": error_msg
            }))
            return {"error": error_msg}

        start_time = time.time()
        final_response = ""
        token_usage = 0
        
        await event_bus.publish(Event(type="AI_PROCESSING_STARTED", payload={
            "conversationId": request.conversationId,
            "provider": self._provider.provider_id,
            "timestamp": time.time()
        }))

        try:
            # We assume ILLMEngine.generate now takes AIRequestContext
            async for chunk in self._engine.generate(request, request.transcript):
                final_response += chunk
                
                # Approximate token usage if provider doesn't report natively during stream
                # E.g. roughly 1.3 tokens per word
                words = len(chunk.split())
                token_usage += max(1, int(words * 1.3))

                await event_bus.publish(Event(type="AI_STREAM_DELTA", payload={
                    "conversationId": request.conversationId,
                    "delta": chunk,
                    "provider": self._provider.provider_id
                }))
            
            processing_time = time.time() - start_time
            
            payload = {
                "conversationId": request.conversationId,
                "provider": self._provider.provider_id,
                "response": final_response,
                "processingTime": processing_time,
                "tokenUsage": token_usage
            }
            
            await event_bus.publish(Event(type="AI_PROCESSING_COMPLETED", payload=payload))
            
            self._logger.info(f"[AI] Conversation: {request.conversationId} | Provider: {self._provider.provider_id} | Model: {request.model} | Processing: {processing_time:.2f}s | Tokens: {token_usage}")
            
            return payload

        except Exception as e:
            self._logger.error(f"Error during AI processing: {e}")
            await event_bus.publish(Event(type="AI_PROCESSING_FAILED", payload={
                "conversationId": request.conversationId,
                "provider": self._provider.provider_id,
                "error": str(e)
            }))
            return {"error": str(e)}
