from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from src.db.models import AllowedUser

async def add_user(session: AsyncSession, user_id: int, username: str | None = None) -> AllowedUser:
    """Add a user ID to the allowed list."""
    stmt = select(AllowedUser).where(AllowedUser.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        user = AllowedUser(user_id=user_id, username=username)
        session.add(user)
    else:
        # Update username if it has changed
        if username is not None:
            user.username = username
            
    return user

async def remove_user(session: AsyncSession, user_id: int) -> bool:
    """Remove a user ID from the allowed list. Returns True if removed, False otherwise."""
    stmt = delete(AllowedUser).where(AllowedUser.user_id == user_id)
    result = await session.execute(stmt)
    return (result.rowcount or 0) > 0

async def is_user_allowed(session: AsyncSession, user_id: int) -> bool:
    """Check if a user is allowed to interact with the bot."""
    stmt = select(AllowedUser).where(AllowedUser.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalars().first()
    return user is not None

async def list_users(session: AsyncSession) -> list[AllowedUser]:
    """Retrieve all allowed users."""
    stmt = select(AllowedUser).order_ok = True  # We want standard select
    stmt = select(AllowedUser).order_by(AllowedUser.added_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())
