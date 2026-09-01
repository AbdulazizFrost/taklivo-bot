"""
Обработчики панели администратора TAKLIVO (/admin).
Включает функции управления заказами, чеками, статистику и выгрузку бэкапа базы данных.
"""
import json
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.database import db, OrderStatus
from bot.keyboards import (
    get_admin_main_keyboard,
    get_admin_order_actions_keyboard,
    get_admin_status_selection_keyboard,
    get_admin_orders_list_keyboard,
    get_admin_back_keyboard,
)
from bot.services import order_service, notifications, site_generator
from bot.states.admin import AdminStates
from bot.utils.helpers import format_currency, get_status_badge, escape
from bot.utils.validators import validate_url
from config import config

router = Router(name="admin_router")
logger = logging.getLogger(__name__)


def is_admin(telegram_id: int) -> bool:
    """Проверка прав администратора."""
    return telegram_id in config.ADMIN_IDS


# --- Вход в панель администратора ---

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """Открытие главной панели управления администратора."""
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    stats = await order_service.get_system_statistics()
    text = (
        "👑 <b>ПАНЕЛЬ АДМИНИСТРАТОРА TAKLIVO</b>\n\n"
        f"📊 <b>Всего заказов:</b> {stats['total_orders']}\n"
        f"💰 <b>Общая выручка:</b> {format_currency(stats['total_revenue'], 'ru')}\n"
        f"📅 <b>За текущий месяц:</b> {stats['month_orders']} заказов ({format_currency(stats['month_revenue'], 'ru')})\n\n"
        "Выберите раздел для управления заказами:"
    )

    await message.answer(
        text=text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm:main")
async def callback_admin_main(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню админки."""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    stats = await order_service.get_system_statistics()
    text = (
        "👑 <b>ПАНЕЛЬ АДМИНИСТРАТОРА TAKLIVO</b>\n\n"
        f"📊 <b>Всего заказов:</b> {stats['total_orders']}\n"
        f"💰 <b>Общая выручка:</b> {format_currency(stats['total_revenue'], 'ru')}\n"
        f"📅 <b>За текущий месяц:</b> {stats['month_orders']} заказов ({format_currency(stats['month_revenue'], 'ru')})\n\n"
        "Выберите раздел для управления заказами:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "adm:refresh")
async def callback_admin_refresh(callback: CallbackQuery, state: FSMContext) -> None:
    """Обновление данных главной панели."""
    if not is_admin(callback.from_user.id):
        return
    await callback_admin_main(callback, state)


# --- Резервная копия базы данных (Backup) ---

@router.callback_query(F.data == "adm:backup_db")
async def callback_admin_backup_db(callback: CallbackQuery) -> None:
    """Создает резервный снимок базы данных и отправляет файл администратору."""
    if not is_admin(callback.from_user.id):
        return

    await callback.answer("⏳ Создание бэкапа базы данных...")
    backup_file_path = db.create_backup_copy()

    try:
        document = FSInputFile(path=backup_file_path, filename=backup_file_path.split("\\")[-1].split("/")[-1])
        await callback.message.answer_document(
            document=document,
            caption=(
                "💾 <b>Резервная копия базы данных SQLite</b>\n\n"
                "Все пользователи, заказы, фото и настройки сохранены в файле выше.\n"
                "Файл бэкапа защищен от повреждений и содержит полную историю сервиса."
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Ошибка отправки файла бэкапа: {e}")
        await callback.message.answer(f"⚠️ Ошибка при создании бэкапа: {e}")


# --- Статистика и аналитика ---

@router.callback_query(F.data == "adm:stats")
async def callback_admin_stats(callback: CallbackQuery) -> None:
    """Отображение расширенной статистики."""
    if not is_admin(callback.from_user.id):
        return

    stats = await order_service.get_system_statistics()
    counts = stats["status_counts"]

    status_lines = []
    for st, cnt in counts.items():
        badge = get_status_badge(st, "ru")
        status_lines.append(f"• {badge}: <b>{cnt}</b>")

    status_text = "\n".join(status_lines) if status_lines else "Нет заказов"

    text = (
        "📊 <b>ДЕТАЛЬНАЯ АНАЛИТИКА TAKLIVO</b>\n\n"
        f"📦 <b>Всего оформлено заказов:</b> {stats['total_orders']}\n"
        f"💰 <b>Общий подтвержденный доход:</b> {format_currency(stats['total_revenue'], 'ru')}\n\n"
        f"📅 <b>В этом месяце:</b>\n"
        f"• Заказов: <b>{stats['month_orders']}</b>\n"
        f"• Выручка: <b>{format_currency(stats['month_revenue'], 'ru')}</b>\n\n"
        f"📈 <b>Распределение по статусам:</b>\n{status_text}"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Просмотр заказов по фильтрам ---

@router.callback_query(F.data.startswith("adm_filter:"))
async def callback_admin_filter_orders(callback: CallbackQuery, state: FSMContext) -> None:
    """Фильтрация заказов по категориям статусов."""
    if not is_admin(callback.from_user.id):
        return

    status_filter = callback.data.split(":")[1]
    await state.update_data(current_filter=status_filter)
    orders = await order_service.get_orders_by_status_category(status_filter)

    titles = {
        "PAYMENT_REVIEW": "⏳ Заказы на проверке оплаты:",
        "IN_PROGRESS": "🔨 Заказы в работе у дизайнера:",
        "PREVIEW": "👀 Заказы на проверке клиентом:",
        "REVISION": "✏️ Заказы с запрошенными правками:",
        "COMPLETED": "🎉 Завершенные заказы:",
        "ALL": "📋 Все заказы сервиса:",
    }
    title = titles.get(status_filter, "Список заказов:")

    if not orders:
        text = f"{title}\n\n<i>Заказов в данной категории пока нет.</i>"
    else:
        text = f"{title}\nНажмите на заказ для управления:"

    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_orders_list_keyboard(orders, status_filter),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "adm:back_to_list")
async def callback_admin_back_to_list(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат к предыдущему списку заказов."""
    if not is_admin(callback.from_user.id):
        return
    data = await state.get_data()
    status_filter = data.get("current_filter", "ALL")
    orders = await order_service.get_orders_by_status_category(status_filter)
    await callback.message.edit_text(
        text="Список заказов:",
        reply_markup=get_admin_orders_list_keyboard(orders, status_filter),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Карточка отдельного заказа в админке ---

@router.callback_query(F.data.startswith("adm_order:"))
async def callback_admin_view_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Детальный просмотр карточки заказа."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    order = await order_service.get_order_by_id(order_id)

    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return

    await state.update_data(current_admin_order_id=order_id)
    photos = await db.get_order_photos(order_id)
    music = await db.get_order_music(order_id)

    info_text = order_service.format_admin_notification(
        order=order,
        photos_count=len(photos),
        has_music=music is not None,
    )

    if order.website_url:
        info_text += f"\n\n🌐 <b>Сайт:</b> <a href='{order.website_url}'>{order.website_url}</a>"
    if order.revision_text:
        info_text += f"\n\n✏️ <b>Текст правок от клиента:</b>\n<i>{escape(order.revision_text)}</i>"

    await callback.message.edit_text(
        text=info_text,
        reply_markup=get_admin_order_actions_keyboard(order),
        parse_mode="HTML",
        disable_web_page_preview=False,
    )
    await callback.answer()


# --- Подтверждение / отклонение оплаты ---

@router.callback_query(F.data.startswith("adm_pay_ok:"))
async def callback_admin_confirm_payment(callback: CallbackQuery, state: FSMContext) -> None:
    """Администратор подтверждает оплату."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    ok, order = await order_service.confirm_order_payment(order_id)

    if ok and order:
        await callback.answer("✅ Оплата подтверждена!")
        user_lang = await db.get_user_language(order.telegram_id)
        await notifications.notify_client_payment_confirmed(callback.bot, order, user_lang)
        await callback_admin_view_order(callback, state)
    else:
        await callback.answer("Ошибка при подтверждении", show_alert=True)


@router.callback_query(F.data.startswith("adm_pay_rej:"))
async def callback_admin_reject_payment(callback: CallbackQuery, state: FSMContext) -> None:
    """Администратор отклоняет оплату."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    ok, order = await order_service.reject_order_payment(order_id)

    if ok and order:
        await callback.answer("❌ Оплата отклонена.")
        user_lang = await db.get_user_language(order.telegram_id)
        await notifications.notify_client_payment_rejected(callback.bot, order, user_lang)
        await callback_admin_view_order(callback, state)
    else:
        await callback.answer("Ошибка при отклонении", show_alert=True)


# --- Отправка ссылки на готовый сайт клиенту ---

@router.callback_query(F.data.startswith("adm_send_url:"))
async def callback_admin_start_send_url(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос ввода ссылки на готовый сайт."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    await state.update_data(target_order_id=order_id)
    await state.set_state(AdminStates.entering_website_url)

    await callback.message.answer(
        text=(
            f"🌐 <b>Отправка ссылки на сайт по заказу #{order_id}</b>\n\n"
            "Отправьте URL сайта (например: <code>https://taklivo.uz/wedding/aziz-malika</code>):"
        ),
        reply_markup=get_admin_back_keyboard(order_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.entering_website_url, F.text)
async def process_admin_entered_url(message: Message, state: FSMContext) -> None:
    """Прием и валидация ссылки на сайт, сохранение и отправка клиенту."""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    order_id = data.get("target_order_id")
    url = message.text.strip()

    if not validate_url(url):
        await message.answer(
            "⚠️ <b>Некорректная ссылка!</b> Пожалуйста, отправьте валидный URL (начинается с http:// или https://):",
            parse_mode="HTML",
        )
        return

    ok, order = await order_service.set_website_url_for_order(order_id, url)
    await state.clear()

    if ok and order:
        user_lang = await db.get_user_language(order.telegram_id)
        await notifications.notify_client_site_ready(
            bot=message.bot,
            order=order,
            website_url=url,
            lang=user_lang,
        )
        await message.answer(
            f"✅ <b>Ссылка успешно сохранена и отправлена клиенту!</b>\n\n🔗 {url}\nСтатус заказа переведен в <code>PREVIEW</code>.",
            reply_markup=get_admin_back_keyboard(order.id),
            parse_mode="HTML",
        )
    else:
        await message.answer("⚠️ Не удалось обновить заказ.")


# --- Просмотр чека и фотографий ---

@router.callback_query(F.data.startswith("adm_view_receipt:"))
async def callback_admin_view_receipt(callback: CallbackQuery) -> None:
    """Показ чека об оплате."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    order = await order_service.get_order_by_id(order_id)

    if not order or not order.payment_receipt_file_id:
        await callback.answer("Чек не прикреплен", show_alert=True)
        return

    await callback.message.answer_photo(
        photo=order.payment_receipt_file_id,
        caption=f"🧾 <b>Чек по заказу #{order.id}</b>\nСумма: {format_currency(order.total_price, 'ru')}",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_view_photos:"))
async def callback_admin_view_photos(callback: CallbackQuery) -> None:
    """Выгрузка всех фотографий заказа."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    photos = await db.get_order_photos(order_id)

    if not photos:
        await callback.answer("К этому заказу нет фотографий", show_alert=True)
        return

    await callback.answer("Загрузка фотографий...")
    media_group = [
        InputMediaPhoto(media=p.file_id, caption=f"📸 Фото {idx+1}/{len(photos)} (Заказ #{order_id})")
        for idx, p in enumerate(photos[:10])
    ]
    await callback.message.answer_media_group(media=media_group)


# --- Экспорт JSON для генератора сайтов ---

@router.callback_query(F.data.startswith("adm_export_json:"))
async def callback_admin_export_json(callback: CallbackQuery) -> None:
    """Выгрузка структурированного JSON для генерации сайта."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    order = await order_service.get_order_by_id(order_id)
    photos = await db.get_order_photos(order_id)
    music = await db.get_order_music(order_id)

    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    json_str = site_generator.export_order_to_json(order, photos, music)
    await callback.message.answer(
        text=f"📄 <b>JSON ДАННЫЕ ДЛЯ ГЕНЕРАЦИИ САЙТА #{order.id}:</b>\n\n<code>{escape(json_str)}</code>",
        parse_mode="HTML",
    )
    await callback.answer()


# --- Отправка сообщения клиенту через бота ---

@router.callback_query(F.data.startswith("adm_msg_client:"))
async def callback_admin_start_msg_client(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос текста сообщения клиенту."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    await state.update_data(msg_target_order_id=order_id)
    await state.set_state(AdminStates.entering_client_message)

    await callback.message.answer(
        text=f"✉️ <b>Введите сообщение, которое будет отправлено клиенту по заказу #{order_id}:</b>",
        reply_markup=get_admin_back_keyboard(order_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.entering_client_message, F.text)
async def process_admin_client_message(message: Message, state: FSMContext) -> None:
    """Отправка сообщения клиенту."""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    order_id = data.get("msg_target_order_id")
    order = await order_service.get_order_by_id(order_id)
    await state.clear()

    if not order:
        await message.answer("Заказ не найден.")
        return

    try:
        await message.bot.send_message(
            chat_id=order.telegram_id,
            text=f"💬 <b>Сообщение от администрации TAKLIVO по заказу #{order.id}:</b>\n\n{escape(message.text)}",
            parse_mode="HTML",
        )
        await message.answer(
            "✅ <b>Сообщение успешно доставлено клиенту!</b>",
            reply_markup=get_admin_back_keyboard(order.id),
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось доставить сообщение: {e}")


# --- Ручная смена статуса заказа ---

@router.callback_query(F.data.startswith("adm_change_st:"))
async def callback_admin_change_status(callback: CallbackQuery) -> None:
    """Выбор нового статуса для заказа."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        text=f"⚙️ <b>Выберите новый статус для заказа #{order_id}:</b>",
        reply_markup=get_admin_status_selection_keyboard(order_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_st:"))
async def callback_admin_set_status(callback: CallbackQuery, state: FSMContext) -> None:
    """Установка выбранного статуса."""
    if not is_admin(callback.from_user.id):
        return

    parts = callback.data.split(":")
    order_id = int(parts[1])
    new_status = parts[2]

    await db.update_order_status(order_id, new_status)
    await callback.answer(f"Статус изменен на {new_status}")
    await callback_admin_view_order(callback, state)
