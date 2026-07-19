from typing import Optional, Tuple

import numpy as np

from services.ai.speaker.config import SpeakerConfiguration
from services.ai.speaker.inference import SpeakerInference
from services.ai.speaker.store import SpeakerStore
from services.ai.speaker.types import ConfidenceBand, SpeakerProfile


class SpeakerVerifier:
    def __init__(
        self,
        store: SpeakerStore,
        inference: SpeakerInference,
        config: SpeakerConfiguration,
    ):
        self.store = store
        self.inference = inference
        self.config = config

    def _get_confidence_band(self, confidence: float) -> ConfidenceBand:
        if confidence >= 0.90:
            return ConfidenceBand.VERY_HIGH
        elif confidence >= 0.80:
            return ConfidenceBand.HIGH
        elif confidence >= self.config.verification_threshold:
            return ConfidenceBand.MEDIUM
        elif confidence >= self.config.verification_threshold - 0.1:
            return ConfidenceBand.LOW
        return ConfidenceBand.REJECTED

    async def verify(
        self, source_embedding: np.ndarray
    ) -> Tuple[bool, float, ConfidenceBand, Optional[SpeakerProfile]]:
        best_score = 0.0
        best_profile = None

        profiles = self.store.get_all_profiles()
        for profile in profiles:
            for emb_ref in profile.embedding_references:
                target_emb_obj = self.store.get_embedding(emb_ref)
                if target_emb_obj:
                    target_vec = np.array(target_emb_obj.vector)
                    score = await self.inference.compare_embeddings(
                        source_embedding, target_vec
                    )
                    if score > best_score:
                        best_score = score
                        best_profile = profile

        band = self._get_confidence_band(best_score)
        verified = best_score >= self.config.verification_threshold

        return verified, best_score, band, best_profile if verified else None
