"""
Обработчики клиентской части бота TAKLIVO (Главное меню, FAQ, Рефералы, Портфолио, Прайс-лист, Мои заказы, О сервисе, Правки).
"""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.database import db, OrderStatus, PaymentStatus
from bot.keyboards import (
    get_language_keyboard,
    get_main_menu_keyboard,
    get_about_keyboard,
    get_faq_keyboard,
    get_faq_answer_keyboard,
    get_referral_keyboard,
    get_portfolio_keyboard,
    get_template_detail_keyboard,
    get_pricing_keyboard,
    get_my_orders_keyboard,
    get_order_card_keyboard,
    get_cancel_keyboard,
    get_back_cancel_keyboard,
    get_promo_activated_keyboard,
    get_event_type_keyboard,
)
from bot.locales import get_text
from bot.services import order_service, notifications
from bot.states import OrderStates, ClientStates
from bot.utils.helpers import format_currency, get_status_badge, escape
from config import config

router = Router(name="client_router")
logger = logging.getLogger(__name__)


# --- Команда /start и выбор языка ---

@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработка команд /start и /menu с поддержкой реферальных ссылок, промокодов и прямого старта заказа."""
    await state.clear()

    existing_user = await db.get_user(message.from_user.id)

    # Проверка параметров в deep link: /start ref_123456 или /start promo или /start promo_TAKLIVO50
    referrer_id = None
    promo_code_to_activate = None
    is_direct_order = False
    args = message.text.split()
    if len(args) > 1:
        param = args[1].strip()
        if param in ("promo", "create", "order", "flash"):
            is_direct_order = True
        elif param.startswith("ref_"):
            try:
                ref_str = param.replace("ref_", "")
                referrer_id = int(ref_str)
            except ValueError:
                referrer_id = None
        elif param.startswith("promo_") or param.upper().startswith("TAKLIVO"):
            promo_raw = param.replace("promo_", "").strip().upper()
            promo = await db.get_promocode(promo_raw)
            if promo and promo.is_active and promo.used_count < promo.max_uses:
                promo_code_to_activate = promo.code

    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        referrer_id=referrer_id,
    )

    if promo_code_to_activate:
        current_promo = await db.get_user_active_promocode(user.telegram_id)
        if not current_promo:
            await db.set_user_active_promocode(user.telegram_id, promo_code_to_activate)
    else:
        # Автоматическая выдача 24-часового велкам промокода TAKLIVO50 новым пользователям (без заказов)
        current_promo = await db.get_user_active_promocode(user.telegram_id)
        if not current_promo:
            user_orders = await db.get_user_orders(user.telegram_id)
            if not user_orders:
                await db.set_user_active_promocode(user.telegram_id, "TAKLIVO50")

    lang = user.language or "ru"

    # Если пользователь перешел по кнопке "Создать приглашение" (из рассылки /start=promo):
    if is_direct_order:
        user_orders = await db.get_user_orders(user.telegram_id)
        active_unpaid = next(
            (
                o for o in user_orders
                if o.payment_status != PaymentStatus.PAID.value
                and o.status in (
                    OrderStatus.IN_PROGRESS.value,
                    OrderStatus.PREVIEW.value,
                    OrderStatus.REVISION.value,
                    OrderStatus.WAITING_PAYMENT.value,
                )
            ),
            None,
        )
        if active_unpaid:
            await message.answer(
                text=get_text(lang, "err_already_has_active_order", order_id=active_unpaid.id),
                reply_markup=get_main_menu_keyboard(lang=lang),
                parse_mode="HTML",
            )
            return

        active_promo_code = await db.get_user_active_promocode(user.telegram_id)
        promo_obj = await db.get_promocode(active_promo_code) if active_promo_code else None
        promocode = promo_obj.code if (promo_obj and promo_obj.is_active and promo_obj.used_count < promo_obj.max_uses) else None

        await state.update_data(
            lang=lang,
            event_type="wedding",
            promocode=promocode,
            options={
                "timer": True,
                "rsvp": False,
                "map": True,
                "gallery": False,
                "music": False,
                "dresscode": False,
                "schedule": False,
                "second_language": False,
            },
        )
        await state.set_state(OrderStates.choosing_event_type)
        await message.answer(
            text=get_text(lang, "step_event_type"),
            reply_markup=get_event_type_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    # Если пользователь уже зарегистрирован, сразу открываем главное меню на его языке без переспрашивания
    if existing_user:
        active_promo_code = await db.get_user_active_promocode(user.telegram_id)
        promo_banner = ""
        if active_promo_code:
            is_active, time_left, deadline, _ = await db.get_user_promo_timer(user.telegram_id, lang=lang)
            if not is_active and active_promo_code == "TAKLIVO50":
                await db.set_user_active_promocode(user.telegram_id, None)
                active_promo_code = None

            if active_promo_code:
                promo = await db.get_promocode(active_promo_code)
                if promo and promo.is_active and promo.used_count < promo.max_uses:
                    disc_str = f"{promo.discount_percent}%" if promo.discount_percent > 0 else format_currency(promo.discount_amount, lang)
                    promo_banner = f"\n\n{get_text(lang, 'start_promo_activated', code=promo.code, discount=disc_str, time_left=time_left, deadline=deadline)}"

        await message.answer(
            text=get_text(lang, "main_menu_title") + promo_banner,
            reply_markup=get_main_menu_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    # Только для самых новых пользователей (первый раз в боте) спрашиваем язык
    await message.answer(
        text=get_text(lang, "select_language"),
        reply_markup=get_language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def callback_select_language(callback: CallbackQuery, state: FSMContext) -> None:
    """Сохранение выбранного языка и показ главного меню с учетом активного промокода."""
    lang = callback.data.split(":")[1]
    await db.set_user_language(callback.from_user.id, lang)
    await callback.answer(get_text(lang, "language_selected"))

    active_promo_code = await db.get_user_active_promocode(callback.from_user.id)
    promo_banner = ""
    if active_promo_code:
        is_active, time_left, deadline, _ = await db.get_user_promo_timer(callback.from_user.id, lang=lang)
        if not is_active and active_promo_code == "TAKLIVO50":
            await db.set_user_active_promocode(callback.from_user.id, None)
            active_promo_code = None

        if active_promo_code:
            promo = await db.get_promocode(active_promo_code)
            if promo and promo.is_active and promo.used_count < promo.max_uses:
                disc_str = f"{promo.discount_percent}%" if promo.discount_percent > 0 else format_currency(promo.discount_amount, lang)
                promo_banner = f"\n\n{get_text(lang, 'start_promo_activated', code=promo.code, discount=disc_str, time_left=time_left, deadline=deadline)}"

    await callback.message.edit_text(
        text=get_text(lang, "main_menu_title") + promo_banner,
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "client:enter_promo")
async def callback_enter_promo(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос ввода промокода из главного меню (с блокировкой, если уже есть активный)."""
    lang = await db.get_user_language(callback.from_user.id)

    # Если уже есть активный неиспользованный промокод, запрещаем вводить второй
    active_promo_code = await db.get_user_active_promocode(callback.from_user.id)
    if active_promo_code:
        promo = await db.get_promocode(active_promo_code)
        if promo and promo.is_active and promo.used_count < promo.max_uses:
            disc_str = f"{promo.discount_percent}%" if promo.discount_percent > 0 else format_currency(promo.discount_amount, lang)
            await callback.message.edit_text(
                text=get_text(lang, "menu_promo_already_active", code=promo.code, discount=disc_str),
                reply_markup=get_promo_activated_keyboard(lang=lang),
                parse_mode="HTML",
            )
            await callback.answer()
            return

    await state.set_state(ClientStates.entering_menu_promocode)
    await callback.message.edit_text(
        text=get_text(lang, "menu_promo_prompt"),
        reply_markup=get_back_cancel_keyboard("client:main_menu", lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ClientStates.entering_menu_promocode, F.text)
async def process_menu_promocode(message: Message, state: FSMContext) -> None:
    """Обработка и активация промокода из главного меню."""
    lang = await db.get_user_language(message.from_user.id)

    # Дополнительная проверка на случай параллельного ввода
    active_promo_code = await db.get_user_active_promocode(message.from_user.id)
    if active_promo_code:
        promo = await db.get_promocode(active_promo_code)
        if promo and promo.is_active and promo.used_count < promo.max_uses:
            disc_str = f"{promo.discount_percent}%" if promo.discount_percent > 0 else format_currency(promo.discount_amount, lang)
            await state.clear()
            await message.answer(
                text=get_text(lang, "menu_promo_already_active", code=promo.code, discount=disc_str),
                reply_markup=get_promo_activated_keyboard(lang=lang),
                parse_mode="HTML",
            )
            return

    code = message.text.strip().upper()

    promo = await db.get_promocode(code)
    if not promo or not promo.is_active or promo.used_count >= promo.max_uses:
        await message.answer(
            text=get_text(lang, "menu_promo_invalid"),
            reply_markup=get_back_cancel_keyboard("client:main_menu", lang=lang),
            parse_mode="HTML",
        )
        return

    # Сохраняем активный промокод для пользователя в базе
    await db.set_user_active_promocode(message.from_user.id, promo.code)
    await state.clear()

    discount_str = f"{promo.discount_percent}%" if promo.discount_percent > 0 else format_currency(promo.discount_amount, lang)

    await message.answer(
        text=get_text(lang, "menu_promo_success", code=promo.code, discount=discount_str),
        reply_markup=get_promo_activated_keyboard(lang=lang),
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
    """Возврат в главное меню с отображением активного промокода."""
    await state.clear()
    lang = await db.get_user_language(callback.from_user.id)
    active_promo_code = await db.get_user_active_promocode(callback.from_user.id)
    promo_banner = ""
    if active_promo_code:
        is_active, time_left, deadline, _ = await db.get_user_promo_timer(callback.from_user.id, lang=lang)
        if not is_active and active_promo_code == "TAKLIVO50":
            await db.set_user_active_promocode(callback.from_user.id, None)
            active_promo_code = None

        if active_promo_code:
            promo = await db.get_promocode(active_promo_code)
            if promo and promo.is_active and promo.used_count < promo.max_uses:
                disc_str = f"{promo.discount_percent}%" if promo.discount_percent > 0 else format_currency(promo.discount_amount, lang)
                promo_banner = f"\n\n{get_text(lang, 'start_promo_activated', code=promo.code, discount=disc_str, time_left=time_left, deadline=deadline)}"

    await callback.message.edit_text(
        text=get_text(lang, "main_menu_title") + promo_banner,
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Частые вопросы (FAQ) ---

@router.callback_query(F.data == "client:faq")
async def callback_faq(callback: CallbackQuery) -> None:
    """Список вопросов FAQ."""
    lang = await db.get_user_language(callback.from_user.id)
    await callback.message.edit_text(
        text=get_text(lang, "faq_title"),
        reply_markup=get_faq_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("faq_q:"))
async def callback_faq_answer(callback: CallbackQuery) -> None:
    """Отображение ответа на конкретный вопрос FAQ."""
    q_num = callback.data.split(":")[1]
    lang = await db.get_user_language(callback.from_user.id)
    answer_text = get_text(lang, f"faq_a{q_num}")

    await callback.message.edit_text(
        text=answer_text,
        reply_markup=get_faq_answer_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Реферальная программа («Пригласи друга») ---

@router.callback_query(F.data == "client:referral")
async def callback_referral(callback: CallbackQuery) -> None:
    """Раздел реферальной программы со статистикой и персональной ссылкой."""
    lang = await db.get_user_language(callback.from_user.id)
    stats = await db.get_referral_stats(callback.from_user.id)

    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username or "taklivo_bot"
    ref_link = f"https://t.me/{bot_username}?start=ref_{callback.from_user.id}"

    text = get_text(
        lang,
        "referral_title",
        referral_link=ref_link,
        invited_count=stats["invited_count"],
        orders_count=stats["orders_count"],
        bonus_balance=format_currency(stats.get("bonus_balance", 0), lang),
        reward_bonus=format_currency(config.REFERRAL_REWARD_BONUS, lang),
        welcome_bonus=format_currency(config.REFERRAL_WELCOME_BONUS, lang),
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_referral_keyboard(ref_link, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- О сервисе ---

@router.callback_query(F.data == "client:about")
async def callback_about(callback: CallbackQuery) -> None:
    """Раздел «О сервисе»."""
    lang = await db.get_user_language(callback.from_user.id)
    await callback.message.edit_text(
        text=get_text(lang, "about_text"),
        reply_markup=get_about_keyboard(lang=lang),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()


# --- Портфолио шаблонов ---

# --- Портфолио и демо-шаблоны ---

@router.message(Command("demo", "portfolio", "katalog", "shablon"))
async def cmd_portfolio(message: Message) -> None:
    """Прямая команда перехода к каталогу и витрине демо-сайтов."""
    lang = await db.get_user_language(message.from_user.id)
    await message.answer(
        text=get_text(lang, "portfolio_title"),
        reply_markup=get_portfolio_keyboard(lang=lang),
        parse_mode="HTML",
    )


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
        f"🔗 <b>Прямая ссылка:</b> <a href='{tmpl.demo_url}'>{tmpl.demo_url}</a>\n\n"
        f"📱 Нажмите кнопку ниже, чтобы открыть сайт прямо в Telegram или в браузере.\n\n"
        f"Если стиль вам подходит — нажмите <b>«{get_text(lang, 'btn_choose_template')}»</b> для перехода к конструктору."
    ) if lang == "ru" else (
        f"{tmpl.emoji} <b>{name}</b>\n\n"
        f"<i>{desc}</i>\n\n"
        f"🔗 <b>Jonli havola:</b> <a href='{tmpl.demo_url}'>{tmpl.demo_url}</a>\n\n"
        f"📱 Saytni ko‘rish uchun quyidagi havola yoki tugmalardan foydalaning.\n\n"
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

    def fmt_price(val: int) -> str:
        if val == 0:
            return "БЕСПЛАТНО 🎁" if lang == "ru" else "BEPUL 🎁"
        return format_currency(val, lang=lang)

    pricing_text = get_text(
        lang,
        "pricing_title",
        base_price=format_currency(config.BASE_PRICE, lang=lang),
        timer_price=fmt_price(extra_prices["timer"]),
        rsvp_price=fmt_price(extra_prices["rsvp"]),
        map_price=fmt_price(extra_prices["map"]),
        gallery_price="БЕСПЛАТНО 🎁" if lang == "ru" else "BEPUL 🎁",
        music_price="БЕСПЛАТНО 🎁" if lang == "ru" else "BEPUL 🎁",
        dresscode_price=fmt_price(extra_prices["dresscode"]),
        schedule_price=fmt_price(extra_prices["schedule"]),
        second_language_price=fmt_price(extra_prices["second_language"]),
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
        event_type=order.event_type,
        bride_name=order.bride_name,
        groom_name=order.groom_name,
        celebrant_name=order.celebrant_name,
        parents_name=order.parents_name,
        age_or_details=order.age_or_details,
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
        promocode=order.promocode,
        discount_amount=order.discount_amount,
        reference_url=order.reference_url,
        location_url=order.location_url,
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
async def callback_client_approve(callback: CallbackQuery, state: FSMContext) -> None:
    """Клиент одобряет готовый сайт (с перенаправлением на оплату, если сайт не был оплачен)."""
    order_id = int(callback.data.split(":")[1])
    lang = await db.get_user_language(callback.from_user.id)
    order = await order_service.get_order_by_id(order_id)

    if not order or order.telegram_id != callback.from_user.id:
        await callback.answer("Ошибка заказа", show_alert=True)
        return

    # Если заказ еще не оплачен и сумма > 0, перенаправляем к оплате
    if order.payment_status != PaymentStatus.PAID.value and order.total_price > 0:
        await callback.answer()
        from bot.handlers.order import process_pay_existing_order
        callback.data = f"pay_order:{order_id}"
        await process_pay_existing_order(callback, state)
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

    if len(revision_text) > 1000:
        await message.answer(
            text=get_text(lang, "err_text_too_long", max_len=1000),
            reply_markup=get_cancel_keyboard(lang=lang),
            parse_mode="HTML",
        )
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


# --- Обработка входящих сообщений и локации от клиентов вне визарда ---

@router.message(
    StateFilter(None),
    ~F.text.startswith("/"),
    F.text | F.location | F.photo | F.document | F.audio | F.voice,
)
async def process_client_idle_message(message: Message, state: FSMContext) -> None:
    """
    Прием локаций, сообщений и файлов от клиентов, у которых уже есть заказ,
    с автоматическим сохранением локации и оповещением администратора.
    """
    if not message.from_user:
        return

    # Проверяем, есть ли у пользователя заказы
    orders = await db.get_user_orders(message.from_user.id)
    lang = await db.get_user_language(message.from_user.id) or "uz"

    if not orders:
        # Если пользователь без заказов пишет в чат бота
        await message.answer(
            text=get_text(lang, "client_no_order_fallback"),
            reply_markup=get_main_menu_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    # Выбираем самый актуальный заказ клиента (активный или последний)
    active_statuses = [
        OrderStatus.IN_PROGRESS.value,
        OrderStatus.WAITING_PAYMENT.value,
        OrderStatus.PAYMENT_REVIEW.value,
        OrderStatus.PREVIEW.value,
        OrderStatus.REVISION.value,
    ]
    target_order = next((o for o in orders if o.status in active_statuses), orders[0])
    user_mention = f"@{escape(message.from_user.username)}" if message.from_user.username else f"ID: <code>{message.from_user.id}</code>"

    # Клавиатура для быстрого действия администратора
    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👁 Открыть заказ #{target_order.id}", callback_data=f"adm_order:{target_order.id}")],
            [InlineKeyboardButton(text="💬 Написать клиенту", callback_data=f"adm_msg_client:{target_order.id}")],
        ]
    )

    # 1. Если отправлена геолокация или ссылка на карту
    location_url = None
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        location_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    elif message.text:
        text_lower = message.text.lower()
        if (
            "maps.google" in text_lower
            or "goo.gl/maps" in text_lower
            or "maps.app.goo.gl" in text_lower
            or ("yandex" in text_lower and "maps" in text_lower)
            or "2gis" in text_lower
            or text_lower.startswith("http://")
            or text_lower.startswith("https://")
        ):
            location_url = message.text.strip()
            if len(location_url) > 500:
                location_url = location_url[:500]

    if location_url:
        # Сохраняем локацию в БД
        await order_service.update_order_location(target_order.id, location_url)

        # Оповещаем администратора
        admin_alert = (
            f"📍 <b>КЛИЕНТ ПРИСЛАЛ ЛОКАЦИЮ ПО ЗАКАЗУ #{target_order.id}!</b>\n\n"
            f"👤 <b>Клиент:</b> {user_mention}\n"
            f"📞 <b>Телефон:</b> {escape(target_order.phone or '—')}\n"
            f"🗺 <b>Ссылка на карту:</b> {escape(location_url)}\n\n"
            f"<i>✅ Локация автоматически сохранена в заказ #{target_order.id} в базе данных!</i>"
        )
        for admin_id in config.ADMIN_IDS:
            try:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=admin_alert,
                    reply_markup=admin_kb,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(f"Failed to notify admin #{admin_id} of client location: {e}")

        # Отвечаем клиенту
        await message.answer(
            text=get_text(lang, "client_location_updated", order_id=target_order.id, location_url=escape(location_url)),
            parse_mode="HTML",
        )
        return

    # 2. Если отправлен обычный текст
    if message.text:
        admin_alert = (
            f"💬 <b>СООБЩЕНИЕ ОТ КЛИЕНТА (Заказ #{target_order.id})</b>\n\n"
            f"👤 <b>Клиент:</b> {user_mention}\n"
            f"📞 <b>Телефон:</b> {escape(target_order.phone or '—')}\n\n"
            f"<b>Текст:</b>\n{escape(message.text)}"
        )
        for admin_id in config.ADMIN_IDS:
            try:
                await message.bot.send_message(
                    chat_id=admin_id,
                    text=admin_alert,
                    reply_markup=admin_kb,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error(f"Failed to forward client message to admin #{admin_id}: {e}")

        await message.answer(
            text=get_text(lang, "client_message_forwarded"),
            parse_mode="HTML",
        )
        return

    # 3. Если отправлен медиа-файл (фото, музыка, документ, голос)
    admin_caption = f"📎 <b>Файл от клиента {user_mention} (Заказ #{target_order.id})</b>"
    for admin_id in config.ADMIN_IDS:
        try:
            await message.send_copy(
                chat_id=admin_id,
                caption=admin_caption,
                reply_markup=admin_kb,
            )
        except Exception as e:
            logger.error(f"Failed to forward client media to admin #{admin_id}: {e}")

    await message.answer(
        text=get_text(lang, "client_message_forwarded"),
        parse_mode="HTML",
    )
