"""
Сервис экспорта данных пользователей и заказов в формат Excel (CSV с UTF-8 BOM).
Совместим со всеми версиями Microsoft Excel, Google Таблицами и Apple Numbers.
"""
import csv
from datetime import datetime
import os
from pathlib import Path
from bot.database import db
from config import config


class ExporterService:
    def __init__(self, export_dir: str = "data/backups"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def export_users_csv(self) -> str:
        """Экспортирует всех пользователей в Excel CSV."""
        users = await db.get_all_users()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"users_taklivo_{timestamp}.csv"
        filepath = self.export_dir / filename

        with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            # Заголовки таблицы
            writer.writerow([
                "ID в базе",
                "Telegram ID",
                "Имя (First Name)",
                "Username (@)",
                "Язык интерфейса",
                "Бонусный баланс (сум)",
                "Приглашен кем (Referrer ID)",
                "Дата первого входа (UTC)",
            ])

            for u in users:
                writer.writerow([
                    u.id,
                    u.telegram_id,
                    u.first_name or "",
                    f"@{u.username}" if u.username else "",
                    u.language.upper(),
                    getattr(u, "bonus_balance", 0) or 0,
                    u.referrer_id or "—",
                    u.created_at,
                ])

        return str(filepath)

    async def export_orders_csv(self) -> str:
        """Экспортирует все заказы сервиса в Excel CSV."""
        orders = await db.get_all_orders()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"orders_taklivo_{timestamp}.csv"
        filepath = self.export_dir / filename

        with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            # Заголовки таблицы
            writer.writerow([
                "Номер заказа (#)",
                "Тип торжества",
                "Главные персоны",
                "Дата торжества",
                "Время",
                "Заведение / Место",
                "Адрес",
                "Телефон клиента",
                "Дизайн (Шаблон)",
                "Сумма к оплате (сум)",
                "Списано бонусов (сум)",
                "Промокод",
                "Скидка (сум)",
                "Статус заказа",
                "Статус оплаты",
                "Ссылка на сайт",
                "Telegram ID клиента",
                "Дата создания заказа",
            ])

            for o in orders:
                if o.event_type == "birthday":
                    event_title = "День рождения"
                    persons = f"{o.celebrant_name or ''} ({o.age_or_details or ''})".strip()
                elif o.event_type == "sunnat":
                    event_title = "Суннат туй"
                    persons = f"{o.celebrant_name or ''} (Родители: {o.parents_name or ''})".strip()
                else:
                    event_title = "Свадьба"
                    persons = f"{o.bride_name} & {o.groom_name}"

                writer.writerow([
                    o.id,
                    event_title,
                    persons,
                    o.wedding_date,
                    o.wedding_time,
                    o.venue,
                    o.address,
                    o.phone,
                    o.template_name,
                    o.total_price,
                    getattr(o, "bonus_used", 0) or 0,
                    o.promocode or "—",
                    o.discount_amount,
                    o.status,
                    o.payment_status,
                    o.website_url or "—",
                    o.telegram_id,
                    o.created_at,
                ])

        return str(filepath)


exporter = ExporterService()
