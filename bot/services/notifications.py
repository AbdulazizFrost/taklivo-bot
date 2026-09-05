"""
Сервис отправки уведомлений клиентам и администраторам TAKLIVO.
Изолирует работу с сообщениями, фото и обработку исключений Telegram API.
Поддерживает многоязычность (автоматическое определение UZ/RU) и совместимость сигнатур.
"""
import logging
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.database import db
from bot.database.models import Order
from bot.keyboards.admin import get_admin_order_actions_keyboard
from bot.keyboards.client import get_client_website_review_keyboard
from bot.locales import get_text
from bot.services.order_service import order_service
from bot.utils.helpers import escape, format_currency
from config import config

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    async def _resolve_lang(telegram_id: int, lang: Optional[str] = None) -> str:
        """Определяет язык пользователя: переданный явно -> язык из БД -> fallback 'ru'."""
        if lang:
            return lang
        try:
            return await db.get_user_language(telegram_id)
        except Exception:
            return "ru"

    @staticmethod
    async def notify_admin_new_order(
        bot: Bot,
        order: Order,
        username: Optional[str] = None,
        receipt_file_id: Optional[str] = None,
        photos_count: int = 0,
        has_music: bool = False,
    ) -> None:
        """Отправляет администраторам уведомление о новом заказе и чек."""
        text = order_service.format_admin_notification(
            order=order,
            username=username,
            photos_count=photos_count,
            has_music=has_music,
        )
        keyboard = get_admin_order_actions_keyboard(order)

        for admin_id in config.ADMIN_IDS:
            try:
                if receipt_file_id:
                    await bot.send_photo(
                        chat_id=admin_id,
                        photo=receipt_file_id,
                        caption=f"🧾 <b>Чек к заказу #{order.id}</b>\n\n" + text,
                        reply_markup=keyboard,
                        parse_mode="HTML",
                    )
                else:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="HTML",
                    )
                logger.info(f"Admin #{admin_id} notified of order #{order.id}")
            except TelegramAPIError as e:
                logger.error(f"Failed to notify admin #{admin_id} of order #{order.id}: {e}")

    @classmethod
    async def notify_admin_payment(
        cls,
        bot: Bot,
        order: Order,
        receipt_file_id: str,
        username: Optional[str] = None,
        photos_count: int = 0,
        has_music: bool = False,
    ) -> None:
        """Алиас для отправки чека администратору."""
        await cls.notify_admin_new_order(
            bot=bot,
            order=order,
            username=username,
            receipt_file_id=receipt_file_id,
            photos_count=photos_count,
            has_music=has_music,
        )

    @classmethod
    async def notify_client_payment_confirmed(
        cls,
        bot: Bot,
        order: Optional[Order] = None,
        order_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Уведомляет клиента об успешном подтверждении оплаты.
        Поддерживает вызов как через объект order, так и через order_id/telegram_id.
        """
        if not order and order_id:
            order = await db.get_order(order_id)

        target_tg_id = telegram_id or (order.telegram_id if order else None)
        target_order_id = order_id or (order.id if order else 0)

        if not target_tg_id:
            logger.error("notify_client_payment_confirmed: telegram_id не определен")
            return False

        user_lang = await cls._resolve_lang(target_tg_id, lang)
        text = get_text(user_lang, "notify_payment_confirmed", order_id=target_order_id)

        reply_markup = None
        if order and order.website_url:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=get_text(user_lang, "btn_open_website"), url=order.website_url)]
                ]
            )

        try:
            await bot.send_message(
                chat_id=target_tg_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to notify client #{target_tg_id} of payment confirmation: {e}")
            return False

    @classmethod
    async def notify_client_payment_rejected(
        cls,
        bot: Bot,
        order: Optional[Order] = None,
        order_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Уведомляет клиента об отклонении чека.
        Поддерживает вызов как через объект order, так и через order_id/telegram_id.
        """
        if not order and order_id:
            order = await db.get_order(order_id)

        target_tg_id = telegram_id or (order.telegram_id if order else None)
        target_order_id = order_id or (order.id if order else 0)

        if not target_tg_id:
            logger.error("notify_client_payment_rejected: telegram_id не определен")
            return False

        user_lang = await cls._resolve_lang(target_tg_id, lang)
        text = get_text(
            user_lang,
            "notify_payment_rejected",
            order_id=target_order_id,
            support_admin=config.SUPPORT_ADMIN,
        )

        try:
            await bot.send_message(
                chat_id=target_tg_id,
                text=text,
                parse_mode="HTML",
            )
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to notify client #{target_tg_id} of payment rejection: {e}")
            return False

    @classmethod
    async def notify_client_site_ready(
        cls,
        bot: Bot,
        order: Optional[Order] = None,
        website_url: str = "",
        order_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Отправляет клиенту ссылку на готовый сайт и кнопки проверки/правок.
        Поддерживает вызов как через объект order, так и через telegram_id / order_id.
        """
        if not order and order_id:
            order = await db.get_order(order_id)

        target_tg_id = telegram_id or (order.telegram_id if order else None)
        target_order_id = order_id or (order.id if order else 0)

        if not target_tg_id:
            logger.error("notify_client_site_ready: telegram_id не определен")
            return False

        user_lang = await cls._resolve_lang(target_tg_id, lang)

        hero_title = "Taklifnoma"
        if order:
            if order.event_type == "birthday":
                hero_title = order.celebrant_name or "Tug‘ilgan kun"
            elif order.event_type == "sunnat":
                hero_title = order.celebrant_name or "Sunnat to‘y"
            else:
                hero_title = f"{order.bride_name} & {order.groom_name}"

        total_price_str = format_currency(order.total_price, lang=user_lang) if order else ""
        text = get_text(
            user_lang,
            "notify_website_ready",
            hero_title=escape(hero_title),
            website_url=website_url,
            total_price=total_price_str,
        )
        keyboard = get_client_website_review_keyboard(
            order or target_order_id,
            website_url,
            lang=user_lang,
            is_paid=(order.payment_status == "PAID" or order.total_price == 0) if order else None,
            total_price=order.total_price if order else 0,
        )

        try:
            await bot.send_message(
                chat_id=target_tg_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to send website URL to client #{target_tg_id}: {e}")
            return False

    # Алиас для полной обратной совместимости
    notify_client_website_ready = notify_client_site_ready

    @staticmethod
    async def notify_admin_revision(
        bot: Bot,
        order: Order,
        revision_text: str,
        username: Optional[str] = None,
    ) -> None:
        """Уведомляет администраторов о поступивших правках по заказу."""
        user_mention = f"@{escape(username)}" if username else "<i>(без @username)</i>"
        if order.event_type == "birthday":
            hero_title = f"🎂 <b>{escape(order.celebrant_name or 'Именинник')}</b>"
        elif order.event_type == "sunnat":
            hero_title = f"✂️ <b>{escape(order.celebrant_name or 'Мальчик')}</b>"
        else:
            hero_title = f"👰🤵 <b>{escape(order.bride_name)} & {escape(order.groom_name)}</b>"

        text = (
            f"✏️ <b>НОВЫЕ ПРАВКИ К ЗАКАЗУ #{order.id}</b>\n\n"
            f"{hero_title}\n"
            f"👤 Клиент: {user_mention} (ID: <code>{order.telegram_id}</code>)\n"
            f"🌐 Сайт: {order.website_url or '—'}\n\n"
            f"<b>Текст пожеланий:</b>\n<i>{escape(revision_text)}</i>"
        )
        keyboard = get_admin_order_actions_keyboard(order)

        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            except TelegramAPIError as e:
                logger.error(f"Failed to alert admin #{admin_id} of revision for order #{order.id}: {e}")


notifications = NotificationService()
