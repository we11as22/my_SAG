"""
MySQL storage client

Uses SQLAlchemy 2.0 async API
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from sag.core.config import get_settings
from sag.exceptions import DatabaseError
from sag.utils import get_logger

logger = get_logger("storage.mysql")


class MySQLClient:
    """MySQL async client"""

    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_recycle: Optional[int] = None,
        echo: bool = False,
    ) -> None:
        """
        Initialize MySQL client

        Args:
            database_url: Database connection URL
            pool_size: Connection pool size
            max_overflow: Connection pool max overflow
            pool_recycle: Connection recycle time (seconds)
            echo: Whether to print SQL statements
        """
        settings = get_settings()

        self.database_url = database_url or settings.mysql_url
        self.pool_size = pool_size or settings.db_pool_size
        self.max_overflow = max_overflow or settings.db_max_overflow
        self.pool_recycle = pool_recycle or settings.db_pool_recycle

        # Create async engine
        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # Test connection before use
            echo=echo,
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        logger.info(
            "MySQL client initialized",
            extra={
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
            },
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Get database session (context manager)

        Yields:
            AsyncSession instance

        Example:
            >>> async with mysql_client.session() as session:
            ...     result = await session.execute(select(User))
            ...     users = result.scalars().all()
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database operation failed: {e}", exc_info=True)
                raise DatabaseError(f"Database operation failed: {e}") from e

    async def close(self) -> None:
        """Close database connection pool"""
        await self.engine.dispose()
        logger.info("MySQL connection pool closed")

    async def ping(self) -> bool:
        """
        Test database connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with self.session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


def create_mysql_client(
    database_url: Optional[str] = None,
    **kwargs: Any,
) -> MySQLClient:
    """
    Create MySQL client instance

    Args:
        database_url: Database connection URL
        **kwargs: Other parameters

    Returns:
        MySQLClient instance
    """
    return MySQLClient(database_url=database_url, **kwargs)


# Global client instance (singleton)
_mysql_client: Optional[MySQLClient] = None


def get_mysql_client() -> MySQLClient:
    """
    Get MySQL client singleton

    Returns:
        MySQLClient instance
    """
    global _mysql_client
    if _mysql_client is None:
        _mysql_client = create_mysql_client()
    return _mysql_client


async def close_mysql_client() -> None:
    """Close global MySQL client"""
    global _mysql_client
    if _mysql_client is not None:
        await _mysql_client.close()
        _mysql_client = None
