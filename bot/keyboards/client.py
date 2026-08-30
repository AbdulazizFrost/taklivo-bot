"""
Клавиатуры для взаимодействия с клиентом.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.models import Order
from bot.locales import get_text
from bot.utils.helpers import format_currency
from config import config


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            ]
        ]
    )


def get_main_menu_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Главное меню бота."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_create_invitation"), callback_data="client:create_order")],
            [InlineKeyboardButton(text=get_text(lang, "btn_portfolio"), callback_data="client:portfolio")],
            [InlineKeyboardButton(text=get_text(lang, "btn_pricing"), callback_data="client:pricing")],
            [InlineKeyboardButton(text=get_text(lang, "btn_my_orders"), callback_data="client:my_orders")],
            [
                InlineKeyboardButton(text=get_text(lang, "btn_about"), callback_data="client:about"),
                InlineKeyboardButton(text=get_text(lang, "btn_change_language"), callback_data="client:change_lang"),
            ],
        ]
    )


def get_portfolio_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Список шаблонов для просмотра."""
    buttons = []
    for tmpl_id, tmpl in config.TEMPLATES.items():
        name = tmpl.name_uz if lang == "uz" else tmpl.name_ru
        buttons.append([
            InlineKeyboardButton(text=name, callback_data=f"tmpl_view:{tmpl_id}")
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_create_invitation"), callback_data="client:create_order"),
        InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_template_detail_keyboard(template_id: str, demo_url: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки в карточке конкретного шаблона."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_demo_link"), url=demo_url)],
            [InlineKeyboardButton(text=get_text(lang, "btn_choose_template"), callback_data=f"order_select_tmpl:{template_id}")],
            [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:portfolio")],
        ]
    )


def get_pricing_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура раздела цен."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_create_invitation"), callback_data="client:create_order")],
            [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu")],
        ]
    )


# --- Клавиатуры визарда заказа (Конструктор) ---

def get_template_selection_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор дизайна в визарде заказа."""
    buttons = []
    for tmpl_id, tmpl in config.TEMPLATES.items():
        name = tmpl.name_uz if lang == "uz" else tmpl.name_ru
        buttons.append([
            InlineKeyboardButton(text=name, callback_data=f"wizard_tmpl:{tmpl_id}")
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_options_toggle_keyboard(
    selected_options: dict[str, bool],
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    """
    Клавиатура конструктора дополнительных опций.
    Каждая опция переключается (🟢 включена / ⚪️ выключена) с отображением цены.
    """
    extra_prices = config.get_extra_options_prices()

    option_keys = [
        ("timer", get_text(lang, "option_timer")),
        ("rsvp", get_text(lang, "option_rsvp")),
        ("map", get_text(lang, "option_map")),
        ("gallery", get_text(lang, "option_gallery")),
        ("music", get_text(lang, "option_music")),
        ("dresscode", get_text(lang, "option_dresscode")),
        ("schedule", get_text(lang, "option_schedule")),
        ("second_language", get_text(lang, "option_second_language")),
    ]

    buttons = []
    for key, label in option_keys:
        is_active = selected_options.get(key, False)
        icon = "🟢" if is_active else "⚪️"
        price = extra_prices.get(key, 0)
        price_str = f"+{format_currency(price, lang)}"
        btn_text = f"{icon} {label} ({price_str})"
        callback = f"opt_toggle:{key}"

        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=callback)])

    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_continue"), callback_data="wizard_opt:continue")
    ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="wizard_back:to_tmpl"),
        InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_gallery_upload_keyboard(count: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура загрузки фотографий."""
    buttons = []
    if count > 0:
        buttons.append([
            InlineKeyboardButton(text=get_text(lang, "btn_photos_done"), callback_data="wizard_gallery:done")
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_skip_media"), callback_data="wizard_gallery:skip")
    ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_music_upload_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура загрузки музыки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_skip_media"), callback_data="wizard_music:skip")],
            [InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel")],
        ]
    )


def get_order_preview_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_confirm_order"), callback_data="wizard_order:confirm")],
            [InlineKeyboardButton(text=get_text(lang, "btn_edit_order"), callback_data="wizard_order:edit")],
            [InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel")],
        ]
    )


def get_edit_fields_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор поля для редактирования."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👰 Имя невесты" if lang == "ru" else "👰 Kelin ismi", callback_data="edit_field:bride"),
                InlineKeyboardButton(text="🤵 Имя жениха" if lang == "ru" else "🤵 Kuyov ismi", callback_data="edit_field:groom"),
            ],
            [
                InlineKeyboardButton(text="📅 Дата" if lang == "ru" else "📅 Sana", callback_data="edit_field:date"),
                InlineKeyboardButton(text="🕐 Время" if lang == "ru" else "🕐 Vaqt", callback_data="edit_field:time"),
            ],
            [
                InlineKeyboardButton(text="🏰 Место" if lang == "ru" else "🏰 To‘yxona", callback_data="edit_field:venue"),
                InlineKeyboardButton(text="📍 Адрес" if lang == "ru" else "📍 Manzil", callback_data="edit_field:address"),
            ],
            [
                InlineKeyboardButton(text="📞 Телефон" if lang == "ru" else "📞 Telefon", callback_data="edit_field:phone"),
                InlineKeyboardButton(text="🎨 Дизайн" if lang == "ru" else "🎨 Dizayn", callback_data="edit_field:template"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Функции сайта" if lang == "ru" else "⚙️ Sayt funksiyalari", callback_data="edit_field:options"),
            ],
            [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="wizard_back:to_preview")],
        ]
    )


def get_payment_keyboard(order_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура на экране оплаты."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data=f"order_cancel_unpaid:{order_id}")]
        ]
    )


def get_my_orders_keyboard(orders: list[Order], lang: str = "ru") -> InlineKeyboardMarkup:
    """Список заказов пользователя."""
    buttons = []
    for order in orders:
        badge = order.status
        btn_text = f"#{order.id} | {order.bride_name} & {order.groom_name} ({badge})"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"my_order:{order.id}")
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_order_card_keyboard(order: Order, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки в карточке заказа пользователя."""
    buttons = []
    if order.website_url:
        buttons.append([
            InlineKeyboardButton(text=get_text(lang, "btn_open_website"), url=order.website_url)
        ])
    if order.status in ("PREVIEW", "COMPLETED", "IN_PROGRESS"):
        buttons.append([
            InlineKeyboardButton(text=get_text(lang, "btn_request_revisions"), callback_data=f"req_revision:{order.id}")
        ])
    if order.status == "WAITING_PAYMENT":
        buttons.append([
            InlineKeyboardButton(text="💳 Перейти к оплате" if lang == "ru" else "💳 To‘lovga o‘tish", callback_data=f"pay_order:{order.id}")
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:my_orders")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_client_website_review_keyboard(order_id: int, website_url: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки под сообщением о готовности сайта."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_open_website"), url=website_url)],
            [InlineKeyboardButton(text=get_text(lang, "btn_approve_website"), callback_data=f"client_approve:{order_id}")],
            [InlineKeyboardButton(text=get_text(lang, "btn_request_revisions"), callback_data=f"req_revision:{order_id}")],
        ]
    )


def get_cancel_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Простая кнопка отмены."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel")]
        ]
    )


def get_back_cancel_keyboard(back_callback: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки назад и отмена."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data=back_callback),
                InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel"),
            ]
        ]
    )
