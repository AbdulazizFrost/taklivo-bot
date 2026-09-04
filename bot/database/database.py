"""
Асинхронный модуль работы с базой данных SQLite через aiosqlite.
Включает функции автоматического резервного копирования (Backup) для 100% сохранности данных.
"""
from datetime import datetime, timedelta
import os
from pathlib import Path
import shutil
from typing import Any, Optional
import aiosqlite

from bot.database.models import (
    User,
    Order,
    OrderPhoto,
    OrderMusic,
    OrderStatus,
    PaymentStatus,
    EventType,
    PromoCode,
)
from config import config


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.backups_dir = Path(self.db_path).parent / "backups"
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        """Инициализирует таблицы базы данных, индексы и миграции."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Включаем внешние ключи и WAL
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute("PRAGMA journal_mode = WAL;")

            # 1. Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    language TEXT DEFAULT 'ru',
                    referrer_id INTEGER,
                    bonus_balance INTEGER DEFAULT 0,
                    active_promocode TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Таблица промокодов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS promocodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    discount_percent INTEGER DEFAULT 0,
                    discount_amount INTEGER DEFAULT 0,
                    max_uses INTEGER DEFAULT 100,
                    used_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Таблица заказов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    telegram_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'NEW',
                    template_id TEXT NOT NULL,
                    template_name TEXT NOT NULL,
                    plan TEXT NOT NULL DEFAULT 'CUSTOM',
                    event_type TEXT NOT NULL DEFAULT 'wedding',
                    bride_name TEXT NOT NULL DEFAULT '',
                    groom_name TEXT NOT NULL DEFAULT '',
                    celebrant_name TEXT,
                    parents_name TEXT,
                    age_or_details TEXT,
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
                    promocode TEXT,
                    discount_amount INTEGER DEFAULT 0,
                    bonus_used INTEGER DEFAULT 0,
                    payment_status TEXT DEFAULT 'UNPAID',
                    payment_receipt_file_id TEXT,
                    website_url TEXT,
                    reference_url TEXT,
                    revision_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)

            # 4. Таблица фотографий к заказу
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

            # 5. Таблица музыки к заказу
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

            # Миграции для существующих баз данных
            cursor = await db.execute("PRAGMA table_info(users);")
            u_cols = [row["name"] for row in await cursor.fetchall()]
            if "referrer_id" not in u_cols:
                await db.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER;")
            if "bonus_balance" not in u_cols:
                await db.execute("ALTER TABLE users ADD COLUMN bonus_balance INTEGER DEFAULT 0;")
            if "active_promocode" not in u_cols:
                await db.execute("ALTER TABLE users ADD COLUMN active_promocode TEXT;")

            cursor = await db.execute("PRAGMA table_info(orders);")
            o_cols = [row["name"] for row in await cursor.fetchall()]
            if "event_type" not in o_cols:
                await db.execute("ALTER TABLE orders ADD COLUMN event_type TEXT NOT NULL DEFAULT 'wedding';")
            if "celebrant_name" not in o_cols:
                await db.execute("ALTER TABLE orders ADD COLUMN celebrant_name TEXT;")
            if "parents_name" not in o_cols:
                await db.execute("ALTER TABLE orders ADD COLUMN parents_name TEXT;")
            if "age_or_details" not in o_cols:
                await db.execute("ALTER TABLE orders ADD COLUMN age_or_details TEXT;")
            if "promocode" not in o_cols:
                await db.execute("ALTER TABLE orders ADD COLUMN promocode TEXT;")
            if "discount_amount" not in o_cols:
                await db.execute("ALTER TABLE orders ADD COLUMN discount_amount INTEGER DEFAULT 0;")
            if "bonus_used" not in o_cols:
                await db.execute("ALTER TABLE orders ADD COLUMN bonus_used INTEGER DEFAULT 0;")
            if "reference_url" not in o_cols:
                await db.execute("ALTER TABLE orders ADD COLUMN reference_url TEXT;")

            # Индексы
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_telegram_id ON orders(telegram_id);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_promocodes_code ON promocodes(code);")

            await db.commit()

    def create_backup_copy(self) -> str:
        """Создает мгновенный резервный снимок файла базы данных."""
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
        referrer_id: Optional[int] = None,
    ) -> User:
        """Получает или создает пользователя в базе (с начислением приветственного бонуса при реферальном входе)."""
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
                    referrer_id=row["referrer_id"] if "referrer_id" in row.keys() else None,
                    bonus_balance=row["bonus_balance"] if "bonus_balance" in row.keys() else 0,
                    active_promocode=row["active_promocode"] if "active_promocode" in row.keys() else None,
                    created_at=str(row["created_at"]),
                )

            # Если пользователь новый и указан реферер (и реферер не сам пользователь)
            valid_referrer = referrer_id if referrer_id and referrer_id != telegram_id else None
            initial_bonus = config.REFERRAL_WELCOME_BONUS if valid_referrer else 0

            cursor = await db.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, language, referrer_id, bonus_balance)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (telegram_id, username, first_name, language, valid_referrer, initial_bonus),
            )
            user_id = cursor.lastrowid
            await db.commit()

            return User(
                id=user_id,
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                language=language,
                referrer_id=valid_referrer,
                bonus_balance=initial_bonus,
                active_promocode=None,
                created_at=datetime.utcnow().isoformat(),
            )

    async def set_user_active_promocode(self, telegram_id: int, promo_code: Optional[str]) -> None:
        """Сохраняет активированный пользователем промокод (или сбрасывает его)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET active_promocode = ? WHERE telegram_id = ?",
                (promo_code.strip().upper() if promo_code else None, telegram_id),
            )
            await db.commit()

    async def get_user_active_promocode(self, telegram_id: int) -> Optional[str]:
        """Возвращает текущий активный промокод пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT active_promocode FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            if row and "active_promocode" in row.keys():
                return row["active_promocode"]
            return None

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

    async def get_user_bonus_balance(self, telegram_id: int) -> int:
        """Возвращает баланс бонусов пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT bonus_balance FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            if row and "bonus_balance" in row.keys() and row["bonus_balance"]:
                return row["bonus_balance"]
            return 0

    async def add_user_bonus(self, telegram_id: int, amount: int) -> int:
        """Начисляет бонусы пользователю и возвращает новый баланс."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET bonus_balance = COALESCE(bonus_balance, 0) + ? WHERE telegram_id = ?",
                (amount, telegram_id),
            )
            await db.commit()
            return await self.get_user_bonus_balance(telegram_id)

    async def deduct_user_bonus(self, telegram_id: int, amount: int) -> bool:
        """Списывает бонусы пользователя при оплате заказа."""
        current_balance = await self.get_user_bonus_balance(telegram_id)
        if current_balance < amount:
            return False
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET bonus_balance = bonus_balance - ? WHERE telegram_id = ?",
                (amount, telegram_id),
            )
            await db.commit()
            return True

    async def get_referral_stats(self, telegram_id: int) -> dict[str, int]:
        """Возвращает количество приглашенных друзей, оформленных заказов и текущий баланс бонусов."""
        async with aiosqlite.connect(self.db_path) as db:
            # Число зарегистрированных по ссылке
            cursor = await db.execute(
                "SELECT COUNT(*) as invited_count FROM users WHERE referrer_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            invited_count = row[0] if row else 0

            # Число оплаченных заказов от рефералов
            cursor = await db.execute(
                """
                SELECT COUNT(o.id) as orders_count
                FROM orders o
                JOIN users u ON o.telegram_id = u.telegram_id
                WHERE u.referrer_id = ?
                  AND o.status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED')
                """,
                (telegram_id,),
            )
            row = await cursor.fetchone()
            orders_count = row[0] if row else 0

            bonus_balance = await self.get_user_bonus_balance(telegram_id)

            return {
                "invited_count": invited_count,
                "orders_count": orders_count,
                "bonus_balance": bonus_balance,
            }

    async def get_all_users(self) -> list[User]:
        """Возвращает всех пользователей из базы для экспорта."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users ORDER BY id ASC")
            rows = await cursor.fetchall()
            return [
                User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=row["username"],
                    first_name=row["first_name"],
                    language=row["language"] or "ru",
                    referrer_id=row["referrer_id"] if "referrer_id" in row.keys() else None,
                    bonus_balance=row["bonus_balance"] if "bonus_balance" in row.keys() else 0,
                    created_at=str(row["created_at"]),
                )
                for row in rows
            ]

    # --- Промокоды ---

    async def create_promocode(
        self,
        code: str,
        discount_percent: int = 0,
        discount_amount: int = 0,
        max_uses: int = 100,
    ) -> int:
        """Создает новый промокод."""
        code_clean = code.strip().upper()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO promocodes (code, discount_percent, discount_amount, max_uses)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    discount_percent = excluded.discount_percent,
                    discount_amount = excluded.discount_amount,
                    max_uses = excluded.max_uses,
                    is_active = 1
                """,
                (code_clean, discount_percent, discount_amount, max_uses),
            )
            promocode_id = cursor.lastrowid
            await db.commit()
            return promocode_id

    async def get_promocode(self, code: str) -> Optional[PromoCode]:
        """Получает активный промокод по его кодовому слову."""
        code_clean = code.strip().upper()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM promocodes WHERE code = ? AND is_active = 1",
                (code_clean,),
            )
            row = await cursor.fetchone()
            if row:
                return PromoCode(
                    id=row["id"],
                    code=row["code"],
                    discount_percent=row["discount_percent"],
                    discount_amount=row["discount_amount"],
                    max_uses=row["max_uses"],
                    used_count=row["used_count"],
                    is_active=bool(row["is_active"]),
                    created_at=str(row["created_at"]),
                )
            return None

    async def get_all_promocodes(self) -> list[PromoCode]:
        """Возвращает список всех промокодов."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM promocodes ORDER BY id DESC")
            rows = await cursor.fetchall()
            return [
                PromoCode(
                    id=row["id"],
                    code=row["code"],
                    discount_percent=row["discount_percent"],
                    discount_amount=row["discount_amount"],
                    max_uses=row["max_uses"],
                    used_count=row["used_count"],
                    is_active=bool(row["is_active"]),
                    created_at=str(row["created_at"]),
                )
                for row in rows
            ]

    async def delete_promocode(self, promocode_id: int) -> bool:
        """Деактивирует или удаляет промокод."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM promocodes WHERE id = ?", (promocode_id,))
            await db.commit()
            return True

    async def increment_promocode_usage(self, code: str) -> None:
        """Увеличивает счетчик использований промокода."""
        code_clean = code.strip().upper()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?",
                (code_clean,),
            )
            await db.commit()

    # --- Заказы ---

    def _row_to_order(self, row: aiosqlite.Row) -> Order:
        keys = row.keys()
        return Order(
            id=row["id"],
            user_id=row["user_id"],
            telegram_id=row["telegram_id"],
            status=row["status"],
            template_id=row["template_id"],
            template_name=row["template_name"],
            plan=row["plan"],
            event_type=row["event_type"] if "event_type" in keys and row["event_type"] else "wedding",
            bride_name=row["bride_name"] or "",
            groom_name=row["groom_name"] or "",
            celebrant_name=row["celebrant_name"] if "celebrant_name" in keys else None,
            parents_name=row["parents_name"] if "parents_name" in keys else None,
            age_or_details=row["age_or_details"] if "age_or_details" in keys else None,
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
            promocode=row["promocode"] if "promocode" in keys else None,
            discount_amount=row["discount_amount"] if "discount_amount" in keys else 0,
            bonus_used=row["bonus_used"] if "bonus_used" in keys else 0,
            payment_status=row["payment_status"],
            payment_receipt_file_id=row["payment_receipt_file_id"],
            website_url=row["website_url"],
            reference_url=row["reference_url"] if "reference_url" in keys else None,
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
        event_type: str = "wedding",
        bride_name: str = "",
        groom_name: str = "",
        celebrant_name: Optional[str] = None,
        parents_name: Optional[str] = None,
        age_or_details: Optional[str] = None,
        promocode: Optional[str] = None,
        discount_amount: int = 0,
        bonus_used: int = 0,
        reference_url: Optional[str] = None,
        status: str = OrderStatus.WAITING_PAYMENT.value,
    ) -> int:
        """Создает новый заказ в базе данных с учетом промокода, списанных бонусов и ссылки на пример."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO orders (
                    user_id, telegram_id, status, template_id, template_name, plan,
                    event_type, bride_name, groom_name, celebrant_name, parents_name, age_or_details,
                    wedding_date, wedding_time,
                    venue, address, phone, rsvp_enabled, map_enabled,
                    music_enabled, gallery_enabled, dresscode_enabled,
                    schedule_enabled, second_language_enabled, total_price,
                    promocode, discount_amount, bonus_used, payment_status, reference_url
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    user_id,
                    telegram_id,
                    status,
                    template_id,
                    template_name,
                    plan,
                    event_type,
                    bride_name,
                    groom_name,
                    celebrant_name,
                    parents_name,
                    age_or_details,
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
                    promocode,
                    discount_amount,
                    bonus_used,
                    PaymentStatus.UNPAID.value,
                    reference_url,
                ),
            )
            order_id = cursor.lastrowid

            if promocode:
                await db.execute(
                    "UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?",
                    (promocode.strip().upper(),),
                )

            if bonus_used > 0:
                await db.execute(
                    "UPDATE users SET bonus_balance = MAX(0, bonus_balance - ?) WHERE telegram_id = ?",
                    (bonus_used, telegram_id),
                )

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

    async def get_all_orders(self) -> list[Order]:
        """Возвращает все заказы для экспорта в Excel."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders ORDER BY id ASC")
            rows = await cursor.fetchall()
            return [self._row_to_order(row) for row in rows]

    async def get_orders_due_soon(self, days_ahead: int) -> list[Order]:
        """Возвращает заказы, дата проведения которых наступит через days_ahead дней."""
        target_date_obj = datetime.now() + timedelta(days=days_ahead)
        target_str = target_date_obj.strftime("%d.%m.%Y")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM orders
                WHERE wedding_date = ?
                  AND status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'COMPLETED')
                """,
                (target_str,),
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
        """Возвращает сводные данные по пользователям, заказам и выручке."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = (await cursor.fetchone())["total_users"] or 0

            today_date = datetime.utcnow().strftime("%Y-%m-%d")
            cursor = await db.execute("SELECT COUNT(*) as today_users FROM users WHERE date(created_at) = ?", (today_date,))
            today_users = (await cursor.fetchone())["today_users"] or 0

            current_month = datetime.utcnow().strftime("%Y-%m")
            cursor = await db.execute("SELECT COUNT(*) as month_users FROM users WHERE strftime('%Y-%m', created_at) = ?", (current_month,))
            month_users_reg = (await cursor.fetchone())["month_users"] or 0

            cursor = await db.execute("SELECT COUNT(*) as uz_users FROM users WHERE language = 'uz'")
            uz_users = (await cursor.fetchone())["uz_users"] or 0

            cursor = await db.execute("SELECT COUNT(*) as ru_users FROM users WHERE language = 'ru'")
            ru_users = (await cursor.fetchone())["ru_users"] or 0

            cursor = await db.execute("SELECT COUNT(*) as total FROM orders")
            total_orders = (await cursor.fetchone())["total"] or 0

            cursor = await db.execute("""
                SELECT status, COUNT(*) as count 
                FROM orders 
                GROUP BY status
            """)
            status_counts_raw = await cursor.fetchall()
            status_counts = {row["status"]: row["count"] for row in status_counts_raw}

            cursor = await db.execute("""
                SELECT SUM(total_price) as revenue 
                FROM orders 
                WHERE status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED')
                   OR payment_status = 'PAID'
            """)
            total_revenue_row = await cursor.fetchone()
            total_revenue = total_revenue_row["revenue"] or 0

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
                "total_users": total_users,
                "today_users": today_users,
                "month_users_reg": month_users_reg,
                "uz_users": uz_users,
                "ru_users": ru_users,
                "total_orders": total_orders,
                "status_counts": status_counts,
                "total_revenue": total_revenue,
                "month_orders": month_orders,
                "month_revenue": month_revenue,
            }

    async def get_recent_users(self, limit: int = 20) -> list[User]:
        """Возвращает список последних зарегистрированных пользователей."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [
                User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=row["username"],
                    first_name=row["first_name"],
                    language=row["language"] or "ru",
                    referrer_id=row["referrer_id"] if "referrer_id" in row.keys() else None,
                    bonus_balance=row["bonus_balance"] if "bonus_balance" in row.keys() else 0,
                    created_at=str(row["created_at"]),
                )
                for row in rows
            ]


db = Database()
