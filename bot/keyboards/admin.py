"""
Клавиатуры для панели администратора TAKLIVO.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.models import Order


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
                InlineKeyboardButton(text="👥 Пользователи бота", callback_data="adm:users"),
                InlineKeyboardButton(text="📊 Аналитика и выручка", callback_data="adm:stats"),
            ],
            [
                InlineKeyboardButton(text="💾 Скачать бэкап БД", callback_data="adm:backup_db"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="adm:refresh"),
            ],
        ]
    )


def get_admin_users_keyboard() -> InlineKeyboardMarkup:
    """Кнопки в разделе списка пользователей."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="adm:users")],
            [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="adm:main")],
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
        InlineKeyboardButton(text="⚙️ Сменить статус", callback_data=f"adm_change_st:{order.id}"),
        InlineKeyboardButton(text="⬅️ К списку заказов", callback_data="adm:back_to_list"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_status_selection_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Выбор статуса для ручной смены."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Ожидает оплаты", callback_data=f"set_st:{order_id}:WAITING_PAYMENT"),
                InlineKeyboardButton(text="🔨 В работе", callback_data=f"set_st:{order_id}:IN_PROGRESS"),
            ],
            [
                InlineKeyboardButton(text="👀 На проверке", callback_data=f"set_st:{order_id}:PREVIEW"),
                InlineKeyboardButton(text="✏️ Правки", callback_data=f"set_st:{order_id}:REVISION"),
            ],
            [
                InlineKeyboardButton(text="🎉 Завершён", callback_data=f"set_st:{order_id}:COMPLETED"),
                InlineKeyboardButton(text="❌ Отменён", callback_data=f"set_st:{order_id}:CANCELLED"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад к заказу", callback_data=f"adm_order:{order_id}")],
        ]
    )


def get_admin_orders_list_keyboard(orders: list[Order], current_filter: str) -> InlineKeyboardMarkup:
    """Список заказов с фильтрацией."""
    buttons = []
    for order in orders:
        btn_text = f"#{order.id} | {order.bride_name} & {order.groom_name} [{order.status}]"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"adm_order:{order.id}")
        ])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Главное меню админки", callback_data="adm:main"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"adm_filter:{current_filter}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_back_keyboard(order_id: int | None = None) -> InlineKeyboardMarkup:
    """Кнопка возврата в админку."""
    if order_id:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад к заказу", callback_data=f"adm_order:{order_id}")],
                [InlineKeyboardButton(text="🏠 Главное меню админки", callback_data="adm:main")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню админки", callback_data="adm:main")]
        ]
    )
