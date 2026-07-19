import time
import uuid
from typing import Optional

import numpy as np

from services.ai.speaker.audio import VerificationAudioProvider
from services.ai.speaker.inference import SpeakerInference
from services.ai.speaker.types import (
    SpeakerResult,
)
from services.ai.speaker.verifier import SpeakerVerifier


class SpeakerPipeline:
    def __init__(
        self,
        audio_provider: VerificationAudioProvider,
        inference: SpeakerInference,
        verifier: SpeakerVerifier,
    ):
        self.audio_provider = audio_provider
        self.inference = inference
        self.verifier = verifier

    async def extract_embedding(self, frames: np.ndarray) -> np.ndarray:
        return await self.inference.extract_embedding(frames)

    async def run_verification(
        self, frames: Optional[np.ndarray] = None
    ) -> SpeakerResult:
        start_time = time.time()

        if frames is None:
            window_ms = self.verifier.config.verification_window_ms
            frames = self.audio_provider.get_audio_window(window_ms)

        source_embedding = await self.extract_embedding(frames)

        verified, confidence, band, profile = await self.verifier.verify(
            source_embedding
        )

        inference_time_ms = (time.time() - start_time) * 1000

        return SpeakerResult(
            verified=verified,
            confidence_band=band,
            confidence_score=confidence,
            threshold=self.verifier.config.verification_threshold,
            speaker_id=profile.profile_id if profile else None,
            provider=self.inference.provider_id,
            model_version=self.inference.model_version,
            inference_time_ms=inference_time_ms,
            embedding_version="1.0",
            session_id=str(uuid.uuid4()),
        )
