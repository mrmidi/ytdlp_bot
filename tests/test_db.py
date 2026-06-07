import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.db.repository import add_user, remove_user, is_user_allowed, list_users
from src.db.connection import seed_super_admin, async_session_maker
from src.db.models import AllowedUser
from sqlalchemy import select

pytestmark = pytest.mark.asyncio


async def test_add_and_check_user(test_session: AsyncSession):
    # GIVEN: A user ID and username
    user_id = 12345
    username = "test_user"
    
    # WHEN: Adding the user
    user = await add_user(test_session, user_id, username)
    await test_session.commit()
    
    # THEN: The user should be returned and saved
    assert user.user_id == user_id
    assert user.username == username
    
    # AND: The check function should confirm the user is allowed
    is_allowed = await is_user_allowed(test_session, user_id)
    assert is_allowed is True

async def test_remove_user(test_session: AsyncSession):
    # GIVEN: A user added to the database
    user_id = 12345
    await add_user(test_session, user_id, "to_be_deleted")
    await test_session.commit()
    
    # WHEN: Removing the user
    removed = await remove_user(test_session, user_id)
    await test_session.commit()
    
    # THEN: The removal should return True
    assert removed is True
    
    # AND: The check function should confirm they are no longer allowed
    is_allowed = await is_user_allowed(test_session, user_id)
    assert is_allowed is False

async def test_remove_nonexistent_user(test_session: AsyncSession):
    # WHEN: Removing a user that doesn't exist
    removed = await remove_user(test_session, 99999)
    await test_session.commit()
    
    # THEN: The removal should return False
    assert removed is False

async def test_list_users(test_session: AsyncSession):
    # GIVEN: Multiple users added
    await add_user(test_session, 1, "user1")
    await add_user(test_session, 2, "user2")
    await test_session.commit()
    
    # WHEN: Listing all users
    users = await list_users(test_session)
    
    # THEN: Both users should be in the list
    assert len(users) == 2
    user_ids = {u.user_id for u in users}
    assert user_ids == {1, 2}

async def test_seed_super_admin(test_engine, monkeypatch):
    # GIVEN: Mock the global async_session_maker with our test engine's session maker
    test_session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    monkeypatch.setattr("src.db.connection.async_session_maker", test_session_maker)
    
    admin_id = 1150695
    
    # WHEN: Seeding the super admin
    await seed_super_admin(admin_id)
    
    # THEN: The admin should exist in the database
    async with test_session_maker() as session:
        stmt = select(AllowedUser).where(AllowedUser.user_id == admin_id)
        res = await session.execute(stmt)
        user = res.scalars().first()
        assert user is not None
        assert user.user_id == admin_id
        assert user.username == "super_admin"
        
    # AND: Re-running seed_super_admin should not fail or create duplicate
    await seed_super_admin(admin_id)
