import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat, User, CallbackQuery
from src.bot.middlewares.auth import AllowedUserMiddleware
from src.config import SUPER_ADMIN_ID
from src.db.models import AllowedUser

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_handler():
    return AsyncMock()

@pytest.fixture
def mock_message():
    message = MagicMock(spec=Message)
    message.chat = MagicMock(spec=Chat)
    message.chat.type = "private"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 999
    message.from_user.username = "test_user"
    message.text = None
    message.answer = AsyncMock()
    return message

async def test_middleware_allows_super_admin(mock_message, mock_handler):
    # GIVEN: A message from the Super Admin
    mock_message.from_user.id = SUPER_ADMIN_ID
    middleware = AllowedUserMiddleware()
    
    # WHEN: Calling the middleware
    await middleware(mock_handler, mock_message, {})
    
    # THEN: The handler should be called
    mock_handler.assert_called_once_with(mock_message, {})
    mock_message.answer.assert_not_called()

async def test_middleware_allows_allowed_user(mock_message, mock_handler, test_session, monkeypatch):
    # GIVEN: An allowed user in the database
    user_id = 555
    mock_message.from_user.id = user_id
    
    # Mock database session creator in auth middleware to return our test_session
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=test_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock()
    monkeypatch.setattr("src.bot.middlewares.auth.async_session_maker", mock_session_maker)
    
    # Add user to database
    from src.db.repository import add_user
    await add_user(test_session, user_id, "allowed_user")
    await test_session.commit()
    
    middleware = AllowedUserMiddleware()
    
    # WHEN: Calling the middleware
    await middleware(mock_handler, mock_message, {})
    
    # THEN: The handler should be called
    mock_handler.assert_called_once_with(mock_message, {})
    mock_message.answer.assert_not_called()

async def test_middleware_blocks_unauthorized_private_chat(mock_message, mock_handler, test_session, monkeypatch):
    # GIVEN: A user not in the database and not Super Admin
    mock_message.from_user.id = 8888
    mock_message.chat.type = "private"
    
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=test_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock()
    monkeypatch.setattr("src.bot.middlewares.auth.async_session_maker", mock_session_maker)
    
    middleware = AllowedUserMiddleware()
    
    # WHEN: Calling the middleware
    await middleware(mock_handler, mock_message, {})
    
    # THEN: The handler should NOT be called
    mock_handler.assert_not_called()
    
    # AND: An answer should be sent back telling them they are unauthorized
    mock_message.answer.assert_called_once()
    args, kwargs = mock_message.answer.call_args
    assert "not authorized" in args[0]
    assert "8888" in args[0]

async def test_middleware_blocks_unauthorized_group_chat_silently(mock_message, mock_handler, test_session, monkeypatch):
    # GIVEN: A user not in the database and not Super Admin, in a group chat
    mock_message.from_user.id = 8888
    mock_message.chat.type = "group"
    
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=test_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock()
    monkeypatch.setattr("src.bot.middlewares.auth.async_session_maker", mock_session_maker)
    
    middleware = AllowedUserMiddleware()
    
    # WHEN: Calling the middleware
    await middleware(mock_handler, mock_message, {})
    
    # THEN: The handler should NOT be called
    mock_handler.assert_not_called()
    
    # AND: It should be silently ignored (no answer sent)
    mock_message.answer.assert_not_called()

async def test_middleware_allows_request_command_even_for_unauthorized(mock_message, mock_handler):
    # GIVEN: An unauthorized user sending /request command
    mock_message.from_user.id = 8888
    mock_message.text = "/request access"
    middleware = AllowedUserMiddleware()
    
    # WHEN: Calling the middleware
    await middleware(mock_handler, mock_message, {})
    
    # THEN: The handler should be allowed to proceed
    mock_handler.assert_called_once_with(mock_message, {})
    mock_message.answer.assert_not_called()

async def test_cmd_request_sends_msg_to_admin(mock_message, test_session, monkeypatch):
    # GIVEN: Mock bot send_message
    mock_message.from_user.id = 7777
    mock_message.from_user.username = "requester"
    mock_message.from_user.full_name = "Requester Full Name"
    mock_message.bot = MagicMock()
    mock_message.bot.send_message = AsyncMock()
    
    # Mock db connection inside handler
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=test_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock()
    monkeypatch.setattr("src.bot.handlers.start.async_session_maker", mock_session_maker)
    
    from src.bot.handlers.start import cmd_request
    
    # WHEN: Triggering the request handler
    await cmd_request(mock_message)
    
    # THEN: Message should be sent to Super Admin
    mock_message.bot.send_message.assert_called_once()
    args, kwargs = mock_message.bot.send_message.call_args
    assert kwargs["chat_id"] == SUPER_ADMIN_ID
    assert "7777" in kwargs["text"]
    assert "requester" in kwargs["text"]
    
    # AND: User should receive a confirmation reply
    mock_message.answer.assert_called_once_with("📨 Your request for access has been sent to the administrator.")

async def test_handle_callback_allow(test_session, monkeypatch):
    # GIVEN: A mock CallbackQuery
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.data = "admin_allow:6666"
    callback_query.message = MagicMock()
    callback_query.message.text = "🔔 Access Request:\nUser: Requester (@requester_username)\nUser ID: 6666"
    callback_query.message.edit_text = AsyncMock()
    callback_query.bot = MagicMock()
    callback_query.bot.send_message = AsyncMock()
    callback_query.answer = AsyncMock()
    
    # Mock database session creator in admin callback handler
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=test_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock()
    monkeypatch.setattr("src.bot.handlers.admin.async_session_maker", mock_session_maker)
    
    from src.bot.handlers.admin import handle_callback_allow, list_users
    
    # WHEN: Handling the allow callback
    await handle_callback_allow(callback_query)
    
    # THEN: User should be in database
    users = await list_users(test_session)
    user_ids = {u.user_id for u in users}
    assert 6666 in user_ids
    
    # AND: Requester should be notified
    callback_query.bot.send_message.assert_called_once_with(
        chat_id=6666,
        text="🎉 <b>Access Granted!</b> You can now use the bot. Send me any supported video link!"
    )
    
    # AND: Admin message should be updated
    callback_query.message.edit_text.assert_called_once()
    edit_args, edit_kwargs = callback_query.message.edit_text.call_args
    assert "Allowed user" in edit_args[0]
    assert "6666" in edit_args[0]
    assert "requester_username" in edit_args[0]
    
    # AND: Callback query answered
    callback_query.answer.assert_called_once_with("User allowed.")

async def test_handle_callback_deny(test_session, monkeypatch):
    # GIVEN: A mock CallbackQuery for deny
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.data = "admin_deny:6666"
    callback_query.message = MagicMock()
    callback_query.message.text = "🔔 Access Request:\nUser: Requester (@requester_username)\nUser ID: 6666"
    callback_query.message.edit_text = AsyncMock()
    callback_query.bot = MagicMock()
    callback_query.bot.send_message = AsyncMock()
    callback_query.answer = AsyncMock()
    
    from src.bot.handlers.admin import handle_callback_deny, list_users
    
    # WHEN: Handling the deny callback
    await handle_callback_deny(callback_query)
    
    # THEN: User should NOT be added to database
    users = await list_users(test_session)
    assert len(users) == 0
    
    # AND: Requester should be notified of denial
    callback_query.bot.send_message.assert_called_once_with(
        chat_id=6666,
        text="❌ Your access request was denied by the administrator."
    )
    
    # AND: Admin message should be updated
    callback_query.message.edit_text.assert_called_once()
    edit_args, edit_kwargs = callback_query.message.edit_text.call_args
    assert "Denied user" in edit_args[0]
    assert "6666" in edit_args[0]
    assert "requester_username" in edit_args[0]
    
    # AND: Callback query answered
    callback_query.answer.assert_called_once_with("User denied.")

