"""
Сервис отправки уведомлений клиентам и администраторам TAKLIVO.
Изолирует работу с сообщениями, фото и обработку исключений Telegram API.
"""
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
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
    async def notify_admin_new_order(
        bot: Bot,
        order: Order,
        username: str | None = None,
        receipt_file_id: str | None = None,
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
        keyboard = get_admin_order_actions_keyboard(order.id, username=username)

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
        username: str | None = None,
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

    @staticmethod
    async def notify_client_payment_confirmed(
        bot: Bot,
        order: Order,
        lang: str = "ru",
    ) -> bool:
        """Уведомляет клиента об успешном подтверждении оплаты."""
        text = get_text(lang, "notify_payment_confirmed", order_id=order.id)
        try:
            await bot.send_message(
                chat_id=order.telegram_id,
                text=text,
                parse_mode="HTML",
            )
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to notify client #{order.telegram_id} of payment confirmation: {e}")
            return False

    @staticmethod
    async def notify_client_payment_rejected(
        bot: Bot,
        order: Order,
        lang: str = "ru",
    ) -> bool:
        """Уведомляет клиента об отклонении чека."""
        text = get_text(lang, "notify_payment_rejected", order_id=order.id, support_admin=config.SUPPORT_ADMIN)
        try:
            await bot.send_message(
                chat_id=order.telegram_id,
                text=text,
                parse_mode="HTML",
            )
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to notify client #{order.telegram_id} of payment rejection: {e}")
            return False

    @staticmethod
    async def notify_client_site_ready(
        bot: Bot,
        order: Order,
        website_url: str,
        lang: str = "ru",
    ) -> bool:
        """Отправляет клиенту ссылку на готовый сайт и кнопки проверки/правок."""
        text = get_text(
            lang,
            "notify_website_ready",
            bride_name=escape(order.bride_name),
            groom_name=escape(order.groom_name),
            website_url=website_url,
        )
        keyboard = get_client_website_review_keyboard(order.id, website_url, lang=lang)

        try:
            await bot.send_message(
                chat_id=order.telegram_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to send website URL to client #{order.telegram_id}: {e}")
            return False

    @staticmethod
    async def notify_admin_revision(
        bot: Bot,
        order: Order,
        revision_text: str,
        username: str | None = None,
    ) -> None:
        """Уведомляет администраторов о поступивших правках по заказу."""
        user_mention = f"@{escape(username)}" if username else "<i>(без @username)</i>"
        text = (
            f"✏️ <b>НОВЫЕ ПРАВКИ К ЗАКАЗУ #{order.id}</b>\n\n"
            f"👰🤵 <b>{escape(order.bride_name)} & {escape(order.groom_name)}</b>\n"
            f"👤 Клиент: {user_mention} (ID: <code>{order.telegram_id}</code>)\n"
            f"🌐 Сайт: {order.website_url or '—'}\n\n"
            f"<b>Текст пожеланий:</b>\n<i>{escape(revision_text)}</i>"
        )
        keyboard = get_admin_order_actions_keyboard(order.id, username=username)

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
