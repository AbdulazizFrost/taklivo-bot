"""
Сервис бизнес-логики управления заказами TAKLIVO.
Обрабатывает все операции жизненного цикла заказа.
"""
from typing import Any, Optional
from bot.database import db, Order, OrderPhoto, OrderMusic, OrderStatus, PaymentStatus
from bot.locales import get_text
from bot.services.calculator import calculate_total
from bot.utils.helpers import format_currency, format_date_pretty, escape


class OrderService:
    # --- Создание и получение заказов ---

    @staticmethod
    async def create_new_order(
        user_id: int,
        telegram_id: int,
        data: dict[str, Any],
    ) -> int:
        """Создает новый заказ в базе данных на основе выбранных в конструкторе опций."""
        options = data.get("options", {})
        calc_res = calculate_total(options)

        order_id = await db.create_order(
            user_id=user_id,
            telegram_id=telegram_id,
            template_id=data.get("template_id", "luxury_gold"),
            template_name=data.get("template_name", "Luxury Gold"),
            plan="CUSTOM",
            bride_name=data.get("bride_name", ""),
            groom_name=data.get("groom_name", ""),
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
            total_price=calc_res.total_price,
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
    async def confirm_order_payment(order_id: int) -> tuple[bool, Optional[Order]]:
        """Подтверждает оплату заказа и переводит в работу (IN_PROGRESS)."""
        order = await db.get_order(order_id)
        if not order:
            return False, None
        await db.update_order_status(
            order_id=order_id,
            status=OrderStatus.IN_PROGRESS.value,
            payment_status=PaymentStatus.PAID.value,
        )
        updated = await db.get_order(order_id)
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
        bride_name: str,
        groom_name: str,
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

        return get_text(
            lang,
            "preview_title",
            order_id=order_id,
            bride_name=escape(bride_name),
            groom_name=escape(groom_name),
            wedding_date=format_date_pretty(wedding_date, lang=lang),
            wedding_time=escape(wedding_time),
            venue=escape(venue),
            address=escape(address),
            phone=escape(phone),
            template_name=escape(template_name),
            features_list=features_str,
            photos_count=photos_count,
            music_status=music_status,
            total_price=format_currency(total_price, lang=lang),
        )

    @staticmethod
    def format_admin_notification(
        order: Order,
        username: Optional[str] = None,
        photos_count: int = 0,
        has_music: bool = False,
    ) -> str:
        """Форматирует подробное сообщение о заказе для администратора."""
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

        return (
            f"🔔 <b>ЗАКАЗ #{order.id}</b>\n\n"
            f"👰 <b>Невеста:</b> {escape(order.bride_name)}\n"
            f"🤵 <b>Жених:</b> {escape(order.groom_name)}\n\n"
            f"📅 <b>Дата:</b> {order.wedding_date} | 🕐 <b>Время:</b> {order.wedding_time}\n"
            f"🏰 <b>Место:</b> {escape(order.venue)}\n"
            f"📍 <b>Адрес:</b> {escape(order.address)}\n"
            f"📞 <b>Телефон:</b> {escape(order.phone)}\n\n"
            f"🎨 <b>Дизайн:</b> {escape(order.template_name)}\n\n"
            f"<b>Включенные опции:</b>\n{features_str}\n\n"
            f"💰 <b>Сумма:</b> {format_currency(order.total_price, 'ru')}\n"
            f"📊 <b>Статус заказа:</b> <code>{order.status}</code>\n"
            f"💳 <b>Статус оплаты:</b> <code>{order.payment_status}</code>\n\n"
            f"👤 <b>Клиент:</b> {user_mention}\n"
            f"🆔 <b>Telegram ID:</b> <code>{order.telegram_id}</code>"
        )


order_service = OrderService()
