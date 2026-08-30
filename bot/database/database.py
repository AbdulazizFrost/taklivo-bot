"""
Асинхронный модуль работы с базой данных SQLite через aiosqlite.
Включает функции автоматического резервного копирования (Backup) для 100% сохранности данных.
"""
from datetime import datetime
import os
from pathlib import Path
import shutil
from typing import Any, Optional
import aiosqlite

from bot.database.models import User, Order, OrderPhoto, OrderMusic, OrderStatus, PaymentStatus
from config import config


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.backups_dir = Path(self.db_path).parent / "backups"
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        """Инициализирует таблицы базы данных и индексы."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Включаем внешние ключи
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging для высокой надежности

            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    language TEXT DEFAULT 'ru',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Таблица заказов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    telegram_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'NEW',
                    template_id TEXT NOT NULL,
                    template_name TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'CUSTOM',
                    bride_name TEXT NOT NULL,
                    groom_name TEXT NOT NULL,
                    wedding_date TEXT NOT NULL,
                    wedding_time TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    address TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    rsvp_enabled INTEGER DEFAULT 0,
                    map_enabled INTEGER DEFAULT 1,
                    music_enabled INTEGER DEFAULT 0,
                    gallery_enabled INTEGER DEFAULT 0,
                    dresscode_enabled INTEGER DEFAULT 0,
                    schedule_enabled INTEGER DEFAULT 0,
                    second_language_enabled INTEGER DEFAULT 0,
                    total_price INTEGER NOT NULL,
                    payment_status TEXT DEFAULT 'UNPAID',
                    payment_receipt_file_id TEXT,
                    website_url TEXT,
                    revision_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # Таблица фотографий к заказу
            await db.execute("""
                CREATE TABLE IF NOT EXISTS order_photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    file_unique_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                );
            """)

            # Таблица музыки к заказу
            await db.execute("""
                CREATE TABLE IF NOT EXISTS order_music (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    file_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                );
            """)

            # Создание индексов
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_telegram_id ON orders(telegram_id);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);")

            await db.commit()

    def create_backup_copy(self) -> str:
        """
        Создает мгновенный резервный снимок файла базы данных.
        Возвращает путь к созданному файлу бэкапа.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"taklivo_backup_{timestamp}.db"
        backup_path = self.backups_dir / backup_filename

        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, backup_path)
            return str(backup_path)
        return self.db_path

    # --- Пользователи ---

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        language: str = "ru",
    ) -> User:
        """Получает или создает пользователя в базе."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()

            if row:
                if (username and row["username"] != username) or (first_name and row["first_name"] != first_name):
                    await db.execute(
                        "UPDATE users SET username = ?, first_name = ? WHERE telegram_id = ?",
                        (username, first_name, telegram_id),
                    )
                    await db.commit()
                return User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=username or row["username"],
                    first_name=first_name or row["first_name"],
                    language=row["language"] or "ru",
                    created_at=str(row["created_at"]),
                )

            cursor = await db.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, language)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, username, first_name, language),
            )
            user_id = cursor.lastrowid
            await db.commit()

            return User(
                id=user_id,
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                language=language,
                created_at=datetime.utcnow().isoformat(),
            )

    async def get_user_language(self, telegram_id: int) -> str:
        """Получает язык интерфейса пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT language FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            if row and row["language"]:
                return row["language"]
            return "ru"

    async def set_user_language(self, telegram_id: int, language: str) -> None:
        """Сохраняет выбранный язык пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET language = ? WHERE telegram_id = ?",
                (language, telegram_id),
            )
            await db.commit()

    # --- Заказы ---

    def _row_to_order(self, row: aiosqlite.Row) -> Order:
        return Order(
            id=row["id"],
            user_id=row["user_id"],
            telegram_id=row["telegram_id"],
            status=row["status"],
            template_id=row["template_id"],
            template_name=row["template_name"],
            plan=row["plan"],
            bride_name=row["bride_name"],
            groom_name=row["groom_name"],
            wedding_date=row["wedding_date"],
            wedding_time=row["wedding_time"],
            venue=row["venue"],
            address=row["address"],
            phone=row["phone"],
            rsvp_enabled=bool(row["rsvp_enabled"]),
            map_enabled=bool(row["map_enabled"]),
            music_enabled=bool(row["music_enabled"]),
            gallery_enabled=bool(row["gallery_enabled"]),
            dresscode_enabled=bool(row["dresscode_enabled"]),
            schedule_enabled=bool(row["schedule_enabled"]),
            second_language_enabled=bool(row["second_language_enabled"]),
            total_price=row["total_price"],
            payment_status=row["payment_status"],
            payment_receipt_file_id=row["payment_receipt_file_id"],
            website_url=row["website_url"],
            revision_text=row["revision_text"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    async def create_order(
        self,
        user_id: int,
        telegram_id: int,
        template_id: str,
        template_name: str,
        plan: str,
        bride_name: str,
        groom_name: str,
        wedding_date: str,
        wedding_time: str,
        venue: str,
        address: str,
        phone: str,
        rsvp_enabled: bool,
        map_enabled: bool,
        music_enabled: bool,
        gallery_enabled: bool,
        dresscode_enabled: bool,
        schedule_enabled: bool,
        second_language_enabled: bool,
        total_price: int,
        status: str = OrderStatus.WAITING_PAYMENT.value,
    ) -> int:
        """Создает новый заказ в базе данных."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO orders (
                    user_id, telegram_id, status, template_id, template_name, plan,
                    bride_name, groom_name, wedding_date, wedding_time,
                    venue, address, phone, rsvp_enabled, map_enabled,
                    music_enabled, gallery_enabled, dresscode_enabled,
                    schedule_enabled, second_language_enabled, total_price, payment_status
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?
                )
                """,
                (
                    user_id,
                    telegram_id,
                    status,
                    template_id,
                    template_name,
                    plan,
                    bride_name,
                    groom_name,
                    wedding_date,
                    wedding_time,
                    venue,
                    address,
                    phone,
                    1 if rsvp_enabled else 0,
                    1 if map_enabled else 0,
                    1 if music_enabled else 0,
                    1 if gallery_enabled else 0,
                    1 if dresscode_enabled else 0,
                    1 if schedule_enabled else 0,
                    1 if second_language_enabled else 0,
                    total_price,
                    PaymentStatus.UNPAID.value,
                ),
            )
            order_id = cursor.lastrowid
            await db.commit()
            return order_id

    async def get_order(self, order_id: int) -> Optional[Order]:
        """Получает заказ по ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                return self._row_to_order(row)
            return None

    async def get_user_orders(self, telegram_id: int) -> list[Order]:
        """Возвращает список заказов конкретного пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM orders WHERE telegram_id = ? ORDER BY id DESC",
                (telegram_id,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_order(row) for row in rows]

    async def get_orders_by_status(self, status: str, limit: int = 50) -> list[Order]:
        """Возвращает заказы с указанным статусом."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            )
            rows = await cursor.fetchall()
            return [self._row_to_order(row) for row in rows]

    async def get_recent_orders(self, limit: int = 30) -> list[Order]:
        """Возвращает последние заказы."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_order(row) for row in rows]

    async def update_order_status(
        self,
        order_id: int,
        status: str,
        payment_status: Optional[str] = None,
    ) -> None:
        """Обновляет статус заказа и время обновления."""
        async with aiosqlite.connect(self.db_path) as db:
            if payment_status:
                await db.execute(
                    """
                    UPDATE orders
                    SET status = ?, payment_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, payment_status, order_id),
                )
            else:
                await db.execute(
                    """
                    UPDATE orders
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, order_id),
                )
            await db.commit()

    async def set_order_receipt(self, order_id: int, file_id: str) -> None:
        """Сохраняет чек об оплате и переводит в статус PAYMENT_REVIEW / REVIEW."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE orders
                SET payment_receipt_file_id = ?, status = ?, payment_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (file_id, OrderStatus.PAYMENT_REVIEW.value, PaymentStatus.REVIEW.value, order_id),
            )
            await db.commit()

    async def set_order_website_url(self, order_id: int, url: str) -> None:
        """Сохраняет URL готового сайта и переводит статус в PREVIEW."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE orders
                SET website_url = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (url, OrderStatus.PREVIEW.value, order_id),
            )
            await db.commit()

    async def set_order_revision(self, order_id: int, revision_text: str) -> None:
        """Сохраняет текст правок и переводит статус в REVISION."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE orders
                SET revision_text = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (revision_text, OrderStatus.REVISION.value, order_id),
            )
            await db.commit()

    # --- Фотографии ---

    async def add_order_photo(self, order_id: int, file_id: str, file_unique_id: Optional[str] = None) -> None:
        """Добавляет фото к заказу."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO order_photos (order_id, file_id, file_unique_id) VALUES (?, ?, ?)",
                (order_id, file_id, file_unique_id),
            )
            await db.commit()

    async def get_order_photos(self, order_id: int) -> list[OrderPhoto]:
        """Возвращает фото к заказу."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM order_photos WHERE order_id = ?",
                (order_id,),
            )
            rows = await cursor.fetchall()
            return [
                OrderPhoto(
                    id=row["id"],
                    order_id=row["order_id"],
                    file_id=row["file_id"],
                    file_unique_id=row["file_unique_id"],
                    created_at=str(row["created_at"]),
                )
                for row in rows
            ]

    # --- Музыка ---

    async def set_order_music(self, order_id: int, file_id: str, file_name: Optional[str] = None) -> None:
        """Сохраняет аудиофайл к заказу."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM order_music WHERE order_id = ?", (order_id,))
            await db.execute(
                "INSERT INTO order_music (order_id, file_id, file_name) VALUES (?, ?, ?)",
                (order_id, file_id, file_name),
            )
            await db.commit()

    async def get_order_music(self, order_id: int) -> Optional[OrderMusic]:
        """Возвращает аудиофайл к заказу."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM order_music WHERE order_id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                return OrderMusic(
                    id=row["id"],
                    order_id=row["order_id"],
                    file_id=row["file_id"],
                    file_name=row["file_name"],
                    created_at=str(row["created_at"]),
                )
            return None

    # --- Статистика ---

    async def get_statistics(self) -> dict[str, Any]:
        """Возвращает сводные данные по заказам и выручке."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Всего заказов
            cursor = await db.execute("SELECT COUNT(*) as total FROM orders")
            total_orders = (await cursor.fetchone())["total"]

            # Разбивка по статусам
            cursor = await db.execute("""
                SELECT status, COUNT(*) as count 
                FROM orders 
                GROUP BY status
            """)
            status_counts_raw = await cursor.fetchall()
            status_counts = {row["status"]: row["count"] for row in status_counts_raw}

            # Общая выручка (по оплаченным заказам)
            cursor = await db.execute("""
                SELECT SUM(total_price) as revenue 
                FROM orders 
                WHERE status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED')
                   OR payment_status = 'PAID'
            """)
            total_revenue_row = await cursor.fetchone()
            total_revenue = total_revenue_row["revenue"] or 0

            # Выручка и заказы за текущий месяц
            current_month = datetime.utcnow().strftime("%Y-%m")
            cursor = await db.execute(
                """
                SELECT COUNT(*) as month_orders, SUM(total_price) as month_revenue
                FROM orders
                WHERE strftime('%Y-%m', created_at) = ?
                  AND (status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED') OR payment_status = 'PAID')
                """,
                (current_month,),
            )
            month_stats = await cursor.fetchone()
            month_orders = month_stats["month_orders"] or 0
            month_revenue = month_stats["month_revenue"] or 0

            return {
                "total_orders": total_orders,
                "status_counts": status_counts,
                "total_revenue": total_revenue,
                "month_orders": month_orders,
                "month_revenue": month_revenue,
            }


db = Database()
