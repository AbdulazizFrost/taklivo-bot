"""
Сервис массовой рассылки сообщений по всей базе пользователей TAKLIVO.
Поддерживает рассылку текста, фото с подписью и инлайн-кнопок со ссылками.
Включает защиту от блокировок Telegram API (Rate Limiting).
"""
import asyncio
import logging
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramAPIError
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.database import db

logger = logging.getLogger(__name__)


class BroadcasterService:
    @staticmethod
    async def run_broadcast(
        bot: Bot,
        source_message: Message,
        button_text: Optional[str] = None,
        button_url: Optional[str] = None,
    ) -> dict[str, int]:
        """
        Выполняет рассылку сообщения всем зарегистрированным пользователям.
        Возвращает статистику доставки: total, sent, blocked, failed.
        """
        users = await db.get_all_users()
        total = len(users)
        sent = 0
        blocked = 0
        failed = 0

        # Формируем клавиатуру, если передана кнопка
        keyboard: Optional[InlineKeyboardMarkup] = None
        if button_text and button_url:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=button_text, url=button_url)]]
            )

        logger.info(f"Запуск рассылки по {total} пользователям...")

        for user in users:
            try:
                # Если отправлено фото
                if source_message.photo:
                    photo_id = source_message.photo[-1].file_id
                    await bot.send_photo(
                        chat_id=user.telegram_id,
                        photo=photo_id,
                        caption=source_message.caption or "",
                        caption_entities=source_message.caption_entities,
                        reply_markup=keyboard,
                    )
                # Если обычный текст
                elif source_message.text:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=source_message.text,
                        entities=source_message.entities,
                        reply_markup=keyboard,
                        disable_web_page_preview=False,
                    )
                sent += 1
            except TelegramForbiddenError:
                # Пользователь заблокировал бота
                blocked += 1
            except TelegramRetryAfter as e:
                # Превышен лимит сообщений, ожидаем требуемое время
                logger.warning(f"Telegram Flood Limit: сон на {e.retry_after} сек.")
                await asyncio.sleep(e.retry_after)
                try:
                    if source_message.photo:
                        await bot.send_photo(
                            chat_id=user.telegram_id,
                            photo=source_message.photo[-1].file_id,
                            caption=source_message.caption or "",
                            reply_markup=keyboard,
                        )
                    elif source_message.text:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=source_message.text,
                            reply_markup=keyboard,
                        )
                    sent += 1
                except Exception:
                    failed += 1
            except TelegramAPIError as e:
                logger.error(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
                failed += 1
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при рассылке пользователю {user.telegram_id}: {e}")
                failed += 1

            # Пауза 40 мс (~25 сообщений в секунду для стабильности)
            await asyncio.sleep(0.04)

        logger.info(f"Рассылка завершена: Total={total}, Sent={sent}, Blocked={blocked}, Failed={failed}")
        return {
            "total": total,
            "sent": sent,
            "blocked": blocked,
            "failed": failed,
        }


broadcaster = BroadcasterService()
