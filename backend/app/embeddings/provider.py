import hashlib
import math
from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.config import settings
from app.core.logging import logger

try:
    from openai import OpenAI, AsyncOpenAI
except ImportError:
    OpenAI = None
    AsyncOpenAI = None

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = None, dimension: int = None):
        self.api_key = api_key or settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self._dimension = dimension or settings.EMBEDDING_DIMENSION
        if not self.api_key or self.api_key.startswith("sk-your") or self.api_key.startswith("sk-proj-your"):
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_query(self, text: str) -> List[float]:
        if not self.client:
            # Fallback to deterministic mock if API key not configured
            return LocalFallbackEmbeddingProvider(dimension=self._dimension)._generate_hash_vector(text)
        try:
            resp = await self.client.embeddings.create(
                input=[text],
                model=self.model,
                dimensions=self._dimension if "text-embedding-3" in self.model else None
            )
            return resp.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}. Falling back to deterministic local embedding.")
            return LocalFallbackEmbeddingProvider(dimension=self._dimension)._generate_hash_vector(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.client:
            fallback = LocalFallbackEmbeddingProvider(dimension=self._dimension)
            return [fallback._generate_hash_vector(t) for t in texts]
        try:
            # Batch process up to 100 texts at a time
            all_embeddings: List[List[float]] = []
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                resp = await self.client.embeddings.create(
                    input=batch,
                    model=self.model,
                    dimensions=self._dimension if "text-embedding-3" in self.model else None
                )
                all_embeddings.extend([d.embedding for d in resp.data])
            return all_embeddings
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {e}. Using deterministic local embeddings.")
            fallback = LocalFallbackEmbeddingProvider(dimension=self._dimension)
            return [fallback._generate_hash_vector(t) for t in texts]

class LocalFallbackEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic normalized embedding generator used for offline testing,
    CI/CD test suites, or environments without external LLM API access.
    Produces high semantic relevance for lexical and token-overlap similarity.
    """
    def __init__(self, dimension: int = 1536):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_hash_vector(self, text: str) -> List[float]:
        tokens = text.lower().split()
        vec = [0.0] * self._dimension
        if not tokens:
            return vec
        for i, token in enumerate(tokens):
            h = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            idx = h % self._dimension
            vec[idx] += 1.0 + (0.1 * (i % 5))
        # Add character n-grams to capture spelling variations (e.g. Urdu/Roman Urdu)
        clean_text = "".join(c for c in text.lower() if c.isalnum())
        for n in [3, 4]:
            for i in range(len(clean_text) - n + 1):
                gram = clean_text[i:i+n]
                h = int(hashlib.sha256(gram.encode('utf-8')).hexdigest(), 16)
                idx = h % self._dimension
                vec[idx] += 0.5

        # Normalize to unit vector
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]
        return vec

    async def embed_query(self, text: str) -> List[float]:
        return self._generate_hash_vector(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_hash_vector(t) for t in texts]

def get_embedding_provider(provider_type: Optional[str] = None) -> BaseEmbeddingProvider:
    provider = (provider_type or settings.EMBEDDING_PROVIDER).lower()
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    elif provider == "local" or provider == "mock":
        return LocalFallbackEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
    else:
        # Default to OpenAI with automatic graceful fallback
        return OpenAIEmbeddingProvider()
