"""
Database configuration and session management.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from apps.backend.src.core.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
    
    def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._engine is not None:
            return
        
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.is_development,
            poolclass=NullPool if settings.is_development else None,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=10,
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        
        # Add event listeners for debugging
        if settings.is_development:
            @event.listens_for(self._engine.sync_engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                conn.info.setdefault("query_start_time", []).append(__import__("time").time())
            
            @event.listens_for(self._engine.sync_engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                total = __import__("time").time() - conn.info["query_start_time"].pop(-1)
                if total > 1.0:  # Log slow queries
                    import logging
                    logging.getLogger("sqlalchemy.slow").warning(
                        f"Slow query ({total:.2f}s): {statement[:200]}"
                    )
    
    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self.initialize()
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self.initialize()
        return self._session_factory
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    async def create_tables(self) -> None:
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# Global database manager instance
db_manager = DatabaseManager()


async get_db_session = db_manager.session


async def init_db() -> None:
    """Initialize database on startup."""
    db_manager.initialize()


async def close_db() -> None:
    """Close database on shutdown."""
    await db_manager.close()