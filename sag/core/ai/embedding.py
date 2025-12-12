"""
Embedding generation service

Provides unified text vectorization capability, shared by all modules
"""

from typing import List, Optional

from sag.core.config import get_settings
from sag.exceptions import AIError
from sag.utils import get_logger

logger = get_logger("ai.embedding")


class EmbeddingClient:
    """
    Embedding client
    
    Unified text vectorization service, supports:
    - OpenAI Embedding API
    - Custom Embedding services
    - Local Embedding models (future extension)
    """
    
    def __init__(
        self, 
        model: Optional[str] = None, 
        base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize Embedding client
        
        Args:
            model: Model name (default read from config)
            base_url: API address (default read from config)
            api_key: API key (default read from config)
        """
        from openai import AsyncOpenAI
        
        settings = get_settings()
        
        self.model = model or settings.embedding_model_name
        self.base_url = base_url or settings.embedding_base_url or settings.llm_base_url
        # ✅ Prioritize passed api_key, then environment variables
        self.api_key = api_key or settings.embedding_api_key or settings.llm_api_key
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = AsyncOpenAI(**client_kwargs)
        
        logger.info(
            f"Embedding client initialized",
            extra={
                "model": self.model,
                "base_url": self.base_url or "default",
            },
        )
    
    async def generate(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Text content
            
        Returns:
            Embedding vector
            
        Raises:
            AIError: Generation failed
        """
        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.model,
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(
                f"Embedding generation successful",
                extra={
                    "text_length": len(text),
                    "vector_dim": len(embedding),
                },
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)
            raise AIError(f"Embedding generation failed: {e}") from e
    
    async def batch_generate(self, texts: List[str]) -> List[List[float]]:
        """
        Batch generate embedding vectors
        
        Args:
            texts: Text list
            
        Returns:
            Embedding vector list
            
        Raises:
            AIError: Generation failed
        """
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=self.model,
            )
            
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(
                f"Batch embedding generation successful",
                extra={
                    "batch_size": len(texts),
                    "vector_dim": len(embeddings[0]) if embeddings else 0,
                },
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}", exc_info=True)
            raise AIError(f"Batch embedding generation failed: {e}") from e


# Global singleton
_embedding_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """
    Get global Embedding client (singleton) - synchronous version
    
    ⚠️ Warning: This function is only for pure synchronous environments (e.g., test scripts)
    In async environments, please use factory.get_embedding_client() async version
    
    This function does not use configuration management, only reads from environment variables
    
    Recommended usage:
    - factory.get_embedding_client(scenario='general') - async version, supports configuration management
    
    Returns:
        EmbeddingClient instance
    """
    global _embedding_client
    if _embedding_client is None:
        # Simple creation, read config from environment variables (does not use factory's config management)
        _embedding_client = EmbeddingClient()
    return _embedding_client


def reset_embedding_client() -> None:
    """Reset global Embedding client"""
    global _embedding_client
    _embedding_client = None


async def generate_embedding(text: str) -> List[float]:
    """
    Convenience function to generate embedding
    
    Args:
        text: Text content
        
    Returns:
        Embedding vector
    """
    client = get_embedding_client()
    return await client.generate(text)


async def batch_generate_embedding(texts: List[str]) -> List[List[float]]:
    """
    Convenience function to batch generate embeddings
    
    Args:
        texts: Text list
        
    Returns:
        Embedding vector list
    """
    client = get_embedding_client()
    return await client.batch_generate(texts)

