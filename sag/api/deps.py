"""Dependency injection

Provides common dependencies
"""

from typing import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sag.core.storage.mysql import get_mysql_client
from sag.exceptions import DatabaseError


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session
    
    Handles FastAPI's HTTPException, not treating it as a database error
    """
    client = get_mysql_client()
    
    async with client.session_factory() as session:
        try:
            yield session
            # Only commit if no exception occurred
            await session.commit()
        except HTTPException:
            # HTTPException is a business logic exception, commit changes before raising
            await session.commit()
            raise
        except Exception as e:
            # Other exceptions are real database errors, rollback
            await session.rollback()
            # Log the error for debugging
            import traceback
            print(f"Database error in get_db: {e}")
            print(traceback.format_exc())
            raise DatabaseError(f"Database operation failed: {e}") from e

