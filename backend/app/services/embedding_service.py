"""
Embedding generation service using OpenRouter API
Generates vector embeddings for semantic search using pgvector
"""
from typing import List, Optional
from openai import AsyncOpenAI
from loguru import logger

from app.config import settings


class EmbeddingService:
    """
    Service for generating embeddings via OpenRouter
    Uses OpenAI-compatible API with OpenRouter endpoint
    """

    def __init__(self):
        """Initialize OpenRouter client"""
        if not settings.openrouter_api_key:
            logger.warning("OpenRouter API key not configured - embeddings disabled")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url
            )
            logger.info(f"Embedding service initialized with model: {settings.embedding_model}")

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            List of floats (1536 dimensions) or None if embeddings disabled
        """
        if not self.client:
            logger.debug("Embeddings disabled - skipping generation")
            return None

        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None

        try:
            response = await self.client.embeddings.create(
                input=text,
                model=settings.embedding_model
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text ({len(text)} chars) -> {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (each 1536 dimensions) or None for failed items
        """
        if not self.client:
            logger.debug("Embeddings disabled - skipping batch generation")
            return [None] * len(texts)

        if not texts:
            return []

        # Filter empty texts
        valid_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]

        if not valid_texts:
            logger.warning("All texts in batch are empty")
            return [None] * len(texts)

        try:
            # OpenRouter supports batch embedding
            response = await self.client.embeddings.create(
                input=[text for _, text in valid_texts],
                model=settings.embedding_model
            )

            # Map results back to original indices
            results: List[Optional[List[float]]] = [None] * len(texts)
            for idx, (original_idx, _) in enumerate(valid_texts):
                results[original_idx] = response.data[idx].embedding

            logger.info(f"Generated {len(valid_texts)} embeddings in batch")
            return results

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)


# Global service instance
embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service instance"""
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return embedding_service
