"""
Клавиатуры для панели администратора TAKLIVO.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.models import Order, PromoCode


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура панели администратора."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ На проверке оплаты", callback_data="adm_filter:PAYMENT_REVIEW"),
                InlineKeyboardButton(text="🔨 В работе у дизайнера", callback_data="adm_filter:IN_PROGRESS"),
            ],
            [
                InlineKeyboardButton(text="👀 На проверке клиентом", callback_data="adm_filter:PREVIEW"),
                InlineKeyboardButton(text="✏️ С правками", callback_data="adm_filter:REVISION"),
            ],
            [
                InlineKeyboardButton(text="🎉 Завершённые", callback_data="adm_filter:COMPLETED"),
                InlineKeyboardButton(text="📋 Все заказы", callback_data="adm_filter:ALL"),
            ],
            [
                InlineKeyboardButton(text="📢 Массовая рассылка", callback_data="adm:broadcast"),
                InlineKeyboardButton(text="🎟 Промокоды", callback_data="adm:promos"),
            ],
            [
                InlineKeyboardButton(text="👥 Пользователи бота", callback_data="adm:users"),
                InlineKeyboardButton(text="📊 Аналитика и выручка", callback_data="adm:stats"),
            ],
            [
                InlineKeyboardButton(text="📥 Скачать базу (Excel)", callback_data="adm:export_excel"),
                InlineKeyboardButton(text="💾 Скачать бэкап БД", callback_data="adm:backup_db"),
            ],
            [InlineKeyboardButton(text="🔄 Обновить панель", callback_data="adm:refresh")],
        ]
    )


def get_admin_order_actions_keyboard(order: Order) -> InlineKeyboardMarkup:
    """Кнопки управления конкретным заказом в админке."""
    buttons = []

    # Если чек на проверке
    if order.status == "PAYMENT_REVIEW" or order.payment_status == "REVIEW":
        buttons.append([
            InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"adm_pay_ok:{order.id}"),
            InlineKeyboardButton(text="❌ Отклонить оплату", callback_data=f"adm_pay_rej:{order.id}"),
        ])

    # Если заказ оплачен / в работе / на проверке
    if order.status in ("IN_PROGRESS", "REVISION", "PREVIEW", "PAID"):
        buttons.append([
            InlineKeyboardButton(text="🌐 Отправить ссылку на сайт", callback_data=f"adm_send_url:{order.id}"),
        ])

    # Просмотр медиа и экспорт
    media_row = []
    if order.gallery_enabled:
        media_row.append(InlineKeyboardButton(text="📸 Фото заказа", callback_data=f"adm_view_photos:{order.id}"))
    if order.payment_receipt_file_id:
        media_row.append(InlineKeyboardButton(text="🧾 Показать чек", callback_data=f"adm_view_receipt:{order.id}"))
    if media_row:
        buttons.append(media_row)

    buttons.append([
        InlineKeyboardButton(text="📄 Получить JSON", callback_data=f"adm_export_json:{order.id}"),
        InlineKeyboardButton(text="✉️ Написать клиенту", callback_data=f"adm_msg_client:{order.id}"),
    ])

    buttons.append([
        InlineKeyboardButton(text="⚙️ Изменить статус", callback_data=f"adm_change_st:{order.id}"),
        InlineKeyboardButton(text="⬅️ К списку заказов", callback_data="adm:back_to_list"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_status_selection_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Выбор нового статуса для заказа."""
    statuses = [
        ("💳 Ожидает оплаты", "WAITING_PAYMENT"),
        ("⏳ Чек на проверке", "PAYMENT_REVIEW"),
        ("✅ Оплачен", "PAID"),
        ("🔨 В работе", "IN_PROGRESS"),
        ("👀 На проверке", "PREVIEW"),
        ("✏️ С правками", "REVISION"),
        ("🎉 Завершён", "COMPLETED"),
        ("❌ Отменён", "CANCELLED"),
    ]
    buttons = []
    for label, st in statuses:
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"set_st:{order_id}:{st}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к заказу", callback_data=f"adm_order:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_orders_list_keyboard(orders: list[Order], current_filter: str = "ALL") -> InlineKeyboardMarkup:
    """Список заказов в админке."""
    buttons = []
    for order in orders:
        if order.event_type == "birthday":
            title = f"🎂 {order.celebrant_name or 'ДР'}"
        elif order.event_type == "sunnat":
            title = f"✂️ {order.celebrant_name or 'Суннат туй'}"
        else:
            title = f"💍 {order.bride_name} & {order.groom_name}"

        btn_text = f"#{order.id} | {title} | {order.total_price:,} сум"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"adm_order:{order.id}")
        ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ В главное меню админки", callback_data="adm:main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_back_keyboard(order_id: int | None = None) -> InlineKeyboardMarkup:
    """Кнопка возврата в админке."""
    back_callback = f"adm_order:{order_id}" if order_id else "adm:main"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)]
        ]
    )


def get_admin_users_keyboard() -> InlineKeyboardMarkup:
    """Кнопки в разделе списка пользователей."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Скачать базу (Excel)", callback_data="adm:export_excel")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="adm:users")],
            [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="adm:main")],
        ]
    )


def get_admin_promos_keyboard(promos: list[PromoCode]) -> InlineKeyboardMarkup:
    """Список промокодов в админке."""
    buttons = [
        [InlineKeyboardButton(text="➕ Создать промокод", callback_data="adm_promo:create")]
    ]
    for p in promos:
        discount_label = f"{p.discount_percent}%" if p.discount_percent > 0 else f"{p.discount_amount:,} сум"
        btn_text = f"🎟 {p.code} ({discount_label}) — {p.used_count}/{p.max_uses} исп."
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"adm_promo_view:{p.id}")
        ])
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="adm:main")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_promo_card_keyboard(promo_id: int) -> InlineKeyboardMarkup:
    """Кнопки управления отдельным промокодом."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить промокод", callback_data=f"adm_promo_del:{promo_id}")],
            [InlineKeyboardButton(text="⬅️ К списку промокодов", callback_data="adm:promos")],
        ]
    )


def get_admin_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Кнопки подтверждения запуска рассылки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Запустить рассылку", callback_data="adm_bc:confirm")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="adm:main")],
        ]
    )
