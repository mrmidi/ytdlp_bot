import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import DB_URL
from src.db.models import Base, AllowedUser
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Create the async engine
# Note: sqlite+aiosqlite is used for asynchronous SQLite support
engine = create_async_engine(DB_URL, echo=False)

# Session factory for generating AsyncSession instances
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

async def init_db() -> None:
    """Initialize the database tables."""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_super_admin(admin_id: int) -> None:
    """Ensure the super admin user is seeded in the allowed users table."""
    logger.info(f"Seeding super admin user ID: {admin_id}")
    async with async_session_maker() as session:
        async with session.begin():
            # Check if user already exists
            stmt = select(AllowedUser).where(AllowedUser.user_id == admin_id)
            result = await session.execute(stmt)
            existing_user = result.scalars().first()
            
            if not existing_user:
                admin_user = AllowedUser(user_id=admin_id, username="super_admin")
                session.add(admin_user)
                logger.info(f"Super admin user ID {admin_id} successfully seeded.")
            else:
                logger.info(f"Super admin user ID {admin_id} already exists in database.")
