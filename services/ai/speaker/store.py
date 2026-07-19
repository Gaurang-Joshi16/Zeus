from typing import Dict, List, Optional

from cryptography.fernet import Fernet

from services.ai.speaker.types import SpeakerEmbedding, SpeakerProfile, SpeakerRole


class SpeakerStore:
    def __init__(self, encryption_enabled: bool = True):
        self.encryption_enabled = encryption_enabled
        self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)

        self._profiles: Dict[str, SpeakerProfile] = {}
        self._embeddings: Dict[str, SpeakerEmbedding] = {}

    def _encrypt(self, data: str) -> bytes:
        if not self.encryption_enabled:
            return data.encode("utf-8")
        return self._cipher.encrypt(data.encode("utf-8"))

    def _decrypt(self, data: bytes) -> str:
        if not self.encryption_enabled:
            return data.decode("utf-8")
        return self._cipher.decrypt(data).decode("utf-8")

    def save_profile(self, profile: SpeakerProfile):
        self._profiles[profile.profile_id] = profile

    def get_profile(self, profile_id: str) -> Optional[SpeakerProfile]:
        return self._profiles.get(profile_id)

    def owner_exists(self) -> bool:
        for profile in self._profiles.values():
            if profile.role == SpeakerRole.OWNER:
                return True
        return False

    def save_embedding(self, embedding: SpeakerEmbedding):
        self._embeddings[embedding.embedding_id] = embedding

    def get_embedding(self, embedding_id: str) -> Optional[SpeakerEmbedding]:
        return self._embeddings.get(embedding_id)

    def get_all_profiles(self) -> List[SpeakerProfile]:
        return list(self._profiles.values())

    def delete_profile(self, profile_id: str):
        if profile_id in self._profiles:
            profile = self._profiles[profile_id]
            for emb_id in profile.embedding_references:
                if emb_id in self._embeddings:
                    del self._embeddings[emb_id]
            del self._profiles[profile_id]

    def secure_delete(self):
        self._profiles.clear()
        self._embeddings.clear()
        self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)
