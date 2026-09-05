"""
Клавиатуры для взаимодействия с клиентом TAKLIVO.
"""
from typing import Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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
    """Главное меню бота с удобной структурой."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_create_invitation"), callback_data="client:create_order")],
            [
                InlineKeyboardButton(text=get_text(lang, "btn_portfolio"), callback_data="client:portfolio"),
                InlineKeyboardButton(text=get_text(lang, "btn_pricing"), callback_data="client:pricing"),
            ],
            [
                InlineKeyboardButton(text=get_text(lang, "btn_my_orders"), callback_data="client:my_orders"),
                InlineKeyboardButton(text=get_text(lang, "btn_referral"), callback_data="client:referral"),
            ],
            [
                InlineKeyboardButton(text=get_text(lang, "btn_promo_code"), callback_data="client:enter_promo"),
            ],
            [
                InlineKeyboardButton(text=get_text(lang, "btn_faq"), callback_data="client:faq"),
                InlineKeyboardButton(text=get_text(lang, "btn_about"), callback_data="client:about"),
            ],
            [InlineKeyboardButton(text=get_text(lang, "btn_instagram"), url=config.INSTAGRAM_URL)],
            [InlineKeyboardButton(text=get_text(lang, "btn_change_language"), callback_data="client:change_lang")],
        ]
    )


def get_promo_activated_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура после успешной активации промокода."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_order_with_discount"), callback_data="client:create_order")],
            [InlineKeyboardButton(text=get_text(lang, "btn_main_menu"), callback_data="client:main_menu")],
        ]
    )


def get_faq_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура списка вопросов FAQ."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "faq_q1"), callback_data="faq_q:1")],
            [InlineKeyboardButton(text=get_text(lang, "faq_q2"), callback_data="faq_q:2")],
            [InlineKeyboardButton(text=get_text(lang, "faq_q3"), callback_data="faq_q:3")],
            [InlineKeyboardButton(text=get_text(lang, "faq_q4"), callback_data="faq_q:4")],
            [InlineKeyboardButton(text=get_text(lang, "faq_q5"), callback_data="faq_q:5")],
            [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu")],
        ]
    )


def get_faq_answer_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка возврата к списку вопросов FAQ."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Другие вопросы" if lang == "ru" else "⬅️ Boshqa savollar", callback_data="client:faq")],
            [InlineKeyboardButton(text=get_text(lang, "btn_main_menu"), callback_data="client:main_menu")],
        ]
    )


def get_referral_keyboard(referral_link: str, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки в разделе реферальной программы с корректным URL-кодированием без артефактов."""
    import urllib.parse
    if lang == "uz":
        share_text = "💍 TAKLIVO — To‘y va marosimlar uchun zamonaviy onlayn taklifnomalar! Havolam orqali o‘ting va 10 000 so‘m chegirmaga ega bo‘ling ✨"
    else:
        share_text = "💍 TAKLIVO — Стильные онлайн-приглашения на свадьбу и торжества! Переходи по моей ссылке и получи скидку 10 000 сум ✨"

    encoded_url = urllib.parse.quote(referral_link, safe="")
    encoded_text = urllib.parse.quote(share_text, safe="")
    share_url = f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_share_ref"), url=share_url)],
            [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu")],
        ]
    )


def get_about_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопки в разделе «О сервисе»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_instagram"), url=config.INSTAGRAM_URL)],
            [InlineKeyboardButton(text=get_text(lang, "btn_create_invitation"), callback_data="client:create_order")],
            [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu")],
        ]
    )


def get_portfolio_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура каталога шаблонов."""
    buttons = []
    for tmpl_id, tmpl in config.TEMPLATES.items():
        name = tmpl.name_uz if lang == "uz" else tmpl.name_ru
        buttons.append([
            InlineKeyboardButton(text=name, callback_data=f"tmpl_view:{tmpl_id}")
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_custom_template"), callback_data="order_select_tmpl:custom")
    ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_template_detail_keyboard(
    template_id: str,
    demo_url: str,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    """Клавиатура детального просмотра шаблона."""
    choose_text = "✨ Tanlash va buyurtma berish" if lang == "uz" else "✨ Выбрать и настроить"
    demo_text = "🌐 Namunani ko‘rish" if lang == "uz" else "🌐 Открыть демо-сайт"
    back_text = "⬅️ Orqaga" if lang == "uz" else "⬅️ Назад"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=demo_text, url=demo_url)],
            [InlineKeyboardButton(text=choose_text, callback_data=f"order_select_tmpl:{template_id}")],
            [InlineKeyboardButton(text=back_text, callback_data="client:portfolio")],
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

def get_event_type_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Шаг 1: Выбор типа мероприятия."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "event_wedding"), callback_data="wizard_event:wedding")],
            [InlineKeyboardButton(text=get_text(lang, "event_birthday"), callback_data="wizard_event:birthday")],
            [InlineKeyboardButton(text=get_text(lang, "event_sunnat"), callback_data="wizard_event:sunnat")],
            [InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel")],
        ]
    )


def get_template_selection_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Шаг 2: Выбор стиля в визарде заказа."""
    buttons = []
    for tmpl_id, tmpl in config.TEMPLATES.items():
        name = tmpl.name_uz if lang == "uz" else tmpl.name_ru
        buttons.append([
            InlineKeyboardButton(text=name, callback_data=f"wizard_tmpl:{tmpl_id}")
        ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_custom_template"), callback_data="wizard_tmpl:custom")
    ])
    buttons.append([
        InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="wizard_back:to_event"),
        InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel"),
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


def get_order_preview_keyboard(
    has_promo: bool = False,
    bonus_balance: int = 0,
    bonus_applied: bool = False,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа с поддержкой бонусов и промокодов."""
    buttons = [
        [InlineKeyboardButton(text=get_text(lang, "btn_confirm_order"), callback_data="wizard_order:confirm")],
    ]
    if bonus_balance > 0 and not bonus_applied:
        bonus_btn_text = f"🎁 Списать бонусы (-{bonus_balance:,} сум)" if lang == "ru" else f"🎁 Bonuslarni ishlatish (-{bonus_balance:,} so‘m)"
        buttons.append([InlineKeyboardButton(text=bonus_btn_text, callback_data="wizard_order:apply_bonus")])
    elif bonus_applied:
        cancel_bonus_text = "❌ Убрать списание бонусов" if lang == "ru" else "❌ Bonuslarni bekor qilish"
        buttons.append([InlineKeyboardButton(text=cancel_bonus_text, callback_data="wizard_order:cancel_bonus")])

    if not has_promo:
        buttons.append([InlineKeyboardButton(text=get_text(lang, "btn_enter_promo"), callback_data="wizard_order:enter_promo")])
    buttons.append([InlineKeyboardButton(text=get_text(lang, "btn_edit_order"), callback_data="wizard_order:edit")])
    buttons.append([InlineKeyboardButton(text=get_text(lang, "btn_cancel"), callback_data="wizard:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_edit_fields_keyboard(event_type: str = "wedding", lang: str = "ru") -> InlineKeyboardMarkup:
    """Адаптивный выбор поля для редактирования под тип события."""
    buttons = []
    if event_type == "wedding":
        buttons.append([
            InlineKeyboardButton(text="👰 Имя невесты" if lang == "ru" else "👰 Kelin ismi", callback_data="edit_field:bride"),
            InlineKeyboardButton(text="🤵 Имя жениха" if lang == "ru" else "🤵 Kuyov ismi", callback_data="edit_field:groom"),
        ])
    elif event_type == "birthday":
        buttons.append([
            InlineKeyboardButton(text="🎂 Имя именинника" if lang == "ru" else "🎂 Yubilyar ismi", callback_data="edit_field:birthday_name"),
            InlineKeyboardButton(text="🎉 Возраст / Юбилей" if lang == "ru" else "🎉 Yoshi / Sana", callback_data="edit_field:birthday_age"),
        ])
    elif event_type == "sunnat":
        buttons.append([
            InlineKeyboardButton(text="👦 Имя мальчика" if lang == "ru" else "👦 Bola ismi", callback_data="edit_field:sunnat_child"),
            InlineKeyboardButton(text="👨‍👩‍👦 Родители" if lang == "ru" else "👨‍👩‍👦 Ota-onasi", callback_data="edit_field:sunnat_parents"),
        ])

    buttons.extend([
        [
            InlineKeyboardButton(text="📅 Дата" if lang == "ru" else "📅 Sana", callback_data="edit_field:date"),
            InlineKeyboardButton(text="🕐 Время" if lang == "ru" else "🕐 Vaqt", callback_data="edit_field:time"),
        ],
        [
            InlineKeyboardButton(text="🏰 Место" if lang == "ru" else "🏰 To‘yxona / Joy", callback_data="edit_field:venue"),
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
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
        if order.event_type == "birthday":
            title = f"🎂 {order.celebrant_name or 'ДР'}"
        elif order.event_type == "sunnat":
            title = f"✂️ {order.celebrant_name or 'Суннат туй'}"
        else:
            title = f"💍 {order.bride_name} & {order.groom_name}"

        btn_text = f"#{order.id} | {title} ({badge})"
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


def get_phone_request_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отправки подтвержденного номера телефона Telegram."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text(lang, "btn_send_contact"), request_contact=True)],
            [KeyboardButton(text=get_text(lang, "btn_cancel"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_client_website_review_keyboard(
    order_or_id: Any,
    website_url: str,
    lang: str = "ru",
    is_paid: Optional[bool] = None,
    total_price: int = 0,
) -> InlineKeyboardMarkup:
    """Кнопки под сообщением о готовности сайта (с поддержкой постоплаты)."""
    if hasattr(order_or_id, "id"):
        order_id = order_or_id.id
        paid = (order_or_id.payment_status == "PAID" or order_or_id.total_price == 0) if is_paid is None else is_paid
        price = order_or_id.total_price
    else:
        order_id = int(order_or_id)
        paid = False if is_paid is None else is_paid
        price = total_price

    if not paid and price > 0:
        action_btn = InlineKeyboardButton(
            text=get_text(lang, "btn_pay_and_activate_website", total_price=format_currency(price, lang)),
            callback_data=f"pay_order:{order_id}",
        )
    else:
        action_btn = InlineKeyboardButton(
            text=get_text(lang, "btn_approve_website"),
            callback_data=f"client_approve:{order_id}",
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_open_website"), url=website_url)],
            [action_btn],
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
