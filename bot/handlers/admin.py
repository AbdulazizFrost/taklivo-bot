"""
Обработчики панели администратора TAKLIVO (/admin).
Включает функции управления заказами, чеками, статистику, промокоды, рассылку и экспорт в Excel.
"""
import json
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.database import db, OrderStatus, PromoCode
from bot.keyboards import (
    get_admin_main_keyboard,
    get_admin_order_actions_keyboard,
    get_admin_status_selection_keyboard,
    get_admin_orders_list_keyboard,
    get_admin_back_keyboard,
    get_admin_users_keyboard,
    get_admin_promos_keyboard,
    get_admin_promo_card_keyboard,
    get_admin_broadcast_confirm_keyboard,
)
from bot.services import (
    order_service,
    notifications,
    site_generator,
    exporter,
    broadcaster,
)
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
        f"👥 <b>Пользователей в боте:</b> <code>{stats['total_users']}</code> чел. "
        f"(сегодня: +<code>{stats['today_users']}</code>, за месяц: +<code>{stats['month_users_reg']}</code>)\n"
        f"🌐 <b>Языки:</b> 🇺🇿 {stats['uz_users']} | 🇷🇺 {stats['ru_users']}\n\n"
        f"📊 <b>Всего заказов:</b> {stats['total_orders']}\n"
        f"💰 <b>Общая выручка:</b> {format_currency(stats['total_revenue'], 'ru')}\n"
        f"📅 <b>За текущий месяц:</b> {stats['month_orders']} заказов ({format_currency(stats['month_revenue'], 'ru')})\n\n"
        "Выберите раздел для управления:"
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
        f"👥 <b>Пользователей в боте:</b> <code>{stats['total_users']}</code> чел. "
        f"(сегодня: +<code>{stats['today_users']}</code>, за месяц: +<code>{stats['month_users_reg']}</code>)\n"
        f"🌐 <b>Языки:</b> 🇺🇿 {stats['uz_users']} | 🇷🇺 {stats['ru_users']}\n\n"
        f"📊 <b>Всего заказов:</b> {stats['total_orders']}\n"
        f"💰 <b>Общая выручка:</b> {format_currency(stats['total_revenue'], 'ru')}\n"
        f"📅 <b>За текущий месяц:</b> {stats['month_orders']} заказов ({format_currency(stats['month_revenue'], 'ru')})\n\n"
        "Выберите раздел для управления:"
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


# --- Просмотр пользователей бота ---

@router.callback_query(F.data == "adm:users")
async def callback_admin_users(callback: CallbackQuery) -> None:
    """Отображение детального списка и аналитики пользователей бота."""
    if not is_admin(callback.from_user.id):
        return

    stats = await order_service.get_system_statistics()
    recent_users = await db.get_recent_users(limit=15)

    user_lines = []
    for i, u in enumerate(recent_users, 1):
        uname = f"@{escape(u.username)}" if u.username else "<i>(без юзернейма)</i>"
        fname = escape(u.first_name or "Пользователь")
        lang_icon = "🇺🇿" if u.language == "uz" else "🇷🇺"
        date_str = u.created_at[:10] if u.created_at else "—"
        user_lines.append(f"{i}. <b>{fname}</b> ({uname})\n   └ ID: <code>{u.telegram_id}</code> | {lang_icon} {u.language.upper()} | <i>{date_str}</i>")

    users_list_text = "\n\n".join(user_lines) if user_lines else "<i>Пока нет зарегистрированных пользователей.</i>"

    total = max(stats['total_users'], 1)
    uz_pct = round((stats['uz_users'] / total) * 100)
    ru_pct = round((stats['ru_users'] / total) * 100)

    text = (
        "👥 <b>ПОЛЬЗОВАТЕЛИ БОТА TAKLIVO</b>\n\n"
        f"📈 <b>Общая статистика аудитории:</b>\n"
        f"• Всего пользователей в базе: <b>{stats['total_users']}</b> чел.\n"
        f"• Новых сегодня: +<b>{stats['today_users']}</b>\n"
        f"• Новых за текущий месяц: +<b>{stats['month_users_reg']}</b>\n\n"
        f"🌐 <b>Языковые предпочтения:</b>\n"
        f"• 🇺🇿 O‘zbek tili: <b>{stats['uz_users']}</b> ({uz_pct}%)\n"
        f"• 🇷🇺 Русский язык: <b>{stats['ru_users']}</b> ({ru_pct}%)\n\n"
        f"📋 <b>Последние 15 пользователей:</b>\n\n{users_list_text}"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_users_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Экспорт в Excel (CSV UTF-8 BOM) ---

@router.callback_query(F.data == "adm:export_excel")
async def callback_admin_export_excel(callback: CallbackQuery) -> None:
    """Генерирует и отправляет файлы Excel для пользователей и заказов."""
    if not is_admin(callback.from_user.id):
        return

    await callback.answer("⏳ Формирование файлов Excel...")
    try:
        users_file = await exporter.export_users_csv()
        orders_file = await exporter.export_orders_csv()

        doc_users = FSInputFile(path=users_file, filename=users_file.split("\\")[-1].split("/")[-1])
        doc_orders = FSInputFile(path=orders_file, filename=orders_file.split("\\")[-1].split("/")[-1])

        await callback.message.answer_document(
            document=doc_users,
            caption="📊 <b>Таблица пользователей TAKLIVO (Excel)</b>",
            parse_mode="HTML",
        )
        await callback.message.answer_document(
            document=doc_orders,
            caption="📦 <b>Таблица всех заказов TAKLIVO (Excel)</b>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта Excel: {e}")
        await callback.message.answer(f"⚠️ Ошибка при формировании Excel: {e}")


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
        f"👥 <b>Пользователи в боте:</b> {stats['total_users']} чел. (сегодня: +{stats['today_users']})\n"
        f"📦 <b>Всего оформлено заказов:</b> {stats['total_orders']}\n"
        f"💰 <b>Общий подтвержденный доход:</b> {format_currency(stats['total_revenue'], 'ru')}\n\n"
        f"📅 <b>В этом месяце:</b>\n"
        f"• Новых пользователей: <b>+{stats['month_users_reg']}</b>\n"
        f"• Заказов: <b>{stats['month_orders']}</b>\n"
        f"• Выручка: <b>{format_currency(stats['month_revenue'], 'ru')}</b>\n\n"
        f"📈 <b>Распределение заказов по статусам:</b>\n{status_text}"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Массовая рассылка по пользователям ---

@router.callback_query(F.data == "adm:broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало процесса рассылки."""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.entering_broadcast_message)
    await callback.message.edit_text(
        text=(
            "📢 <b>МАССОВАЯ РАССЫЛКА ПО ВСЕМ ПОЛЬЗОВАТЕЛЯМ</b>\n\n"
            "Отправьте сообщение (текст или фото с подписью), которое получат все пользователи бота."
        ),
        reply_markup=get_admin_back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.entering_broadcast_message)
async def process_broadcast_content(message: Message, state: FSMContext) -> None:
    """Прием контента рассылки и запрос опциональной кнопки."""
    if not is_admin(message.from_user.id):
        return

    # Сохраняем ID сообщения для рассылки
    await state.update_data(broadcast_message_id=message.message_id, broadcast_chat_id=message.chat.id)
    await state.set_state(AdminStates.entering_broadcast_button)

    await message.answer(
        text=(
            "🔗 <b>Добавить кнопку со ссылкой под постом?</b>\n\n"
            "Если нужна кнопка, отправьте её в формате:\n"
            "<code>Текст кнопки | https://ссылка.uz</code>\n\n"
            "<i>(или отправьте «-» или «нет» чтобы отправить без кнопки)</i>"
        ),
        parse_mode="HTML",
    )


@router.message(AdminStates.entering_broadcast_button, F.text)
async def process_broadcast_button(message: Message, state: FSMContext) -> None:
    """Обработка кнопки и подтверждение запуска."""
    if not is_admin(message.from_user.id):
        return

    btn_text_raw = message.text.strip()
    button_label = None
    button_url = None

    if "|" in btn_text_raw:
        parts = btn_text_raw.split("|", 1)
        button_label = parts[0].strip()
        button_url = parts[1].strip()

    await state.update_data(button_label=button_label, button_url=button_url)
    await state.set_state(AdminStates.confirming_broadcast)

    stats = await order_service.get_system_statistics()
    total_users = stats["total_users"]

    btn_info = f"• Кнопка: <b>{button_label}</b> ({button_url})\n" if button_label else "• Без кнопки\n"

    await message.answer(
        text=(
            "🚀 <b>ГОТОВНОСТЬ К РАССЫЛКЕ</b>\n\n"
            f"• Получателей: <b>{total_users}</b> чел.\n"
            f"{btn_info}\n"
            "Нажмите «Запустить рассылку» для старта."
        ),
        reply_markup=get_admin_broadcast_confirm_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(AdminStates.confirming_broadcast, F.data == "adm_bc:confirm")
async def callback_confirm_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    """Запуск рассылки."""
    if not is_admin(callback.from_user.id):
        return

    data = await state.get_data()
    msg_id = data.get("broadcast_message_id")
    chat_id = data.get("broadcast_chat_id")
    btn_label = data.get("button_label")
    btn_url = data.get("button_url")
    await state.clear()

    await callback.message.edit_text("⏳ Рассылка выполняется в фоновом режиме...")

    # Получаем исходное сообщение через copy
    # Для рассылки передаем сохраненные параметры
    users = await db.get_all_users()
    sent = 0
    blocked = 0
    failed = 0

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = None
    if btn_label and btn_url:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=btn_label, url=btn_url)]])

    import asyncio
    for u in users:
        try:
            await callback.bot.copy_message(
                chat_id=u.telegram_id,
                from_chat_id=chat_id,
                message_id=msg_id,
                reply_markup=keyboard,
            )
            sent += 1
        except Exception:
            blocked += 1
        await asyncio.sleep(0.04)

    await callback.message.answer(
        text=(
            "✅ <b>РАССЫЛКА ЗАВЕРШЕНА!</b>\n\n"
            f"• Всего пользователей: <b>{len(users)}</b>\n"
            f"• Успешно доставлено: <b>{sent}</b>\n"
            f"• Заблокировали/Недоступны: <b>{blocked}</b>"
        ),
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Управление промокодами ---

@router.callback_query(F.data == "adm:promos")
async def callback_admin_promos(callback: CallbackQuery) -> None:
    """Список промокодов."""
    if not is_admin(callback.from_user.id):
        return

    promos = await db.get_all_promocodes()
    await callback.message.edit_text(
        text="🎟 <b>УПРАВЛЕНИЕ ПРОМОКОДАМИ И СКИДКАМИ</b>\n\nВыберите промокод или создайте новый:",
        reply_markup=get_admin_promos_keyboard(promos),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "adm_promo:create")
async def callback_admin_start_promo_create(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало создания промокода."""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.entering_promo_code)
    await callback.message.edit_text(
        text=(
            "🎟 <b>Введите кодовое слово промокода</b>\n\n"
            "<i>(например: OQSAROY2026 или WEDDING10)</i>"
        ),
        reply_markup=get_admin_back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.entering_promo_code, F.text)
async def process_promo_code_text(message: Message, state: FSMContext) -> None:
    """Ввод названия промокода."""
    if not is_admin(message.from_user.id):
        return

    code = message.text.strip().upper()
    await state.update_data(new_promo_code=code)
    await state.set_state(AdminStates.entering_promo_discount)

    await message.answer(
        text=(
            f"🎟 Промокод: <b>{code}</b>\n\n"
            "<b>Введите размер скидки:</b>\n"
            "• В процентах: напишите например <code>15%</code> или <code>20%</code>\n"
            "• Фиксированная сумма в сумах: напишите например <code>20000</code>"
        ),
        parse_mode="HTML",
    )


@router.message(AdminStates.entering_promo_discount, F.text)
async def process_promo_discount(message: Message, state: FSMContext) -> None:
    """Ввод скидки промокода."""
    if not is_admin(message.from_user.id):
        return

    val = message.text.strip()
    percent = 0
    amount = 0

    if "%" in val:
        try:
            percent = int(val.replace("%", "").strip())
        except ValueError:
            percent = 10
    else:
        try:
            amount = int(val.replace(" ", "").strip())
        except ValueError:
            amount = 15000

    await state.update_data(new_promo_percent=percent, new_promo_amount=amount)
    await state.set_state(AdminStates.entering_promo_limit)

    await message.answer(
        text="🔢 <b>Введите лимит использований</b> (например: <code>50</code> или <code>100</code>):",
        parse_mode="HTML",
    )


@router.message(AdminStates.entering_promo_limit, F.text)
async def process_promo_limit(message: Message, state: FSMContext) -> None:
    """Сохранение промокода."""
    if not is_admin(message.from_user.id):
        return

    try:
        limit = int(message.text.strip())
    except ValueError:
        limit = 100

    data = await state.get_data()
    code = data.get("new_promo_code", "PROMO")
    percent = data.get("new_promo_percent", 0)
    amount = data.get("new_promo_amount", 0)
    await state.clear()

    await db.create_promocode(
        code=code,
        discount_percent=percent,
        discount_amount=amount,
        max_uses=limit,
    )

    discount_label = f"{percent}%" if percent > 0 else f"{amount:,} сум"
    await message.answer(
        text=(
            f"✅ <b>Промокод {code} успешно создан!</b>\n\n"
            f"• Скидка: <b>{discount_label}</b>\n"
            f"• Лимит использований: <b>{limit}</b>"
        ),
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("adm_promo_view:"))
async def callback_admin_promo_view(callback: CallbackQuery) -> None:
    """Просмотр отдельного промокода."""
    if not is_admin(callback.from_user.id):
        return

    promo_id = int(callback.data.split(":")[1])
    promos = await db.get_all_promocodes()
    target = next((p for p in promos if p.id == promo_id), None)

    if not target:
        await callback.answer("Промокод не найден", show_alert=True)
        return

    discount_label = f"{target.discount_percent}%" if target.discount_percent > 0 else f"{target.discount_amount:,} сум"
    text = (
        f"🎟 <b>ПРОМОКОД: {target.code}</b>\n\n"
        f"• Скидка: <b>{discount_label}</b>\n"
        f"• Использовано: <b>{target.used_count}</b> из <b>{target.max_uses}</b>\n"
        f"• Дата создания: <i>{target.created_at[:10]}</i>"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_promo_card_keyboard(target.id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_promo_del:"))
async def callback_admin_promo_delete(callback: CallbackQuery) -> None:
    """Удаление промокода."""
    if not is_admin(callback.from_user.id):
        return

    promo_id = int(callback.data.split(":")[1])
    await db.delete_promocode(promo_id)
    await callback.answer("Промокод удален!")
    await callback_admin_promos(callback)


# --- Просмотр заказов по фильтрам ---

@router.callback_query(F.data.startswith("adm_filter:"))
async def callback_admin_filter_orders(callback: CallbackQuery, state: FSMContext) -> None:
    """Фильтрация заказов по категориям статусов."""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    status_filter = callback.data.split(":")[1]
    orders = await order_service.get_orders_by_status_category(status_filter)

    filter_names = {
        "PAYMENT_REVIEW": "⏳ На проверке оплаты",
        "IN_PROGRESS": "🔨 В работе у дизайнера",
        "PREVIEW": "👀 На проверке клиентом",
        "REVISION": "✏️ С правками",
        "COMPLETED": "🎉 Завершённые",
        "ALL": "📋 Все заказы",
    }

    title = filter_names.get(status_filter, status_filter)
    if not orders:
        await callback.message.edit_text(
            text=f"📋 <b>{title}</b>\n\n<i>В этой категории пока нет заказов.</i>",
            reply_markup=get_admin_back_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        text=f"📋 <b>{title}</b> (Найдено: {len(orders)}):\n\nВыберите заказ для детального просмотра:",
        reply_markup=get_admin_orders_list_keyboard(orders, status_filter),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "adm:back_to_list")
async def callback_admin_back_to_list(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат к полному списку заказов."""
    if not is_admin(callback.from_user.id):
        return
    orders = await order_service.get_orders_by_status_category("ALL")
    await callback.message.edit_text(
        text="📋 <b>Все заказы:</b>",
        reply_markup=get_admin_orders_list_keyboard(orders, "ALL"),
        parse_mode="HTML",
    )
    await callback.answer()


# --- Детальный просмотр заказа администратором ---

@router.callback_query(F.data.startswith("adm_order:"))
async def callback_admin_view_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Детальная карточка заказа для администратора."""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    order_id = int(callback.data.split(":")[1])
    order = await order_service.get_order_by_id(order_id)

    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    photos = await db.get_order_photos(order_id)
    music = await db.get_order_music(order_id)

    card_text = order_service.format_admin_notification(
        order=order,
        photos_count=len(photos),
        has_music=music is not None,
    )

    if order.website_url:
        card_text += f"\n\n🌐 <b>Ссылка на сайт:</b> <a href='{order.website_url}'>{order.website_url}</a>"

    if order.revision_text:
        card_text += f"\n\n✏️ <b>Пожелания по правкам:</b>\n<i>{escape(order.revision_text)}</i>"

    await callback.message.edit_text(
        text=card_text,
        reply_markup=get_admin_order_actions_keyboard(order),
        parse_mode="HTML",
        disable_web_page_preview=False,
    )
    await callback.answer()


# --- Подтверждение / Отклонение оплаты администратором ---

@router.callback_query(F.data.startswith("adm_pay_ok:"))
async def callback_admin_confirm_payment(callback: CallbackQuery) -> None:
    """Администратор нажимает «✅ Подтвердить оплату»."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    success, updated_order = await order_service.confirm_order_payment(order_id)

    if not success or not updated_order:
        await callback.answer("Ошибка при подтверждении", show_alert=True)
        return

    await callback.answer("Оплата подтверждена!", show_alert=True)
    await notifications.notify_client_payment_confirmed(
        bot=callback.bot,
        telegram_id=updated_order.telegram_id,
        order_id=updated_order.id,
    )

    await callback.message.edit_text(
        text=f"✅ <b>Оплата по заказу #{order_id} успешно подтверждена!</b>\n\nСтатус заказа изменен на <code>IN_PROGRESS</code> (В работе). Клиент получил оповещение.",
        reply_markup=get_admin_order_actions_keyboard(updated_order),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("adm_pay_rej:"))
async def callback_admin_reject_payment(callback: CallbackQuery) -> None:
    """Администратор нажимает «❌ Отклонить оплату»."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    success, updated_order = await order_service.reject_order_payment(order_id)

    if not success or not updated_order:
        await callback.answer("Ошибка при отклонении", show_alert=True)
        return

    await callback.answer("Оплата отклонена", show_alert=True)
    await notifications.notify_client_payment_rejected(
        bot=callback.bot,
        telegram_id=updated_order.telegram_id,
        order_id=updated_order.id,
    )

    await callback.message.edit_text(
        text=f"❌ <b>Оплата по заказу #{order_id} отклонена.</b>\n\nЗаказ возвращен в статус ожидания оплаты. Клиент оповещен.",
        reply_markup=get_admin_order_actions_keyboard(updated_order),
        parse_mode="HTML",
    )


# --- Отправка ссылки на готовый сайт клиенту ---

@router.callback_query(F.data.startswith("adm_send_url:"))
async def callback_admin_start_send_url(callback: CallbackQuery, state: FSMContext) -> None:
    """Администратор нажимает «🌐 Отправить ссылку на сайт»."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    await state.update_data(target_order_id=order_id)
    await state.set_state(AdminStates.entering_website_url)

    await callback.message.answer(
        text=(
            f"🌐 <b>Введите ссылку на готовый сайт для заказа #{order_id}:</b>\n\n"
            f"<i>Пример: https://taklivo.uz/wedding/aziz-malika</i>"
        ),
        reply_markup=get_admin_back_keyboard(order_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.entering_website_url, F.text)
async def process_admin_entered_url(message: Message, state: FSMContext) -> None:
    """Прием и валидация URL готового сайта."""
    if not is_admin(message.from_user.id):
        return

    url = message.text.strip()
    if not validate_url(url):
        await message.answer("⚠️ <b>Некорректная ссылка!</b> Введите валидный URL (начинающийся с http:// или https://).")
        return

    data = await state.get_data()
    order_id = data.get("target_order_id")
    await state.clear()

    if not order_id:
        await message.answer("Ошибка: номер заказа не найден.")
        return

    success, updated_order = await order_service.set_website_url_for_order(order_id, url)
    if not success or not updated_order:
        await message.answer("Ошибка обновления заказа.")
        return

    await notifications.notify_client_website_ready(
        bot=message.bot,
        telegram_id=updated_order.telegram_id,
        order_id=updated_order.id,
        website_url=url,
        order=updated_order,
    )

    await message.answer(
        text=f"🎉 <b>Ссылка на сайт для заказа #{order_id} успешно отправлена клиенту!</b>\n\nСтатус заказа переведен в <code>PREVIEW</code> (На проверке).",
        reply_markup=get_admin_order_actions_keyboard(updated_order),
        parse_mode="HTML",
    )


# --- Просмотр медиафайлов заказа ---

@router.callback_query(F.data.startswith("adm_view_photos:"))
async def callback_admin_view_photos(callback: CallbackQuery) -> None:
    """Отправка всех фото заказа в виде медиа-группы."""
    if not is_admin(callback.from_user.id):
        return

    order_id = int(callback.data.split(":")[1])
    photos = await db.get_order_photos(order_id)

    if not photos:
        await callback.answer("К этому заказу нет фотографий", show_alert=True)
        return

    await callback.answer("Загрузка фотографий...")
    media_group = [InputMediaPhoto(media=p.file_id) for p in photos[:10]]

    try:
        await callback.message.answer_media_group(media=media_group)
    except Exception as e:
        logger.error(f"Ошибка отправки медиа-группы: {e}")
        await callback.message.answer(f"⚠️ Ошибка отправки фото: {e}")


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

    await callback.answer("Загрузка чека...")
    try:
        await callback.message.answer_photo(
            photo=order.payment_receipt_file_id,
            caption=f"🧾 <b>Чек об оплате к заказу #{order.id}</b>\nСумма: {format_currency(order.total_price, 'ru')}",
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer_document(
            document=order.payment_receipt_file_id,
            caption=f"🧾 <b>Документ чека к заказу #{order.id}</b>",
            parse_mode="HTML",
        )


# --- Экспорт JSON для генератора сайта ---

@router.callback_query(F.data.startswith("adm_export_json:"))
async def callback_admin_export_json(callback: CallbackQuery) -> None:
    """Выгрузка JSON данных заказа."""
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
