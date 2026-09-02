"""
Сервис бизнес-логики управления заказами TAKLIVO.
Обрабатывает все операции жизненного цикла заказа для всех типов торжеств (Свадьба, ДР, Суннат туй).
Включает начисление реферальных бонусов и учет скидок.
"""
import logging
from typing import Any, Optional
from aiogram import Bot
from bot.database import db, Order, OrderPhoto, OrderMusic, OrderStatus, PaymentStatus
from bot.locales import get_text
from bot.services.calculator import calculate_total
from bot.utils.helpers import format_currency, format_date_pretty, escape
from config import config

logger = logging.getLogger(__name__)


class OrderService:
    # --- Создание и получение заказов ---

    @staticmethod
    async def create_new_order(
        user_id: int,
        telegram_id: int,
        data: dict[str, Any],
    ) -> int:
        """Создает новый заказ в базе данных с учетом промокода и списания бонусов."""
        options = data.get("options", {})
        calc_res = calculate_total(options)
        event_type = data.get("event_type", "wedding")

        # Применение скидки промокода и бонусов
        discount_amount = data.get("discount_amount", 0)
        bonus_used = data.get("bonus_used", 0)
        final_price = max(calc_res.total_price - discount_amount - bonus_used, 0)
        promocode = data.get("promocode")

        order_id = await db.create_order(
            user_id=user_id,
            telegram_id=telegram_id,
            template_id=data.get("template_id", "luxury_gold"),
            template_name=data.get("template_name", "Luxury Gold"),
            plan="CUSTOM",
            event_type=event_type,
            bride_name=data.get("bride_name", ""),
            groom_name=data.get("groom_name", ""),
            celebrant_name=data.get("celebrant_name"),
            parents_name=data.get("parents_name"),
            age_or_details=data.get("age_or_details"),
            wedding_date=data.get("wedding_date", ""),
            wedding_time=data.get("wedding_time", ""),
            venue=data.get("venue", ""),
            address=data.get("address", ""),
            phone=data.get("phone", ""),
            rsvp_enabled=options.get("rsvp", False),
            map_enabled=options.get("map", True),
            music_enabled=options.get("music", False),
            gallery_enabled=options.get("gallery", False),
            dresscode_enabled=options.get("dresscode", False),
            schedule_enabled=options.get("schedule", False),
            second_language_enabled=options.get("second_language", False),
            total_price=final_price,
            promocode=promocode,
            discount_amount=discount_amount,
            bonus_used=bonus_used,
            status=OrderStatus.WAITING_PAYMENT.value,
        )

        # Сохраняем фото
        photos = data.get("photos", [])
        for photo in photos:
            await db.add_order_photo(order_id, photo["file_id"], photo.get("file_unique_id"))

        # Сохраняем музыку
        if data.get("music_file_id"):
            await db.set_order_music(order_id, data["music_file_id"], data.get("music_filename"))

        return order_id

    @staticmethod
    async def get_order_by_id(order_id: int) -> Optional[Order]:
        """Возвращает заказ по его ID."""
        return await db.get_order(order_id)

    @staticmethod
    async def get_user_orders_list(telegram_id: int) -> list[Order]:
        """Возвращает список всех заказов конкретного пользователя."""
        return await db.get_user_orders(telegram_id)

    @staticmethod
    async def get_orders_by_status_category(status: str, limit: int = 50) -> list[Order]:
        """Возвращает заказы по статусу."""
        if status == "ALL":
            return await db.get_recent_orders(limit=limit)
        return await db.get_orders_by_status(status, limit=limit)

    # --- Управление статусами и оплатой ---

    @staticmethod
    async def submit_payment_receipt(order_id: int, file_id: str) -> bool:
        """Сохраняет чек об оплате и переводит заказ на проверку."""
        order = await db.get_order(order_id)
        if not order:
            return False
        await db.set_order_receipt(order_id, file_id)
        return True

    @staticmethod
    async def confirm_order_payment(order_id: int, bot: Optional[Bot] = None) -> tuple[bool, Optional[Order]]:
        """Подтверждает оплату заказа, переводит в работу (IN_PROGRESS) и начисляет реферальный бонус пригласившему."""
        order = await db.get_order(order_id)
        if not order:
            return False, None

        await db.update_order_status(
            order_id=order_id,
            status=OrderStatus.IN_PROGRESS.value,
            payment_status=PaymentStatus.PAID.value,
        )
        updated = await db.get_order(order_id)

        # Проверяем, есть ли реферер у клиента
        async with aiosqlite_conn(db.db_path) as conn:
            cursor = await conn.execute("SELECT referrer_id FROM users WHERE telegram_id = ?", (order.telegram_id,))
            row = await cursor.fetchone()
            referrer_id = row[0] if row and row[0] else None

        if referrer_id and referrer_id != order.telegram_id:
            reward = config.REFERRAL_REWARD_BONUS
            new_balance = await db.add_user_bonus(referrer_id, reward)
            logger.info(f"Начислен реферальный бонус +{reward} пользователю {referrer_id} за заказ #{order_id}")

            if bot:
                try:
                    ref_lang = await db.get_user_language(referrer_id)
                    if ref_lang == "uz":
                        ref_text = (
                            f"🎉 <b>Do‘stingiz buyurtma berdi!</b>\n\n"
                            f"Sizga hamkorlik dasturi bo‘yicha <b>+{reward:,} so‘m</b> bonus taqdim etildi! ✨\n\n"
                            f"💰 <b>Joriy bonus balansingiz:</b> {new_balance:,} so‘m\n"
                            f"<i>Ushbu bonuslarni o‘zingizning keyingi buyurtmangizda chegirma sifatida ishlatishingiz mumkin!</i>"
                        )
                    else:
                        ref_text = (
                            f"🎉 <b>Ваш приглашенный друг оформил заказ!</b>\n\n"
                            f"Вам начислено <b>+{reward:,} бонусов</b> (сум) по партнерской программе! ✨\n\n"
                            f"💰 <b>Ваш бонусный баланс:</b> {new_balance:,} сум\n"
                            f"<i>Вы можете использовать эти бонусы для оплаты своего собственного сайта-приглашения!</i>"
                        )
                    await bot.send_message(chat_id=referrer_id, text=ref_text, parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"Не удалось отправить уведомление о бонусе рефереру {referrer_id}: {e}")

        return True, updated

    @staticmethod
    async def reject_order_payment(order_id: int) -> tuple[bool, Optional[Order]]:
        """Отклоняет оплату заказа и возвращает в статус WAITING_PAYMENT."""
        order = await db.get_order(order_id)
        if not order:
            return False, None
        await db.update_order_status(
            order_id=order_id,
            status=OrderStatus.WAITING_PAYMENT.value,
            payment_status=PaymentStatus.REJECTED.value,
        )
        updated = await db.get_order(order_id)
        return True, updated

    @staticmethod
    async def set_website_url_for_order(order_id: int, url: str) -> tuple[bool, Optional[Order]]:
        """Сохраняет URL готового сайта и переводит статус в PREVIEW."""
        order = await db.get_order(order_id)
        if not order:
            return False, None
        await db.set_order_website_url(order_id, url)
        updated = await db.get_order(order_id)
        return True, updated

    @staticmethod
    async def submit_revisions(order_id: int, revision_text: str) -> tuple[bool, Optional[Order]]:
        """Сохраняет текст правок от клиента и переводит статус в REVISION."""
        order = await db.get_order(order_id)
        if not order:
            return False, None
        await db.set_order_revision(order_id, revision_text)
        updated = await db.get_order(order_id)
        return True, updated

    @staticmethod
    async def complete_order(order_id: int) -> bool:
        """Переводит заказ в статус COMPLETED."""
        order = await db.get_order(order_id)
        if not order:
            return False
        await db.update_order_status(order_id, OrderStatus.COMPLETED.value)
        return True

    @staticmethod
    async def cancel_order(order_id: int) -> bool:
        """Отменяет заказ."""
        order = await db.get_order(order_id)
        if not order:
            return False
        await db.update_order_status(order_id, OrderStatus.CANCELLED.value)
        return True

    @staticmethod
    async def get_system_statistics() -> dict[str, Any]:
        """Возвращает общую статистику и финансовые показатели."""
        return await db.get_statistics()

    # --- Форматирование сообщений ---

    @staticmethod
    def format_order_preview(
        order_id: int | str,
        event_type: str,
        wedding_date: str,
        wedding_time: str,
        venue: str,
        address: str,
        phone: str,
        template_name: str,
        plan_name: str,
        options: dict[str, bool],
        photos_count: int,
        has_music: bool,
        total_price: int,
        bride_name: str = "",
        groom_name: str = "",
        celebrant_name: Optional[str] = None,
        parents_name: Optional[str] = None,
        age_or_details: Optional[str] = None,
        promocode: Optional[str] = None,
        discount_amount: int = 0,
        bonus_used: int = 0,
        lang: str = "ru",
    ) -> str:
        """Форматирует сводку заказа перед подтверждением клиентом."""
        features: list[str] = []
        if options.get("timer"):
            features.append("✅ " + get_text(lang, "option_timer"))
        if options.get("rsvp"):
            features.append("✅ " + get_text(lang, "option_rsvp"))
        if options.get("map"):
            features.append("✅ " + get_text(lang, "option_map"))
        if options.get("gallery"):
            features.append("✅ " + get_text(lang, "option_gallery"))
        if options.get("music"):
            features.append("✅ " + get_text(lang, "option_music"))
        if options.get("dresscode"):
            features.append("✅ " + get_text(lang, "option_dresscode"))
        if options.get("schedule"):
            features.append("✅ " + get_text(lang, "option_schedule"))
        if options.get("second_language"):
            features.append("✅ " + get_text(lang, "option_second_language"))

        features_str = "\n".join(features) if features else "—"
        music_status = ("✅ " + ("Yuklangan" if lang == "uz" else "Загружена")) if has_music else ("❌ " + ("Yuklanmagan" if lang == "uz" else "Не выбрана"))

        # Формируем блок главных персон в зависимости от типа торжества
        if event_type == "birthday":
            event_title = "🎂 Tug‘ilgan kun / Yubiley" if lang == "uz" else "🎂 День рождения / Юбилей"
            age_str = f" ({escape(age_or_details)})" if age_or_details and age_or_details != "-" else ""
            if lang == "uz":
                hero_info = f"🎂 <b>Tug‘ilgan kun sohibi:</b> {escape(celebrant_name or '')}{age_str}"
            else:
                hero_info = f"🎂 <b>Именинник / Юбиляр:</b> {escape(celebrant_name or '')}{age_str}"
        elif event_type == "sunnat":
            event_title = "✂️ Sunnat to‘yi" if lang == "uz" else "✂️ Суннат туй"
            parents_str = ""
            if parents_name and parents_name != "-":
                parents_label = "Ota-onasi:" if lang == "uz" else "Родители:"
                parents_str = f"\n👨‍👩‍👦 <b>{parents_label}</b> {escape(parents_name)}"
            if lang == "uz":
                hero_info = f"👦 <b>Bosh qahramon:</b> {escape(celebrant_name or '')}{parents_str}"
            else:
                hero_info = f"👦 <b>Виновник торжества:</b> {escape(celebrant_name or '')}{parents_str}"
        else:
            event_title = "💍 Nikoh to‘yi" if lang == "uz" else "💍 Свадьба"
            if lang == "uz":
                hero_info = f"👰 <b>Kelin:</b> {escape(bride_name)}\n🤵 <b>Kuyov:</b> {escape(groom_name)}"
            else:
                hero_info = f"👰 <b>Невеста:</b> {escape(bride_name)}\n🤵 <b>Жених:</b> {escape(groom_name)}"

        promo_line = ""
        if promocode and discount_amount > 0:
            promo_line += f"🎟 <b>Промокод ({escape(promocode)}):</b> -{format_currency(discount_amount, lang)}\n" if lang == "ru" else f"🎟 <b>Promokod ({escape(promocode)}):</b> -{format_currency(discount_amount, lang)}\n"
        if bonus_used > 0:
            promo_line += f"🎁 <b>Оплачено бонусами:</b> -{format_currency(bonus_used, lang)}\n" if lang == "ru" else f"🎁 <b>Bonuslar orqali to‘landi:</b> -{format_currency(bonus_used, lang)}\n"

        return get_text(
            lang,
            "preview_title",
            order_id=order_id,
            event_title=event_title,
            hero_info=hero_info,
            wedding_date=format_date_pretty(wedding_date, lang=lang),
            wedding_time=escape(wedding_time),
            venue=escape(venue),
            address=escape(address),
            phone=escape(phone),
            template_name=escape(template_name),
            features_list=features_str,
            photos_count=photos_count,
            music_status=music_status,
            promo_line=promo_line,
            total_price=format_currency(total_price, lang=lang),
        )

    @staticmethod
    def format_admin_notification(
        order: Order,
        username: Optional[str] = None,
        photos_count: int = 0,
        has_music: bool = False,
    ) -> str:
        """Форматирует подробное сообщение о заказе для администратора с указанием типа торжества."""
        features: list[str] = []
        if order.rsvp_enabled:
            features.append("➕ RSVP опрос")
        if order.map_enabled:
            features.append("➕ Карта проезда")
        if order.gallery_enabled:
            features.append(f"➕ Фотогалерея ({photos_count} фото)")
        if order.music_enabled:
            features.append("➕ Музыка" + (" (файл прикреплен)" if has_music else " (стандартная)"))
        if order.dresscode_enabled:
            features.append("➕ Дресс-код")
        if order.schedule_enabled:
            features.append("➕ Расписание")
        if order.second_language_enabled:
            features.append("➕ Второй язык")

        features_str = "\n".join(features) if features else "—"
        user_mention = f"@{escape(username)}" if username else "<i>(без @username)</i>"

        if order.event_type == "birthday":
            event_badge = "🎂 ДЕНЬ РОЖДЕНИЯ / ЮБИЛЕЙ"
            age_info = f" ({escape(order.age_or_details)})" if order.age_or_details and order.age_or_details != "-" else ""
            hero_block = f"🎂 <b>Именинник:</b> {escape(order.celebrant_name or '—')}{age_info}\n"
        elif order.event_type == "sunnat":
            event_badge = "✂️ СУННАТ ТУЙ / ХАТНА"
            parents_info = f"\n👨‍👩‍👦 <b>Родители:</b> {escape(order.parents_name)}" if order.parents_name and order.parents_name != "-" else ""
            hero_block = f"👦 <b>Мальчик:</b> {escape(order.celebrant_name or '—')}{parents_info}\n"
        else:
            event_badge = "💍 СВАДЬБА / NIKOH TO‘YI"
            hero_block = f"👰 <b>Невеста:</b> {escape(order.bride_name)}\n🤵 <b>Жених:</b> {escape(order.groom_name)}\n"

        promo_block = ""
        if order.promocode:
            promo_block += f"🎟 <b>Промокод:</b> <code>{escape(order.promocode)}</code> (Скидка: {format_currency(order.discount_amount, 'ru')})\n"
        if order.bonus_used > 0:
            promo_block += f"🎁 <b>Оплачено бонусами:</b> {format_currency(order.bonus_used, 'ru')}\n"

        return (
            f"🔔 <b>НОВЫЙ ЗАКАЗ #{order.id} [{event_badge}]</b>\n\n"
            f"{hero_block}\n"
            f"📅 <b>Дата:</b> {order.wedding_date} | 🕐 <b>Время:</b> {order.wedding_time}\n"
            f"🏰 <b>Место:</b> {escape(order.venue)}\n"
            f"📍 <b>Адрес:</b> {escape(order.address)}\n"
            f"📞 <b>Телефон:</b> {escape(order.phone)}\n\n"
            f"🎨 <b>Дизайн:</b> {escape(order.template_name)}\n\n"
            f"<b>Включенные опции:</b>\n{features_str}\n\n"
            f"{promo_block}"
            f"💰 <b>Сумма к оплате:</b> {format_currency(order.total_price, 'ru')}\n"
            f"📊 <b>Статус заказа:</b> <code>{order.status}</code>\n"
            f"💳 <b>Статус оплаты:</b> <code>{order.payment_status}</code>\n\n"
            f"👤 <b>Клиент:</b> {user_mention}\n"
            f"🆔 <b>Telegram ID:</b> <code>{order.telegram_id}</code>"
        )


def aiosqlite_conn(db_path: str):
    """Вспомогательный контекстный менеджер подключения к SQLite."""
    import aiosqlite
    return aiosqlite.connect(db_path)


order_service = OrderService()
