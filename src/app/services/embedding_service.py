import asyncio
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI  # New import for client-based approach
from ..core.config import settings

logger = logging.getLogger("embedding-service")

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = "text-embedding-3-small"
        self.max_batch_size = 100  # OpenAI's limit for embeddings API
        self.dimension = 1536  # Dimension of the embeddings
        # Create a client instance
        self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts with adaptive batch size"""
        if not texts:
            return []
            
        all_embeddings = []
        
        # Determine maximum batch size based on text length
        avg_text_length = sum(len(text) for text in texts) / len(texts)
        adaptive_batch_size = min(
            self.max_batch_size,
            max(1, int(100000 / avg_text_length))  # Adjust batch size inversely to text length
        )
        
        logger.info(f"Using batch size of {adaptive_batch_size} for embedding generation")
        
        # Process in batches
        for i in range(0, len(texts), adaptive_batch_size):
            batch = texts[i:i + adaptive_batch_size]
            try:
                # Using the new client-based API structure
                response = await self.client.embeddings.create(
                    input=batch,
                    model=self.model,
                )
                # Extract embeddings from response (note the changed response structure)
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                logger.info(f"Generated embeddings for batch {i//adaptive_batch_size + 1}/{(len(texts) + adaptive_batch_size - 1)//adaptive_batch_size}")
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                # Return empty vectors for failed batch
                all_embeddings.extend([[0.0] * self.dimension] * len(batch))
                
        return all_embeddings

embedding_service = EmbeddingService()