import logging
from typing import Any, Callable, TypeVar, Awaitable, Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ..core.config import settings

logger = logging.getLogger("worker-db-helper")

T = TypeVar('T')

async def create_worker_db_session() -> Optional[AsyncSession]:
    """
    Create a database session specifically for the worker context.
    This creates a new session connected to the current event loop.
    
    Returns:
        AsyncSession: A new database session
    """
    try:
        # Use the same database connection details as your application
        DATABASE_URI = settings.POSTGRES_URI
        DATABASE_PREFIX = settings.POSTGRES_ASYNC_PREFIX
        DATABASE_URL = f"{DATABASE_PREFIX}{DATABASE_URI}"
        
        # Create an engine tied to the current event loop
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        # Create a session factory
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Return a session
        return async_session()
    except Exception as e:
        logger.error(f"Error creating worker database session: {e}")
        return None

async def with_worker_db(operation: Callable[[AsyncSession], Awaitable[T]]) -> Optional[T]:
    """
    Execute a database operation using a session specific to the worker context.
    
    Args:
        operation: An async function that accepts a database session and returns a result
        
    Returns:
        The result of the operation or None if the session couldn't be created
        
    Example:
        ```python
        agent_ref = await with_worker_db(
            lambda db: crud_agent_references.get_by_fields(db, fields={"roomid": room_uuid})
        )
        ```
    """
    db = await create_worker_db_session()
    if db is None:
        return None
        
    try:
        # Execute the operation with the session
        return await operation(db)
    finally:
        # Make sure to close the session
        await db.close()