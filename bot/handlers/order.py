"""
FSM-обработчик визарда оформления заказа онлайн-приглашения TAKLIVO.
Поддерживает все типы торжеств: Свадьба (Nikoh to'yi), День рождения (Tug'ilgan kun / Yubiley), Суннат туй (Sunnat to'yi).
Конструктор: Выбор события -> Выбор стиля -> Выбор опций -> Ввод данных -> Загрузка медиа -> Проверка -> Оплата.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db, OrderStatus
from bot.keyboards import (
    get_main_menu_keyboard,
    get_event_type_keyboard,
    get_template_selection_keyboard,
    get_options_toggle_keyboard,
    get_gallery_upload_keyboard,
    get_music_upload_keyboard,
    get_order_preview_keyboard,
    get_edit_fields_keyboard,
    get_payment_keyboard,
    get_back_cancel_keyboard,
)
from bot.locales import get_text
from bot.services import calculate_total, order_service, notifications
from bot.states.order import OrderStates
from bot.utils.helpers import format_currency, escape
from bot.utils.validators import validate_date, validate_time, validate_phone
from config import config

router = Router(name="order_wizard_router")
logger = logging.getLogger(__name__)


# --- Отмена визарда на любом шаге ---

@router.callback_query(F.data == "wizard:cancel")
async def callback_cancel_wizard(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена оформления заказа и возврат в главное меню."""
    data = await state.get_data()
    lang = data.get("lang", await db.get_user_language(callback.from_user.id))
    
    current_order_id = data.get("current_order_id")
    if current_order_id:
        await order_service.cancel_order(current_order_id)

    await state.clear()
    await callback.message.edit_text(
        text=get_text(lang, "cancelled"),
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_cancel_unpaid:"))
async def callback_cancel_unpaid_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена заказа с экрана оплаты."""
    order_id = int(callback.data.split(":")[1])
    lang = await db.get_user_language(callback.from_user.id)
    await order_service.cancel_order(order_id)
    await state.clear()
    await callback.message.edit_text(
        text=get_text(lang, "cancelled"),
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Точки входа в оформление заказа ---

@router.callback_query(F.data == "client:create_order")
async def start_order_wizard(callback: CallbackQuery, state: FSMContext) -> None:
    """Старт визарда: Шаг 1 — Выбор типа мероприятия."""
    lang = await db.get_user_language(callback.from_user.id)
    await state.clear()
    await state.update_data(
        lang=lang,
        event_type="wedding",
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
        photos=[],
        music_file_id=None,
        music_filename=None,
    )
    await state.set_state(OrderStates.choosing_event_type)

    await callback.message.edit_text(
        text=get_text(lang, "step_event_type"),
        reply_markup=get_event_type_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Шаг 1: Выбор типа события -> Шаг 2: Выбор дизайна ---

@router.callback_query(OrderStates.choosing_event_type, F.data.startswith("wizard_event:"))
async def process_step_event_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора типа торжества (свадьба / ДР / суннат туй)."""
    event_type = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")

    await state.update_data(event_type=event_type)
    await state.set_state(OrderStates.choosing_template)

    await callback.message.edit_text(
        text=get_text(lang, "step_template"),
        reply_markup=get_template_selection_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Шаг 2: Выбор шаблона -> Шаг 3: Конструктор опций ---

@router.callback_query(OrderStates.choosing_template, F.data.startswith("wizard_tmpl:"))
async def process_step_template(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора шаблона и переход к конструктору функций."""
    tmpl_id = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    tmpl = config.TEMPLATES.get(tmpl_id)

    if not tmpl:
        await callback.answer("Ошибка шаблона", show_alert=True)
        return

    tmpl_name = tmpl.name_uz if lang == "uz" else tmpl.name_ru
    options = data.get("options", {
        "timer": True,
        "rsvp": False,
        "map": True,
        "gallery": False,
        "music": False,
        "dresscode": False,
        "schedule": False,
        "second_language": False,
    })
    calc_res = calculate_total(options, lang=lang)

    await state.update_data(
        template_id=tmpl_id,
        template_name=tmpl_name,
        options=options,
        total_price=calc_res.total_price,
    )
    await state.set_state(OrderStates.choosing_options)

    await callback.message.edit_text(
        text=get_text(
            lang,
            "step_options",
            base_price=format_currency(calc_res.base_price, lang=lang),
            extra_price=format_currency(calc_res.extra_options_total, lang=lang),
            total_price=format_currency(calc_res.total_price, lang=lang),
        ),
        reply_markup=get_options_toggle_keyboard(options, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Шаг 3: Конструктор опций (Toggle переключатели) ---

@router.callback_query(OrderStates.choosing_options, F.data.startswith("opt_toggle:"))
async def process_option_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    """Включение/выключение любой дополнительной опции."""
    opt_key = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    options = data.get("options", {})

    options[opt_key] = not options.get(opt_key, False)
    calc_res = calculate_total(options, lang=lang)
    await state.update_data(options=options, total_price=calc_res.total_price)

    await callback.message.edit_text(
        text=get_text(
            lang,
            "step_options",
            base_price=format_currency(calc_res.base_price, lang=lang),
            extra_price=format_currency(calc_res.extra_options_total, lang=lang),
            total_price=format_currency(calc_res.total_price, lang=lang),
        ),
        reply_markup=get_options_toggle_keyboard(options, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(OrderStates.choosing_options, F.data == "wizard_opt:continue")
async def process_options_continue(callback: CallbackQuery, state: FSMContext) -> None:
    """Переход к вводу данных в зависимости от типа мероприятия."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    event_type = data.get("event_type", "wedding")

    if event_type == "birthday":
        await state.set_state(OrderStates.birthday_name)
        await callback.message.edit_text(
            text=get_text(lang, "step_birthday_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
    elif event_type == "sunnat":
        await state.set_state(OrderStates.sunnat_child_name)
        await callback.message.edit_text(
            text=get_text(lang, "step_sunnat_child_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
    else:
        await state.set_state(OrderStates.bride_name)
        await callback.message.edit_text(
            text=get_text(lang, "step_bride_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
    await callback.answer()


# --- Навигация НАЗАД по шагам визарда ---

@router.callback_query(F.data.startswith("wizard_back:"))
async def process_wizard_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат на предыдущий шаг визарда."""
    target = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    event_type = data.get("event_type", "wedding")

    if target == "to_event":
        await state.set_state(OrderStates.choosing_event_type)
        await callback.message.edit_text(
            text=get_text(lang, "step_event_type"),
            reply_markup=get_event_type_keyboard(lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_tmpl":
        await state.set_state(OrderStates.choosing_template)
        await callback.message.edit_text(
            text=get_text(lang, "step_template"),
            reply_markup=get_template_selection_keyboard(lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_options":
        options = data.get("options", {})
        calc_res = calculate_total(options, lang=lang)
        await state.set_state(OrderStates.choosing_options)
        await callback.message.edit_text(
            text=get_text(
                lang,
                "step_options",
                base_price=format_currency(calc_res.base_price, lang=lang),
                extra_price=format_currency(calc_res.extra_options_total, lang=lang),
                total_price=format_currency(calc_res.total_price, lang=lang),
            ),
            reply_markup=get_options_toggle_keyboard(options, lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_bride":
        await state.set_state(OrderStates.bride_name)
        await callback.message.edit_text(
            text=get_text(lang, "step_bride_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_groom":
        await state.set_state(OrderStates.groom_name)
        await callback.message.edit_text(
            text=get_text(lang, "step_groom_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_bride", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_birthday_name":
        await state.set_state(OrderStates.birthday_name)
        await callback.message.edit_text(
            text=get_text(lang, "step_birthday_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_birthday_age":
        await state.set_state(OrderStates.birthday_age)
        await callback.message.edit_text(
            text=get_text(lang, "step_birthday_age"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_birthday_name", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_sunnat_child":
        await state.set_state(OrderStates.sunnat_child_name)
        await callback.message.edit_text(
            text=get_text(lang, "step_sunnat_child_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_sunnat_parents":
        await state.set_state(OrderStates.sunnat_parents_name)
        await callback.message.edit_text(
            text=get_text(lang, "step_sunnat_parents_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_sunnat_child", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_date":
        prev_callback = "wizard_back:to_groom"
        if event_type == "birthday":
            prev_callback = "wizard_back:to_birthday_age"
        elif event_type == "sunnat":
            prev_callback = "wizard_back:to_sunnat_parents"

        await state.set_state(OrderStates.wedding_date)
        await callback.message.edit_text(
            text=get_text(lang, "step_date"),
            reply_markup=get_back_cancel_keyboard(prev_callback, lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_time":
        await state.set_state(OrderStates.wedding_time)
        await callback.message.edit_text(
            text=get_text(lang, "step_time"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_date", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_venue":
        await state.set_state(OrderStates.venue)
        await callback.message.edit_text(
            text=get_text(lang, "step_venue"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_time", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_address":
        await state.set_state(OrderStates.address)
        await callback.message.edit_text(
            text=get_text(lang, "step_address"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_venue", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_phone":
        await state.set_state(OrderStates.phone)
        await callback.message.edit_text(
            text=get_text(lang, "step_phone"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_address", lang=lang),
            parse_mode="HTML",
        )
    elif target == "to_preview":
        await _show_order_preview(callback.message, state, is_edit=True)

    await callback.answer()


# --- Шаг 4: Ввод персональных данных (Свадьба) ---

@router.message(OrderStates.bride_name, F.text)
async def process_bride_name(message: Message, state: FSMContext) -> None:
    """Ввод имени невесты."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    name = message.text.strip()
    if len(name) < 2 or len(name) > 60:
        await message.answer(
            get_text(lang, "step_bride_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(bride_name=name)
    await state.set_state(OrderStates.groom_name)

    await message.answer(
        text=get_text(lang, "step_groom_name"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_bride", lang=lang),
        parse_mode="HTML",
    )


@router.message(OrderStates.groom_name, F.text)
async def process_groom_name(message: Message, state: FSMContext) -> None:
    """Ввод имени жениха."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    name = message.text.strip()
    if len(name) < 2 or len(name) > 60:
        await message.answer(
            get_text(lang, "step_groom_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_bride", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(groom_name=name)
    await state.set_state(OrderStates.wedding_date)

    await message.answer(
        text=get_text(lang, "step_date"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_groom", lang=lang),
        parse_mode="HTML",
    )


# --- Шаг 4: Ввод персональных данных (День рождения) ---

@router.message(OrderStates.birthday_name, F.text)
async def process_birthday_name(message: Message, state: FSMContext) -> None:
    """Ввод имени именинника/юбиляра."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    name = message.text.strip()
    if len(name) < 2 or len(name) > 60:
        await message.answer(
            get_text(lang, "step_birthday_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(celebrant_name=name)
    await state.set_state(OrderStates.birthday_age)

    await message.answer(
        text=get_text(lang, "step_birthday_age"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_birthday_name", lang=lang),
        parse_mode="HTML",
    )


@router.message(OrderStates.birthday_age, F.text)
async def process_birthday_age(message: Message, state: FSMContext) -> None:
    """Ввод возраста/юбилея."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    age = message.text.strip()

    await state.update_data(age_or_details=age)
    await state.set_state(OrderStates.wedding_date)

    await message.answer(
        text=get_text(lang, "step_date"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_birthday_age", lang=lang),
        parse_mode="HTML",
    )


# --- Шаг 4: Ввод персональных данных (Суннат туй) ---

@router.message(OrderStates.sunnat_child_name, F.text)
async def process_sunnat_child_name(message: Message, state: FSMContext) -> None:
    """Ввод имени мальчика."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    name = message.text.strip()
    if len(name) < 2 or len(name) > 60:
        await message.answer(
            get_text(lang, "step_sunnat_child_name"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_options", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(celebrant_name=name)
    await state.set_state(OrderStates.sunnat_parents_name)

    await message.answer(
        text=get_text(lang, "step_sunnat_parents_name"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_sunnat_child", lang=lang),
        parse_mode="HTML",
    )


@router.message(OrderStates.sunnat_parents_name, F.text)
async def process_sunnat_parents_name(message: Message, state: FSMContext) -> None:
    """Ввод имен родителей / организаторов."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    parents = message.text.strip()

    await state.update_data(parents_name=parents)
    await state.set_state(OrderStates.wedding_date)

    await message.answer(
        text=get_text(lang, "step_date"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_sunnat_parents", lang=lang),
        parse_mode="HTML",
    )


# --- Шаг 5: Дата и время торжества ---

@router.message(OrderStates.wedding_date, F.text)
async def process_wedding_date(message: Message, state: FSMContext) -> None:
    """Ввод и валидация даты торжества."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    event_type = data.get("event_type", "wedding")
    is_valid, formatted_date = validate_date(message.text)

    prev_callback = "wizard_back:to_groom"
    if event_type == "birthday":
        prev_callback = "wizard_back:to_birthday_age"
    elif event_type == "sunnat":
        prev_callback = "wizard_back:to_sunnat_parents"

    if not is_valid or not formatted_date:
        await message.answer(
            text=get_text(lang, "err_invalid_date"),
            reply_markup=get_back_cancel_keyboard(prev_callback, lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(wedding_date=formatted_date)
    await state.set_state(OrderStates.wedding_time)

    await message.answer(
        text=get_text(lang, "step_time"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_date", lang=lang),
        parse_mode="HTML",
    )


@router.message(OrderStates.wedding_time, F.text)
async def process_wedding_time(message: Message, state: FSMContext) -> None:
    """Ввод и валидация времени начала."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    is_valid, formatted_time = validate_time(message.text)

    if not is_valid or not formatted_time:
        await message.answer(
            text=get_text(lang, "err_invalid_time"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_date", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(wedding_time=formatted_time)
    await state.set_state(OrderStates.venue)

    await message.answer(
        text=get_text(lang, "step_venue"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_time", lang=lang),
        parse_mode="HTML",
    )


# --- Шаг 6: Место, адрес, телефон ---

@router.message(OrderStates.venue, F.text)
async def process_venue(message: Message, state: FSMContext) -> None:
    """Ввод названия места проведения."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    venue = message.text.strip()
    if not venue:
        return

    await state.update_data(venue=venue)
    await state.set_state(OrderStates.address)

    await message.answer(
        text=get_text(lang, "step_address"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_venue", lang=lang),
        parse_mode="HTML",
    )


@router.message(OrderStates.address, F.text)
async def process_address(message: Message, state: FSMContext) -> None:
    """Ввод адреса проведения."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    address = message.text.strip()
    if not address:
        return

    await state.update_data(address=address)
    await state.set_state(OrderStates.phone)

    await message.answer(
        text=get_text(lang, "step_phone"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_address", lang=lang),
        parse_mode="HTML",
    )


@router.message(OrderStates.phone, F.text)
async def process_phone(message: Message, state: FSMContext) -> None:
    """Ввод и валидация контактного телефона."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    is_valid, formatted_phone = validate_phone(message.text)

    if not is_valid or not formatted_phone:
        await message.answer(
            text=get_text(lang, "err_invalid_phone"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_address", lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(phone=formatted_phone)
    options = data.get("options", {})

    # Проверяем, нужна ли загрузка фото
    if options.get("gallery"):
        await state.set_state(OrderStates.gallery_upload)
        await message.answer(
            text=get_text(lang, "step_gallery_upload", count=0),
            reply_markup=get_gallery_upload_keyboard(0, lang=lang),
            parse_mode="HTML",
        )
    elif options.get("music"):
        await state.set_state(OrderStates.music_upload)
        await message.answer(
            text=get_text(lang, "step_music_upload"),
            reply_markup=get_music_upload_keyboard(lang=lang),
            parse_mode="HTML",
        )
    else:
        await _show_order_preview(message, state)


# --- Шаг 7: Загрузка фотографий для галереи ---

@router.message(OrderStates.gallery_upload, F.photo)
async def process_gallery_photo(message: Message, state: FSMContext) -> None:
    """Прием фотографий."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    photos: list[dict] = data.get("photos", [])

    if len(photos) >= 10:
        await message.answer(
            text=get_text(lang, "photo_limit_reached"),
            reply_markup=get_gallery_upload_keyboard(len(photos), lang=lang),
            parse_mode="HTML",
        )
        return

    largest_photo = message.photo[-1]
    photos.append({
        "file_id": largest_photo.file_id,
        "file_unique_id": largest_photo.file_unique_id,
    })
    await state.update_data(photos=photos)

    await message.answer(
        text=get_text(lang, "photo_received", count=len(photos)),
        reply_markup=get_gallery_upload_keyboard(len(photos), lang=lang),
        parse_mode="HTML",
    )


@router.message(OrderStates.gallery_upload, ~F.photo & ~F.text.startswith("/"))
async def process_gallery_invalid_media(message: Message, state: FSMContext) -> None:
    """Обработка неверного типа файла в галерее."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    photos = data.get("photos", [])
    await message.answer(
        text=get_text(lang, "err_not_photo"),
        reply_markup=get_gallery_upload_keyboard(len(photos), lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(OrderStates.gallery_upload, F.data.in_(["wizard_gallery:done", "wizard_gallery:skip"]))
async def process_gallery_finish(callback: CallbackQuery, state: FSMContext) -> None:
    """Завершение загрузки фото."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    options = data.get("options", {})

    if options.get("music"):
        await state.set_state(OrderStates.music_upload)
        await callback.message.edit_text(
            text=get_text(lang, "step_music_upload"),
            reply_markup=get_music_upload_keyboard(lang=lang),
            parse_mode="HTML",
        )
    else:
        await _show_order_preview(callback.message, state, is_edit=True)
    await callback.answer()


# --- Шаг 8: Загрузка музыки ---

@router.message(OrderStates.music_upload, F.audio | F.voice | F.document)
async def process_music_file(message: Message, state: FSMContext) -> None:
    """Прием аудиофайла."""
    data = await state.get_data()
    lang = data.get("lang", "ru")

    file_id = None
    filename = "romantic_track.mp3"

    if message.audio:
        file_id = message.audio.file_id
        filename = message.audio.file_name or f"{message.audio.performer or ''} - {message.audio.title or 'track'}"
    elif message.voice:
        file_id = message.voice.file_id
        filename = "voice_audio.ogg"
    elif message.document and (message.document.mime_type and "audio" in message.document.mime_type):
        file_id = message.document.file_id
        filename = message.document.file_name or "audio_file.mp3"
    else:
        await message.answer(
            text=get_text(lang, "err_not_music"),
            reply_markup=get_music_upload_keyboard(lang=lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(music_file_id=file_id, music_filename=filename)
    await message.answer(get_text(lang, "music_received", filename=filename), parse_mode="HTML")
    await _show_order_preview(message, state)


@router.callback_query(OrderStates.music_upload, F.data == "wizard_music:skip")
async def process_music_skip(callback: CallbackQuery, state: FSMContext) -> None:
    """Пропуск музыки."""
    await _show_order_preview(callback.message, state, is_edit=True)
    await callback.answer()


# --- Предпросмотр (Review) и подтверждение заказа ---

async def _show_order_preview(message_or_msg: Message, state: FSMContext, is_edit: bool = False) -> None:
    """Отображение полной сводки заказа с учетом промокода."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    event_type = data.get("event_type", "wedding")
    options = data.get("options", {})
    calc_res = calculate_total(options, lang=lang)

    promocode = data.get("promocode")
    discount_amount = data.get("discount_amount", 0)
    final_price = max(calc_res.total_price - discount_amount, 0)

    await state.update_data(total_price=final_price)
    await state.set_state(OrderStates.review)

    preview_text = order_service.format_order_preview(
        order_id="NEW",
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
        template_name=data.get("template_name", ""),
        plan_name="CUSTOM",
        options=options,
        photos_count=len(data.get("photos", [])),
        has_music=data.get("music_file_id") is not None,
        promocode=promocode,
        discount_amount=discount_amount,
        total_price=final_price,
        lang=lang,
    )

    if is_edit:
        await message_or_msg.edit_text(
            text=preview_text,
            reply_markup=get_order_preview_keyboard(has_promo=bool(promocode), lang=lang),
            parse_mode="HTML",
        )
    else:
        await message_or_msg.answer(
            text=preview_text,
            reply_markup=get_order_preview_keyboard(has_promo=bool(promocode), lang=lang),
            parse_mode="HTML",
        )


@router.callback_query(OrderStates.review, F.data == "wizard_order:enter_promo")
async def process_start_promocode(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос ввода промокода."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.set_state(OrderStates.entering_promocode)
    await callback.message.edit_text(
        text=get_text(lang, "prompt_promocode"),
        reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(OrderStates.entering_promocode, F.text)
async def process_entered_promocode(message: Message, state: FSMContext) -> None:
    """Проверка и применение промокода."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    code = message.text.strip().upper()

    promo = await db.get_promocode(code)
    if not promo or not promo.is_active or promo.used_count >= promo.max_uses:
        await message.answer(
            text=get_text(lang, "err_invalid_promo"),
            reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang),
            parse_mode="HTML",
        )
        return

    options = data.get("options", {})
    calc_res = calculate_total(options, lang=lang)
    base_total = calc_res.total_price

    if promo.discount_percent > 0:
        discount_amount = int(base_total * (promo.discount_percent / 100))
        success_msg = get_text(
            lang,
            "promo_applied_percent",
            discount=promo.discount_percent,
            amount=format_currency(discount_amount, lang),
        )
    else:
        discount_amount = promo.discount_amount
        success_msg = get_text(
            lang,
            "promo_applied_amount",
            amount=format_currency(discount_amount, lang),
        )

    await state.update_data(promocode=promo.code, discount_amount=discount_amount)
    await message.answer(success_msg, parse_mode="HTML")
    await _show_order_preview(message, state)


@router.callback_query(OrderStates.review, F.data == "wizard_order:edit")
async def process_edit_order_fields(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбор поля для редактирования под тип события."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    event_type = data.get("event_type", "wedding")

    await callback.message.edit_text(
        text="✏️ <b>Выберите, какое поле вы хотите изменить:</b>" if lang == "ru" else "✏️ <b>Qaysi maydonni o‘zgartirmoqchisiz?</b>",
        reply_markup=get_edit_fields_keyboard(event_type=event_type, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(OrderStates.review, F.data.startswith("edit_field:"))
async def process_jump_to_field(callback: CallbackQuery, state: FSMContext) -> None:
    """Точечный переход к конкретному полю для изменения."""
    field = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")

    if field == "bride":
        await state.set_state(OrderStates.bride_name)
        await callback.message.edit_text(text=get_text(lang, "step_bride_name"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "groom":
        await state.set_state(OrderStates.groom_name)
        await callback.message.edit_text(text=get_text(lang, "step_groom_name"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "birthday_name":
        await state.set_state(OrderStates.birthday_name)
        await callback.message.edit_text(text=get_text(lang, "step_birthday_name"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "birthday_age":
        await state.set_state(OrderStates.birthday_age)
        await callback.message.edit_text(text=get_text(lang, "step_birthday_age"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "sunnat_child":
        await state.set_state(OrderStates.sunnat_child_name)
        await callback.message.edit_text(text=get_text(lang, "step_sunnat_child_name"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "sunnat_parents":
        await state.set_state(OrderStates.sunnat_parents_name)
        await callback.message.edit_text(text=get_text(lang, "step_sunnat_parents_name"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "date":
        await state.set_state(OrderStates.wedding_date)
        await callback.message.edit_text(text=get_text(lang, "step_date"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "time":
        await state.set_state(OrderStates.wedding_time)
        await callback.message.edit_text(text=get_text(lang, "step_time"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "venue":
        await state.set_state(OrderStates.venue)
        await callback.message.edit_text(text=get_text(lang, "step_venue"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "address":
        await state.set_state(OrderStates.address)
        await callback.message.edit_text(text=get_text(lang, "step_address"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "phone":
        await state.set_state(OrderStates.phone)
        await callback.message.edit_text(text=get_text(lang, "step_phone"), reply_markup=get_back_cancel_keyboard("wizard_back:to_preview", lang=lang), parse_mode="HTML")
    elif field == "template":
        await state.set_state(OrderStates.choosing_template)
        await callback.message.edit_text(text=get_text(lang, "step_template"), reply_markup=get_template_selection_keyboard(lang=lang), parse_mode="HTML")
    elif field == "options":
        options = data.get("options", {})
        calc_res = calculate_total(options, lang=lang)
        await state.set_state(OrderStates.choosing_options)
        await callback.message.edit_text(
            text=get_text(
                lang,
                "step_options",
                base_price=format_currency(calc_res.base_price, lang=lang),
                extra_price=format_currency(calc_res.extra_options_total, lang=lang),
                total_price=format_currency(calc_res.total_price, lang=lang),
            ),
            reply_markup=get_options_toggle_keyboard(options, lang=lang),
            parse_mode="HTML",
        )
    await callback.answer()


# --- Переход к экрану оплаты и создание заказа ---

@router.callback_query(OrderStates.review, F.data == "wizard_order:confirm")
async def process_confirm_and_create_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Создание заказа в БД только после подтверждения Review."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    user = await db.get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        language=lang,
    )

    # Создаем заказ в базе через order_service
    order_id = await order_service.create_new_order(
        user_id=user.id,
        telegram_id=callback.from_user.id,
        data=data,
    )

    await state.update_data(current_order_id=order_id)
    await state.set_state(OrderStates.waiting_receipt)

    total_price = data.get("total_price", 0)
    payment_text = get_text(
        lang,
        "payment_screen",
        order_id=order_id,
        total_price=format_currency(total_price, lang=lang),
        payment_details=config.PAYMENT_DETAILS,
    )

    await callback.message.edit_text(
        text=payment_text,
        reply_markup=get_payment_keyboard(order_id, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_order:"))
async def process_pay_existing_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Оплата существующего заказа."""
    order_id = int(callback.data.split(":")[1])
    lang = await db.get_user_language(callback.from_user.id)
    order = await order_service.get_order_by_id(order_id)

    if not order or order.telegram_id != callback.from_user.id:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    await state.update_data(current_order_id=order_id, lang=lang)
    await state.set_state(OrderStates.waiting_receipt)

    payment_text = get_text(
        lang,
        "payment_screen",
        order_id=order.id,
        total_price=format_currency(order.total_price, lang=lang),
        payment_details=config.PAYMENT_DETAILS,
    )

    await callback.message.edit_text(
        text=payment_text,
        reply_markup=get_payment_keyboard(order.id, lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Прием чека об оплате ---

@router.message(OrderStates.waiting_receipt, F.photo | F.document)
async def process_payment_receipt(message: Message, state: FSMContext) -> None:
    """Прием скриншота чека об оплате."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    order_id = data.get("current_order_id")

    if not order_id:
        await state.clear()
        return

    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and (message.document.mime_type and ("image" in message.document.mime_type or "pdf" in message.document.mime_type)):
        file_id = message.document.file_id

    if not file_id:
        await message.answer(
            text=get_text(lang, "err_not_receipt"),
            reply_markup=get_payment_keyboard(order_id, lang=lang),
            parse_mode="HTML",
        )
        return

    await order_service.submit_payment_receipt(order_id, file_id)
    order = await order_service.get_order_by_id(order_id)
    photos = await db.get_order_photos(order_id)
    music = await db.get_order_music(order_id)

    await state.clear()

    await message.answer(
        text=get_text(lang, "receipt_received", order_id=order_id),
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )

    if order:
        await notifications.notify_admin_payment(
            bot=message.bot,
            order=order,
            receipt_file_id=file_id,
            username=message.from_user.username,
            photos_count=len(photos),
            has_music=music is not None,
        )


@router.message(OrderStates.waiting_receipt, ~F.photo & ~F.document)
async def process_invalid_receipt_format(message: Message, state: FSMContext) -> None:
    """Обработка неверного формата чека."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    order_id = data.get("current_order_id", 0)
    await message.answer(
        text=get_text(lang, "err_not_receipt"),
        reply_markup=get_payment_keyboard(order_id, lang=lang),
        parse_mode="HTML",
    )


# --- Генератор персональных именных ссылок для гостей ---

@router.callback_query(F.data.startswith("guest_links:"))
async def process_start_guest_links(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос списка имён гостей для создания персональных ссылок."""
    order_id = int(callback.data.split(":")[1])
    order = await order_service.get_order_by_id(order_id)
    lang = await db.get_user_language(callback.from_user.id)

    if not order or not order.website_url:
        await callback.answer("Сайт ещё не готов", show_alert=True)
        return

    await state.update_data(target_website_url=order.website_url, lang=lang)
    await state.set_state(OrderStates.entering_guest_names)

    await callback.message.answer(
        text=get_text(lang, "prompt_guest_names"),
        reply_markup=get_cancel_keyboard(lang=lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(OrderStates.entering_guest_names, F.text)
async def process_generate_guest_links(message: Message, state: FSMContext) -> None:
    """Генерация ссылок для каждого гостя."""
    import urllib.parse
    data = await state.get_data()
    lang = data.get("lang", "ru")
    base_url = data.get("target_website_url", "")

    raw_names = message.text.replace(",", "\n").split("\n")
    names = [n.strip() for n in raw_names if n.strip()]

    if not names:
        await message.answer("⚠️ Введите хотя бы одно имя.")
        return

    links_lines = []
    separator = "&" if "?" in base_url else "?"
    for i, name in enumerate(names[:30], 1):
        encoded = urllib.parse.quote_plus(name)
        personal_url = f"{base_url}{separator}guest={encoded}"
        links_lines.append(f"👤 <b>{escape(name)}:</b>\n🔗 <code>{personal_url}</code>")

    await state.clear()
    await message.answer(
        text=get_text(lang, "guest_links_ready", links_list="\n\n".join(links_lines)),
        reply_markup=get_main_menu_keyboard(lang=lang),
        parse_mode="HTML",
    )
