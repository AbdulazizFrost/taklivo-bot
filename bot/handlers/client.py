"""
Обработчики клиентской части бота TAKLIVO (Главное меню, Портфолио, Прайс-лист, Мои заказы, О сервисе, Правки).
"""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.database import db, OrderStatus
from bot.keyboards import (
    get_language_keyboard,
    get_main_menu_keyboard,
    get_portfolio_keyboard,
    get_template_detail_keyboard,
    get_pricing_keyboard,
    get_my_orders_keyboard,
    get_order_card_keyboard,
    get_cancel_keyboard,
)
from bot.locales import get_text
from bot.services import order_service, notifications
from bot.states.order import OrderStates
from bot.utils.helpers import format_currency, get_status_badge, escape
from config import config

router = Router(name="client_router")
logger = logging.getLogger(__name__)


# --- Команда /start и выбор языка ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработка команды /start."""
    await state.clear()
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    await message.answer(
        text=get_text(user.language, "select_language"),
        reply_markup=get_language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def callback_select_language(callback: CallbackQuery, state: FSMContext) -> None:
    """Сохранение выбранного языка и показ главного меню."""
    lang = callback.data.split(":")[1]
    await db.set_user_language(callback.from_user.id, lang)
    await callback.answer(get_text(lang, "language_selected"))

    await callback.message.edit_text(
        text=get_text(lang, "main_menu_title"),
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "client:change_lang")
async def callback_change_language(callback: CallbackQuery) -> None:
    """Смена языка интерфейса."""
    lang = await db.get_user_language(callback.from_user.id)
    await callback.message.edit_text(
        text=get_text(lang, "select_language"),
        reply_markup=get_language_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "client:main_menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню."""
    await state.clear()
    lang = await db.get_user_language(callback.from_user.id)
    await callback.message.edit_text(
        text=get_text(lang, "main_menu_title"),
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- О сервисе ---

@router.callback_query(F.data == "client:about")
async def callback_about(callback: CallbackQuery) -> None:
    """Раздел «О сервисе»."""
    lang = await db.get_user_language(callback.from_user.id)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text(lang, "btn_create_invitation"), callback_data="client:create_order")],
            [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu")],
        ]
    )
    await callback.message.edit_text(
        text=get_text(lang, "about_text", support_admin=config.SUPPORT_ADMIN),
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


# --- Портфолио шаблонов ---

@router.callback_query(F.data == "client:portfolio")
async def callback_portfolio(callback: CallbackQuery) -> None:
    """Каталог шаблонов."""
    lang = await db.get_user_language(callback.from_user.id)
    await callback.message.edit_text(
        text=get_text(lang, "portfolio_title"),
        reply_markup=get_portfolio_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tmpl_view:"))
async def callback_template_view(callback: CallbackQuery) -> None:
    """Карточка конкретного шаблона с описанием и ссылкой на демо."""
    tmpl_id = callback.data.split(":")[1]
    lang = await db.get_user_language(callback.from_user.id)
    tmpl = config.TEMPLATES.get(tmpl_id)

    if not tmpl:
        await callback.answer("Шаблон не найден", show_alert=True)
        return

    name = tmpl.name_uz if lang == "uz" else tmpl.name_ru
    desc = tmpl.description_uz if lang == "uz" else tmpl.description_ru

    full_text = (
        f"{tmpl.emoji} <b>{name}</b>\n\n"
        f"<i>{desc}</i>\n\n"
        f"📱 Нажмите кнопку <b>«{get_text(lang, 'btn_demo_link')}»</b>, чтобы открыть пример сайта в браузере.\n\n"
        f"Если стиль вам подходит — нажмите <b>«{get_text(lang, 'btn_choose_template')}»</b> для перехода к конструктору."
    ) if lang == "ru" else (
        f"{tmpl.emoji} <b>{name}</b>\n\n"
        f"<i>{desc}</i>\n\n"
        f"📱 Brauzerda jonli namunani ko‘rish uchun <b>«{get_text(lang, 'btn_demo_link')}»</b> tugmasini bosing.\n\n"
        f"Agar dizayn sizga ma’qul bo‘lsa — <b>«{get_text(lang, 'btn_choose_template')}»</b> tugmasi orqali konstruktorga o‘ting."
    )

    await callback.message.edit_text(
        text=full_text,
        reply_markup=get_template_detail_keyboard(tmpl.id, tmpl.demo_url, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Прайс-лист функций ---

@router.callback_query(F.data == "client:pricing")
async def callback_pricing(callback: CallbackQuery) -> None:
    """Раздел прайс-листа."""
    lang = await db.get_user_language(callback.from_user.id)
    extra_prices = config.get_extra_options_prices()

    pricing_text = get_text(
        lang,
        "pricing_title",
        base_price=format_currency(config.BASE_PRICE, lang=lang),
        timer_price=format_currency(extra_prices["timer"], lang=lang),
        rsvp_price=format_currency(extra_prices["rsvp"], lang=lang),
        map_price=format_currency(extra_prices["map"], lang=lang),
        gallery_price=format_currency(extra_prices["gallery"], lang=lang),
        music_price=format_currency(extra_prices["music"], lang=lang),
        dresscode_price=format_currency(extra_prices["dresscode"], lang=lang),
        schedule_price=format_currency(extra_prices["schedule"], lang=lang),
        second_language_price=format_currency(extra_prices["second_language"], lang=lang),
    )

    await callback.message.edit_text(
        text=pricing_text,
        reply_markup=get_pricing_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Мои заказы ---

@router.callback_query(F.data == "client:my_orders")
async def callback_my_orders(callback: CallbackQuery) -> None:
    """Список личных заказов клиента."""
    lang = await db.get_user_language(callback.from_user.id)
    orders = await order_service.get_user_orders_list(callback.from_user.id)

    if not orders:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=get_text(lang, "btn_create_invitation"), callback_data="client:create_order")],
                [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="client:main_menu")],
            ]
        )
        await callback.message.edit_text(
            text=get_text(lang, "no_orders"),
            reply_markup=kb,
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        text=get_text(lang, "my_orders_title"),
        reply_markup=get_my_orders_keyboard(orders, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("my_order:"))
async def callback_view_single_order(callback: CallbackQuery) -> None:
    """Карточка отдельного заказа."""
    order_id = int(callback.data.split(":")[1])
    lang = await db.get_user_language(callback.from_user.id)
    order = await order_service.get_order_by_id(order_id)

    if not order or order.telegram_id != callback.from_user.id:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    photos = await db.get_order_photos(order_id)
    music = await db.get_order_music(order_id)

    options_dict = {
        "timer": True,
        "rsvp": order.rsvp_enabled,
        "map": order.map_enabled,
        "gallery": order.gallery_enabled,
        "music": order.music_enabled,
        "dresscode": order.dresscode_enabled,
        "schedule": order.schedule_enabled,
        "second_language": order.second_language_enabled,
    }

    preview_text = order_service.format_order_preview(
        order_id=order.id,
        bride_name=order.bride_name,
        groom_name=order.groom_name,
        wedding_date=order.wedding_date,
        wedding_time=order.wedding_time,
        venue=order.venue,
        address=order.address,
        phone=order.phone,
        template_name=order.template_name,
        plan_name="CUSTOM",
        options=options_dict,
        photos_count=len(photos),
        has_music=music is not None,
        total_price=order.total_price,
        lang=lang,
    )

    status_badge_text = get_status_badge(order.status, lang=lang)
    site_info = ""
    if order.website_url:
        site_info = f"\n\n🌐 <b>Ссылка на сайт:</b> <a href='{order.website_url}'>{order.website_url}</a>"

    full_text = f"📊 <b>Статус:</b> {status_badge_text}{site_info}\n\n{preview_text}"

    await callback.message.edit_text(
        text=full_text,
        reply_markup=get_order_card_keyboard(order, lang=lang),
        parse_mode="HTML",
        disable_web_page_preview=False,
    )
    await callback.answer()


# --- Одобрение сайта клиентом ---

@router.callback_query(F.data.startswith("client_approve:"))
async def callback_client_approve(callback: CallbackQuery) -> None:
    """Клиент одобряет готовый сайт."""
    order_id = int(callback.data.split(":")[1])
    lang = await db.get_user_language(callback.from_user.id)
    order = await order_service.get_order_by_id(order_id)

    if not order or order.telegram_id != callback.from_user.id:
        await callback.answer("Ошибка заказа", show_alert=True)
        return

    await order_service.complete_order(order_id)
    await callback.message.answer(
        text=get_text(lang, "website_approved"),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Запрос правок по готовому сайту ---

@router.callback_query(F.data.startswith("req_revision:"))
async def callback_request_revisions(callback: CallbackQuery, state: FSMContext) -> None:
    """Клиент нажимает «Нужны изменения»."""
    order_id = int(callback.data.split(":")[1])
    lang = await db.get_user_language(callback.from_user.id)

    await state.update_data(revision_order_id=order_id, lang=lang)
    await state.set_state(OrderStates.revising)

    await callback.message.answer(
        text=get_text(lang, "prompt_revisions"),
        reply_markup=get_cancel_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(OrderStates.revising, F.text)
async def process_revision_text(message: Message, state: FSMContext) -> None:
    """Прием текста правок и оповещение администратора."""
    data = await state.get_data()
    order_id = data.get("revision_order_id")
    lang = data.get("lang", "ru")
    revision_text = message.text.strip()

    if not order_id:
        await state.clear()
        return

    success, updated_order = await order_service.submit_revisions(order_id, revision_text)
    await state.clear()

    await message.answer(
        text=get_text(lang, "revisions_sent"),
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )

    if updated_order:
        await notifications.notify_admin_revision(
            bot=message.bot,
            order=updated_order,
            revision_text=revision_text,
            username=message.from_user.username,
        )
