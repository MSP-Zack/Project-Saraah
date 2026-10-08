"""Optional provider-backed embeddings for Sarah's live memory path."""

import os
from typing import List, Optional

from openai import AsyncOpenAI


class EmbeddingProvider:
    """OpenAI-compatible embeddings with explicit configuration and no fake vectors."""

    def __init__(self):
        self.model = os.getenv("SARAH_EMBEDDING_MODEL", "").strip()
        self.api_key = (os.getenv("SARAH_EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
        self.base_url = (os.getenv("SARAH_EMBEDDING_BASE_URL") or "https://api.openai.com/v1").strip()
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url) if self.is_available else None

    @property
    def is_available(self) -> bool:
        return bool(self.model and self.api_key)

    async def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        if not self.client or not texts:
            return None
        response = await self.client.embeddings.create(model=self.model, input=texts)
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]
