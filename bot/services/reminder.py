"""
Сервис автоматических напоминаний клиентам перед наступлением дня торжества (за 3 дня и за 1 день).
"""
import asyncio
import logging
from aiogram import Bot
from bot.database import db, Order
from bot.locales import get_text
from bot.utils.helpers import escape

logger = logging.getLogger(__name__)


class ReminderService:
    @staticmethod
    async def check_and_send_reminders(bot: Bot) -> None:
        """Проверяет заказы, дата которых наступает через 3 дня или 1 день, и отправляет напоминания."""
        for days in (3, 1):
            orders = await db.get_orders_due_soon(days_ahead=days)
            for order in orders:
                if not order.website_url:
                    continue

                user_lang = await db.get_user_language(order.telegram_id)
                days_word = f"{days} дня" if days == 3 else "1 день"
                days_word_uz = f"{days} kun" if days == 3 else "1 kun"

                if order.event_type == "birthday":
                    title = order.celebrant_name or "Tug‘ilgan kun"
                elif order.event_type == "sunnat":
                    title = order.celebrant_name or "Sunnat to‘yi"
                else:
                    title = f"{order.bride_name} & {order.groom_name}"

                if user_lang == "uz":
                    text = (
                        f"⏰ <b>Tantanangizga {days_word_uz} qoldi!</b> ✨\n\n"
                        f"<b>{escape(title)}</b>\n\n"
                        f"Bayramingiz ajoyib va unutilmas o‘tishini tilaymiz! 🎉\n"
                        f"Mehmonlarga yuborish uchun shaxsiy taklifnomangiz havolasi:\n"
                        f"🔗 <a href='{order.website_url}'>{order.website_url}</a>\n\n"
                        f"<i>TAKLIVO jamoasi siz bilan birga! ❤️</i>"
                    )
                else:
                    text = (
                        f"⏰ <b>До вашего торжества осталось {days_word}!</b> ✨\n\n"
                        f"<b>{escape(title)}</b>\n\n"
                        f"Желаем яркого, счастливого и незабываемого праздника! 🎉\n"
                        f"Ссылка на ваше онлайн-приглашение для гостей:\n"
                        f"🔗 <a href='{order.website_url}'>{order.website_url}</a>\n\n"
                        f"<i>С наилучшими пожеланиями, команда TAKLIVO ❤️</i>"
                    )

                try:
                    await bot.send_message(
                        chat_id=order.telegram_id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=False,
                    )
                    logger.info(f"Напоминание (за {days} дн.) отправлено клиенту #{order.telegram_id} по заказу #{order.id}")
                except Exception as e:
                    logger.warning(f"Не удалось отправить напоминание клиенту #{order.telegram_id}: {e}")

    @staticmethod
    async def check_and_send_promo_urgency_reminders(bot: Bot) -> None:
        """Проверяет пользователей, у которых до сгорания 50% скидки осталось <= 4 часов, и отправляет триггерное напоминание."""
        users = await db.get_users_needing_promo_reminder()
        for user in users:
            user_lang = user.language or "ru"
            text = get_text(user_lang, "promo_urgency_reminder_4h")
            try:
                from bot.keyboards.client import get_main_menu_keyboard
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=text,
                    reply_markup=get_main_menu_keyboard(lang=user_lang),
                    parse_mode="HTML",
                )
                await db.mark_promo_reminder_sent(user.telegram_id)
                logger.info(f"Напоминание о сгорании промокода отправлено пользователю #{user.telegram_id}")
            except Exception as e:
                logger.warning(f"Не удалось отправить напоминание о промокоде пользователю #{user.telegram_id}: {e}")

    @classmethod
    async def run_reminder_loop(cls, bot: Bot) -> None:
        """Фоновый периодический процесс проверки напоминаний о торжествах и сгорании скидок."""
        logger.info("Фоновый сервис напоминаний TAKLIVO запущен.")
        last_wedding_check = 0.0
        loop = asyncio.get_event_loop()
        while True:
            try:
                now_ts = loop.time()
                # Проверка приближающихся свадеб 1 раз в 12 часов (43200 сек)
                if now_ts - last_wedding_check >= 43200 or last_wedding_check == 0.0:
                    await cls.check_and_send_reminders(bot)
                    last_wedding_check = now_ts

                # Проверка сгорания 24-часовой скидки каждые 10 минут
                await cls.check_and_send_promo_urgency_reminders(bot)
            except Exception as e:
                logger.error(f"Ошибка в фоновом цикле напоминаний: {e}", exc_info=True)
            # Ожидание 10 минут между проверками сгорания скидок
            await asyncio.sleep(600)


reminder = ReminderService()
