"""
Redis cache client

Supports string, hash, set and other data structures
"""

import json
from typing import Any, List, Optional

import redis.asyncio as aioredis

from sag.core.config import get_settings
from sag.exceptions import CacheError
from sag.utils import get_logger

logger = get_logger("storage.redis")


class RedisClient:
    """Redis async client"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Redis client

        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            db: Database number
            **kwargs: Other parameters
        """
        settings = get_settings()

        self.host = host or settings.redis_host
        self.port = port or settings.redis_port
        self.password = password or settings.redis_password
        self.db = db or settings.redis_db

        # Build connection URL
        if self.password:
            url = f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        else:
            url = f"redis://{self.host}:{self.port}/{self.db}"

        # Create client
        self.client = aioredis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
            **kwargs,
        )

        logger.info(
            "Redis client initialized",
            extra={"host": self.host, "port": self.port, "db": self.db},
        )

    async def get(self, key: str) -> Optional[Any]:
        """
        Get cache value

        Args:
            key: Key

        Returns:
            Value (JSON deserialized), None if not exists
        """
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except json.JSONDecodeError:
            # If not JSON, return string directly
            return value
        except Exception as e:
            logger.error(f"Get cache failed: {e}", exc_info=True)
            raise CacheError(f"Get cache failed: {e}") from e

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """
        Set cache value

        Args:
            key: Key
            value: Value (auto JSON serialized)
            expire: Expiration time (seconds)

        Returns:
            True if set successfully
        """
        try:
            # JSON serialization
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)

            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Set cache failed: {e}", exc_info=True)
            raise CacheError(f"Set cache failed: {e}") from e

    async def delete(self, key: str) -> bool:
        """
        Delete cache

        Args:
            key: Key

        Returns:
            True if deleted successfully
        """
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Delete cache failed: {e}", exc_info=True)
            raise CacheError(f"Delete cache failed: {e}") from e

    async def exists(self, key: str) -> bool:
        """
        Check if key exists

        Args:
            key: Key

        Returns:
            True if exists
        """
        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Check cache existence failed: {e}", exc_info=True)
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time

        Args:
            key: Key
            seconds: Seconds

        Returns:
            True if set successfully
        """
        try:
            return bool(await self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Set expiration time failed: {e}", exc_info=True)
            return False

    async def ttl(self, key: str) -> int:
        """
        Get remaining expiration time

        Args:
            key: Key

        Returns:
            Remaining seconds, -1 means never expires, -2 means not exists
        """
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Get TTL failed: {e}", exc_info=True)
            return -2

    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment counter

        Args:
            key: Key
            amount: Increment amount

        Returns:
            Value after increment
        """
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Increment counter failed: {e}", exc_info=True)
            raise CacheError(f"Increment counter failed: {e}") from e

    async def hget(self, name: str, key: str) -> Optional[Any]:
        """
        Get hash field value

        Args:
            name: Hash name
            key: Field key

        Returns:
            Field value
        """
        try:
            value = await self.client.hget(name, key)
            if value is None:
                return None
            return json.loads(value)
        except json.JSONDecodeError:
            return value
        except Exception as e:
            logger.error(f"Get hash field failed: {e}", exc_info=True)
            raise CacheError(f"Get hash field failed: {e}") from e

    async def hset(
        self,
        name: str,
        key: str,
        value: Any,
    ) -> bool:
        """
        Set hash field value

        Args:
            name: Hash name
            key: Field key
            value: Field value

        Returns:
            True if set successfully
        """
        try:
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            await self.client.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Set hash field failed: {e}", exc_info=True)
            raise CacheError(f"Set hash field failed: {e}") from e

    async def hdel(self, name: str, *keys: str) -> int:
        """
        Delete hash fields

        Args:
            name: Hash name
            *keys: Field key list

        Returns:
            Number of deleted fields
        """
        try:
            return await self.client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Delete hash fields failed: {e}", exc_info=True)
            raise CacheError(f"Delete hash fields failed: {e}") from e

    async def hgetall(self, name: str) -> dict:
        """
        Get all hash fields

        Args:
            name: Hash name

        Returns:
            Field dictionary
        """
        try:
            return await self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Get all hash fields failed: {e}", exc_info=True)
            raise CacheError(f"Get all hash fields failed: {e}") from e

    async def sadd(self, name: str, *values: Any) -> int:
        """
        Add set members

        Args:
            name: Set name
            *values: Member value list

        Returns:
            Number of added members
        """
        try:
            return await self.client.sadd(name, *values)
        except Exception as e:
            logger.error(f"Add set members failed: {e}", exc_info=True)
            raise CacheError(f"Add set members failed: {e}") from e

    async def smembers(self, name: str) -> List[str]:
        """
        Get all set members

        Args:
            name: Set name

        Returns:
            Member list
        """
        try:
            members = await self.client.smembers(name)
            return list(members)
        except Exception as e:
            logger.error(f"Get set members failed: {e}", exc_info=True)
            raise CacheError(f"Get set members failed: {e}") from e

    async def sismember(self, name: str, value: Any) -> bool:
        """
        Check if is set member

        Args:
            name: Set name
            value: Member value

        Returns:
            True if is member
        """
        try:
            return bool(await self.client.sismember(name, value))
        except Exception as e:
            logger.error(f"Check set member failed: {e}", exc_info=True)
            return False

    async def close(self) -> None:
        """Close Redis connection"""
        await self.client.close()
        logger.info("Redis connection closed")

    async def ping(self) -> bool:
        """
        Test connection

        Returns:
            True if connection successful
        """
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False


# Global client instance (singleton)
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Get Redis client singleton

    Returns:
        RedisClient instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


async def close_redis_client() -> None:
    """Close global Redis client"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
