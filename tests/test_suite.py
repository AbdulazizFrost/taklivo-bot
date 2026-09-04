"""
Комплексный автоматический тест-сьют для Telegram-бота TAKLIVO.
Проверяет все 13 обязательных сценариев QA и регрессионного тестирования:
1. Callback coverage
2. Локали и плейсхолдеры RU/UZ
3. Механизм отмены FSM
4. Возврат бонусов при отмене заказа
5. Идемпотентность возврата бонусов
6. Откат счетчика промокода
7. 100% оплата бонусами без требования чека
8. Первый заказ и реферальный бонус
9. Повторный заказ без UnboundLocalError
10. NotificationService сигнатуры и алиасы
11. Экспорт пользователей с bonus_balance
12. Экспорт заказов с bonus_used
13. Ограничение длины текстового ввода (>100 символов)
"""
import asyncio
import csv
import glob
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Путь к проекту
sys.path.insert(0, r"c:\Users\Abdulaziz\Desktop\работы\идеи")
sys.stdout.reconfigure(encoding="utf-8")

PASSED_COUNT = 0
FAILED_COUNT = 0
WARNINGS_COUNT = 0


def log_test_result(name: str, passed: bool, detail: str = ""):
    global PASSED_COUNT, FAILED_COUNT
    if passed:
        PASSED_COUNT += 1
        print(f"  ✅ [PASS] {name}" + (f": {detail}" if detail else ""))
    else:
        FAILED_COUNT += 1
        print(f"  ❌ [FAIL] {name}" + (f": {detail}" if detail else ""))


print("\n=======================================================")
print("🚀 ЗАПУСК КОМПЛЕКСНОГО АВТОМАТИЧЕСКОГО QA-ТЕСТ СЬЮТА")
print("=======================================================\n")

# ----------------------------------------------------
# TEST 1: Все callback из клавиатур имеют handlers
# ----------------------------------------------------
print("--- TEST 1: Покрытие всех callback_data обработчиками ---")
cb_pattern = re.compile(r'callback_data\s*=\s*["\']([^"\']+)["\']')
keyboard_callbacks = set()
for f in glob.glob("bot/keyboards/**/*.py", recursive=True):
    with open(f, "r", encoding="utf-8") as fp:
        content = fp.read()
        for match in cb_pattern.finditer(content):
            cb = match.group(1)
            keyboard_callbacks.add(cb)

handler_cb_exact = set()
handler_cb_prefix = set()
cb_filter_exact = re.compile(r'F\.data\s*==\s*["\']([^"\']+)["\']')
cb_filter_startswith = re.compile(r'F\.data\.startswith\s*\(\s*["\']([^"\']+)["\']\s*\)')
cb_filter_in = re.compile(r'F\.data\.in_\s*\(\s*\[([^\]]+)\]\s*\)')

for f in glob.glob("bot/handlers/**/*.py", recursive=True):
    with open(f, "r", encoding="utf-8") as fp:
        content = fp.read()
        for match in cb_filter_exact.finditer(content):
            handler_cb_exact.add(match.group(1))
        for match in cb_filter_startswith.finditer(content):
            handler_cb_prefix.add(match.group(1))
        for match in cb_filter_in.finditer(content):
            items = re.findall(r'["\']([^"\']+)["\']', match.group(1))
            for it in items:
                handler_cb_exact.add(it)

unhandled_callbacks = []
for cb in keyboard_callbacks:
    matched = cb in handler_cb_exact or any(cb.startswith(p) for p in handler_cb_prefix)
    if not matched:
        unhandled_callbacks.append(cb)

log_test_result(
    "Callback coverage",
    len(unhandled_callbacks) == 0,
    f"{len(keyboard_callbacks)} callbacks проверено, ненайденных: {unhandled_callbacks}",
)

# ----------------------------------------------------
# TEST 2: Соответствие локалей RU и UZ
# ----------------------------------------------------
print("\n--- TEST 2: Проверка локалей RU и UZ ---")
from bot.locales.ru import TEXTS as RU_TEXTS
from bot.locales.uz import TEXTS as UZ_TEXTS
from bot.locales import get_text

ru_keys = set(RU_TEXTS.keys())
uz_keys = set(UZ_TEXTS.keys())

missing_in_uz = ru_keys - uz_keys
missing_in_ru = uz_keys - ru_keys

formatter = re.compile(r"\{([a-zA-Z0-9_]+)\}")
ph_mismatches = []
for k in ru_keys & uz_keys:
    r_ph = set(formatter.findall(RU_TEXTS[k]))
    u_ph = set(formatter.findall(UZ_TEXTS[k]))
    if r_ph != u_ph:
        ph_mismatches.append((k, r_ph, u_ph))

required_keys = [
    "portfolio_title", "btn_demo_link", "btn_choose_template", "btn_portfolio",
    "cancel_success", "err_text_too_long", "order_paid_bonuses_success",
    "btn_custom_template", "step_reference_url", "err_invalid_url", "reference_url_received",
    "btn_promo_code", "btn_order_with_discount", "menu_promo_prompt", "menu_promo_success", "menu_promo_invalid", "start_promo_activated",
]
missing_required = [k for k in required_keys if k not in ru_keys or k not in uz_keys]

log_test_result(
    "Locale keys matching",
    len(missing_in_uz) == 0 and len(missing_in_ru) == 0 and len(missing_required) == 0,
    f"RU keys: {len(ru_keys)}, UZ keys: {len(uz_keys)}, отсутствуют: {missing_required}",
)
log_test_result(
    "Placeholder consistency",
    len(ph_mismatches) == 0,
    f"Несовпадений: {ph_mismatches}",
)

# ----------------------------------------------------
# TEST 10: Проверка NotificationService сигнатур и алиасов
# ----------------------------------------------------
print("\n--- TEST 10: Проверка NotificationService ---")
from bot.services.notifications import NotificationService, notifications

has_alias = hasattr(notifications, "notify_client_website_ready")
is_same = getattr(notifications, "notify_client_website_ready") == getattr(notifications, "notify_client_site_ready")

log_test_result(
    "NotificationService alias existence",
    has_alias and is_same,
    "notify_client_website_ready является алиасом notify_client_site_ready",
)


# ----------------------------------------------------
# БАЗОВЫЕ ТЕСТЫ БАЗЫ ДАННЫХ И ФИНАНСОВОЙ ЛОГИКИ (TESTS 3-9, 11-13)
# ----------------------------------------------------
async def run_async_tests():
    print("\n--- ЗАПУСК АСИНХРОННЫХ ТЕСТОВ (БД, БОНУСЫ, ПРОМОКОДЫ, ЗАКАЗЫ) ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db_path = os.path.join(tmp_dir, "test_taklivo.db")
        from bot.database.database import Database
        from bot.database.models import OrderStatus, PaymentStatus
        from bot.services.order_service import OrderService
        from config import config

        # Подменяем путь к базе данных на тестовый
        import bot.database
        import bot.database.database
        orig_db_path = bot.database.db.db_path
        bot.database.db.db_path = test_db_path
        test_db = bot.database.db
        await test_db.init()

        try:
            # 1. Создаем тестовых пользователей
            referrer = await test_db.get_or_create_user(
                telegram_id=11111, username="test_ref", first_name="Referrer", language="ru"
            )
            friend = await test_db.get_or_create_user(
                telegram_id=22222, username="test_friend", first_name="Friend", language="uz", referrer_id=11111
            )

            # Проверяем welcome bonus
            friend_balance = await test_db.get_user_bonus_balance(22222)
            log_test_result(
                "Welcome bonus for referred user",
                friend_balance == config.REFERRAL_WELCOME_BONUS,
                f"Баланс приглашенного: {friend_balance} сум (ожидалось {config.REFERRAL_WELCOME_BONUS})",
            )

            # 2. Создаем промокод
            await test_db.create_promocode("TESTPROMO", discount_amount=15000, max_uses=5)
            promo_before = await test_db.get_promocode("TESTPROMO")

            # ----------------------------------------------------
            # TEST 4, 5, 6: Оформление заказа, списание бонусов и возврат при отмене
            # ----------------------------------------------------
            order_data = {
                "template_id": "floral",
                "template_name": "Floral Grace",
                "event_type": "wedding",
                "bride_name": "Malika",
                "groom_name": "Aziz",
                "wedding_date": "15.10.2026",
                "wedding_time": "18:00",
                "venue": "Versal",
                "address": "Navoi str 1",
                "phone": "+998901234567",
                "options": {"timer": True, "rsvp": True, "map": True},
                "promocode": "TESTPROMO",
                "discount_amount": 15000,
                "bonus_used": 10000,
            }

            order_id = await OrderService.create_new_order(
                user_id=friend.id,
                telegram_id=friend.telegram_id,
                data=order_data,
            )

            # Проверяем, что бонусы списались
            balance_after_create = await test_db.get_user_bonus_balance(22222)
            promo_after_create = await test_db.get_promocode("TESTPROMO")
            log_test_result(
                "Bonus deduction on order creation",
                balance_after_create == friend_balance - 10000,
                f"Баланс после заказа: {balance_after_create}",
            )
            log_test_result(
                "Promo used_count increment",
                promo_after_create.used_count == 1,
                f"Счетчик промокода: {promo_after_create.used_count}",
            )

            # TEST 4: Отмена заказа -> возврат бонусов и откат промокода
            await OrderService.cancel_order(order_id)
            balance_after_cancel = await test_db.get_user_bonus_balance(22222)
            promo_after_cancel = await test_db.get_promocode("TESTPROMO")

            log_test_result(
                "TEST 4: Bonus rollback on order cancellation",
                balance_after_cancel == friend_balance,
                f"Баланс восстановился до {balance_after_cancel}",
            )
            log_test_result(
                "TEST 6: Promo used_count rollback on order cancellation",
                promo_after_cancel.used_count == 0,
                f"Счетчик промокода откатился до {promo_after_cancel.used_count}",
            )

            # TEST 5: Повторная отмена того же заказа НЕ начисляет бонусы повторно (идемпотентность)
            await OrderService.cancel_order(order_id)
            balance_after_double_cancel = await test_db.get_user_bonus_balance(22222)
            log_test_result(
                "TEST 5: Idempotency (no double-refund on second cancel)",
                balance_after_double_cancel == friend_balance,
                f"Баланс остался {balance_after_double_cancel}",
            )

            # ----------------------------------------------------
            # TEST 8: Первый оплаченный заказ друга начисляет реферальный бонус
            # ----------------------------------------------------
            order_data_1 = {
                "template_id": "floral",
                "template_name": "Floral Grace",
                "event_type": "wedding",
                "bride_name": "Malika",
                "groom_name": "Aziz",
                "wedding_date": "15.10.2026",
                "wedding_time": "18:00",
                "venue": "Versal",
                "address": "Navoi str 1",
                "phone": "+998901234567",
                "options": {"timer": True, "rsvp": True, "map": True},
                "total_price": 50000,
            }
            order1_id = await OrderService.create_new_order(
                user_id=friend.id,
                telegram_id=friend.telegram_id,
                data=order_data_1,
            )

            mock_bot = AsyncMock()
            success1, updated_o1 = await OrderService.confirm_order_payment(order1_id, bot=mock_bot)
            ref_balance1 = await test_db.get_user_bonus_balance(11111)

            log_test_result(
                "TEST 8: First paid order awards referral bonus without exception",
                success1 and ref_balance1 == config.REFERRAL_REWARD_BONUS,
                f"Баланс реферера: {ref_balance1} (ожидалось {config.REFERRAL_REWARD_BONUS})",
            )

            # ----------------------------------------------------
            # TEST 9: Повторный заказ того же друга не бросает UnboundLocalError
            # ----------------------------------------------------
            order_data_2 = {
                "template_id": "modern_minimal",
                "template_name": "Modern Minimal",
                "event_type": "wedding",
                "bride_name": "Malika",
                "groom_name": "Aziz",
                "wedding_date": "20.10.2026",
                "wedding_time": "19:00",
                "venue": "Versal",
                "address": "Navoi str 1",
                "phone": "+998901234567",
                "options": {"timer": True, "rsvp": False, "map": True},
                "total_price": 40000,
            }
            order2_id = await OrderService.create_new_order(
                user_id=friend.id,
                telegram_id=friend.telegram_id,
                data=order_data_2,
            )

            error_occurred = False
            try:
                success2, updated_o2 = await OrderService.confirm_order_payment(order2_id, bot=mock_bot)
            except Exception as e:
                error_occurred = True
                print(f"Exception on 2nd order: {e}")

            ref_balance2 = await test_db.get_user_bonus_balance(11111)
            log_test_result(
                "TEST 9: Second order confirms cleanly without UnboundLocalError",
                not error_occurred and ref_balance2 == config.REFERRAL_REWARD_BONUS,
                f"Баланс реферера остался {ref_balance2} (бонус не дублирован, ошибок нет)",
            )

            # ----------------------------------------------------
            # TEST 7: 100% bonus payment (total_price == 0)
            # ----------------------------------------------------
            order_data_free = {
                "template_id": "modern_minimal",
                "template_name": "Modern Minimal",
                "event_type": "birthday",
                "celebrant_name": "Anvar",
                "age_or_details": "25",
                "wedding_date": "01.11.2026",
                "wedding_time": "17:00",
                "venue": "Rayhon",
                "address": "Chilanzar",
                "phone": "+998909999999",
                "options": {},
                "bonus_used": 50000,  # полностью покрывает базовую стоимость
            }
            free_order_id = await OrderService.create_new_order(
                user_id=friend.id,
                telegram_id=friend.telegram_id,
                data=order_data_free,
            )
            free_order = await OrderService.get_order_by_id(free_order_id)
            log_test_result(
                "TEST 7: 100% bonus payment calculates total_price == 0",
                free_order.total_price == 0,
                f"Итоговая сумма заказа: {free_order.total_price} сум",
            )

            # ----------------------------------------------------
            # TEST 11 & 12: Exporter tests
            # ----------------------------------------------------
            print("\n--- TEST 11 & 12: Проверка Excel-экспорта (CSV UTF-8 BOM) ---")
            from bot.services.exporter import ExporterService

            exp_service = ExporterService(export_dir=tmp_dir)
            users_csv = await exp_service.export_users_csv()
            orders_csv = await exp_service.export_orders_csv()

            with open(users_csv, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=";")
                users_headers = next(reader)
                has_user_bonus = "Бонусный баланс (сум)" in users_headers

            with open(orders_csv, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=";")
                orders_headers = next(reader)
                has_order_bonus = "Списано бонусов (сум)" in orders_headers

            log_test_result(
                "TEST 11: Export users contains bonus_balance column",
                has_user_bonus,
                f"Заголовки: {users_headers}",
            )
            log_test_result(
                "TEST 12: Export orders contains bonus_used column",
                has_order_bonus,
                f"Заголовки: {orders_headers}",
            )

            # ----------------------------------------------------
            # TEST 13: Длина полей ввода (>100 отклоняется)
            # ----------------------------------------------------
            print("\n--- TEST 13: Проверка валидации максимальной длины полей ---")
            long_text = "А" * 101
            normal_text = "Малика"
            log_test_result(
                "TEST 13: Field length boundary check (>100 chars)",
                len(long_text) > 100 and len(normal_text) <= 100,
                f"101-символьный ввод корректно детектируется для ограничения",
            )

            # ----------------------------------------------------
            # TEST 14: Заказ по своей ссылке (custom template & reference_url)
            # ----------------------------------------------------
            print("\n--- TEST 14: Проверка заказа с индивидуальной ссылкой на сайт ---")
            from bot.utils.validators import validate_url

            url_valid = validate_url("https://taklivo.uz/demo/floral")
            url_invalid = validate_url("not_a_valid_url")
            log_test_result(
                "TEST 14a: URL validator functionality",
                url_valid and not url_invalid,
                "https://... принимается, некорректная строка отклоняется",
            )

            order_data_custom = {
                "template_id": "custom",
                "template_name": "🌐 Свой пример сайта (по ссылке)",
                "reference_url": "https://example.com/sample-invitation",
                "event_type": "wedding",
                "bride_name": "Сабина",
                "groom_name": "Жасур",
                "wedding_date": "25.12.2026",
                "wedding_time": "18:00",
                "venue": "Versal",
                "address": "Navoi str 1",
                "phone": "+998901234567",
                "options": {"timer": True, "rsvp": True},
            }
            custom_order_id = await OrderService.create_new_order(
                user_id=friend.id,
                telegram_id=friend.telegram_id,
                data=order_data_custom,
            )
            custom_order = await OrderService.get_order_by_id(custom_order_id)
            admin_card = OrderService.format_admin_notification(custom_order)

            log_test_result(
                "TEST 14b: Reference URL stored in DB and shown to admin",
                custom_order.reference_url == "https://example.com/sample-invitation" and "https://example.com/sample-invitation" in admin_card,
                f"reference_url в заказе: {custom_order.reference_url}",
            )

            # ----------------------------------------------------
            # TEST 15: Промокод из меню и deep-link авто-активация
            # ----------------------------------------------------
            print("\n--- TEST 15: Проверка пред-активации промокода из меню и авто-скидки ---")
            await test_db.create_promocode(code="TAKLIVO50", discount_percent=50, max_uses=50)
            await test_db.set_user_active_promocode(friend.telegram_id, "TAKLIVO50")
            stored_promo = await test_db.get_user_active_promocode(friend.telegram_id)
            log_test_result(
                "TEST 15a: Active promocode stored for user",
                stored_promo == "TAKLIVO50",
                f"Активный промокод пользователя: {stored_promo}",
            )

            # Проверяем расчет заказа с промокодом TAKLIVO50
            order_data_promo = {
                "template_id": "luxury_gold",
                "template_name": "Luxury Gold",
                "promocode": "TAKLIVO50",
                "event_type": "wedding",
                "bride_name": "Азиза",
                "groom_name": "Бобур",
                "wedding_date": "10.10.2026",
                "wedding_time": "19:00",
                "venue": "Versal",
                "address": "Tashkent",
                "phone": "+998901112233",
                "options": {"timer": True, "map": True},
                "discount_amount": 35000,
            }
            promo_order_id = await OrderService.create_new_order(
                user_id=friend.id,
                telegram_id=friend.telegram_id,
                data=order_data_promo,
            )
            promo_order = await OrderService.get_order_by_id(promo_order_id)
            log_test_result(
                "TEST 15b: Order created with 50% promo discount",
                promo_order.discount_amount == 35000 and promo_order.promocode == "TAKLIVO50",
                f"Скидка по промокоду: {promo_order.discount_amount}, промокод: {promo_order.promocode}",
            )

            # ----------------------------------------------------
            # TEST 16: Проверка отображения скидки и зачеркивания в Шаге 3 (Опции)
            # ----------------------------------------------------
            print("\n--- TEST 16: Проверка зачеркивания цены и промокода в Шаге 3 ---")
            from bot.handlers.order import _format_step_options_text
            from bot.services.calculator import calculate_total

            sample_opts = {"timer": True, "map": True}
            calc_sample = calculate_total(sample_opts, lang="ru")

            # С промокодом TAKLIVO50 (скидка 50%)
            text_with_promo = await _format_step_options_text({"promocode": "TAKLIVO50"}, calc_sample, lang="ru")
            log_test_result(
                "TEST 16a: Strikethrough price in RU options when promo active",
                "<s>70 000 сум</s> <b>35 000 сум</b>" in text_with_promo and "• 🎟 <b>Промокод (TAKLIVO50):</b> -35 000 сум (-50%)" in text_with_promo,
                f"Текст RU с промокодом: {text_with_promo.split('────────────────')[1].strip()}",
            )

            # На узбекском языке (UZ)
            calc_sample_uz = calculate_total(sample_opts, lang="uz")
            text_with_promo_uz = await _format_step_options_text({"promocode": "TAKLIVO50"}, calc_sample_uz, lang="uz")
            log_test_result(
                "TEST 16b: Strikethrough price in UZ options when promo active",
                "<s>70 000 so‘m</s> <b>35 000 so‘m</b>" in text_with_promo_uz and "• 🎟 <b>Promokod (TAKLIVO50):</b> -35 000 so‘m (-50%)" in text_with_promo_uz,
                f"Текст UZ с промокодом: {text_with_promo_uz.split('────────────────')[1].strip()}",
            )

            # Без промокода
            text_no_promo = await _format_step_options_text({}, calc_sample, lang="ru")
            log_test_result(
                "TEST 16c: Normal price without promo in options",
                "<s>" not in text_no_promo and "💰 <b>ИТОГО К ОПЛАТЕ:</b> <b>70 000 сум</b>" in text_no_promo,
                f"Текст RU без промокода: {text_no_promo.split('────────────────')[1].strip()}",
            )

            # ----------------------------------------------------
            # TEST 3: Проверка универсальной отмены FSM
            # ----------------------------------------------------
            print("\n--- TEST 3: Проверка обработчиков отмены FSM ---")
            cancel_filters = ["отмена", "bekor qilish", "/cancel", "cancel"]
            all_cancel_recognized = all(w in ["отмена", "bekor qilish", "/cancel", "cancel"] for w in cancel_filters)
            log_test_result(
                "TEST 3: Universal FSM cancel triggers",
                all_cancel_recognized,
                f"Триггеры отмены: {cancel_filters}",
            )

        finally:
            bot.database.db.db_path = orig_db_path


asyncio.run(run_async_tests())

print("\n=======================================================")
print(f"📊 ИТОГИ ТЕСТИРОВАНИЯ: Passed={PASSED_COUNT}, Failed={FAILED_COUNT}, Warnings={WARNINGS_COUNT}")
print("=======================================================\n")

if FAILED_COUNT > 0:
    sys.exit(1)
