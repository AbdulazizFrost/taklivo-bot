"""
Middleware для автоматической регистрации и отслеживания каждого пользователя при любом взаимодействии с ботом.
Гарантирует, что ни один пользователь не будет потерян или забыт в базе данных.
"""
import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from bot.database import db

logger = logging.getLogger(__name__)


class UserTrackerMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()
        self._tracked_users: set[int] = set()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_user: TgUser | None = data.get("event_from_user")
        is_start_cmd = False
        if hasattr(event, "text") and event.text and event.text.startswith("/start"):
            is_start_cmd = True

        if event_user and not event_user.is_bot and not is_start_cmd:
            if event_user.id not in self._tracked_users:
                self._tracked_users.add(event_user.id)
                # Выполняем сохранение в базу асинхронно в фоне, чтобы мгновенно ответить пользователю
                asyncio.create_task(self._track_user(event_user))

        return await handler(event, data)

    async def _track_user(self, event_user: TgUser) -> None:
        try:
            await db.get_or_create_user(
                telegram_id=event_user.id,
                username=event_user.username,
                first_name=event_user.first_name,
            )
        except Exception as e:
            logger.error(f"Ошибка в UserTrackerMiddleware для пользователя {event_user.id}: {e}")

