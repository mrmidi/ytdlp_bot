import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.db.models import Base

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_engine():
    """Create an in-memory async database engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    # Clean up connections
    await engine.dispose()

@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncSession:
    """Create a new session for each test function."""
    session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
