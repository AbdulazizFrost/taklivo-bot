"""
Модуль работы с базой данных для Telegram-бота TAKLIVO.
Поддерживает два режима работы:
1. Облачный PostgreSQL (Supabase / Neon) через asyncpg при наличии DATABASE_URL.
2. Локальный SQLite через aiosqlite при отсутствии DATABASE_URL (для тестов и автономной работы).
"""
from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Optional
import aiosqlite

try:
    import asyncpg
except ImportError:
    asyncpg = None

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

logger = logging.getLogger(__name__)


class SqliteDatabase:
    """Реализация работы с базой данных через SQLite (aiosqlite)."""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.backups_dir = Path(self.db_path).parent / "backups"
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self._language_cache: dict[int, str] = {}
        self._active_promo_cache: dict[int, Optional[str]] = {}

    async def init(self) -> None:
        """Инициализирует таблицы базы данных, индексы и миграции."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

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

            # Автоматическая гарантия системного промокода TAKLIVO50
            cursor = await db.execute("SELECT id FROM promocodes WHERE code = 'TAKLIVO50'")
            if not await cursor.fetchone():
                await db.execute(
                    "INSERT INTO promocodes (code, discount_percent, discount_amount, max_uses, used_count, is_active) VALUES ('TAKLIVO50', 50, 0, 100, 0, 1)"
                )

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
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()

            if row:
                if (username and row["username"] != username) or (first_name and row["first_name"] != first_name):
                    await db.execute(
                        "UPDATE users SET username = ?, first_name = ? WHERE telegram_id = ?",
                        (username, first_name, telegram_id),
                    )
                    await db.commit()
                lang = row["language"] or "ru"
                self._language_cache[telegram_id] = lang
                self._active_promo_cache[telegram_id] = row["active_promocode"] if "active_promocode" in row.keys() else None
                return User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=username or row["username"],
                    first_name=first_name or row["first_name"],
                    language=lang,
                    referrer_id=row["referrer_id"] if "referrer_id" in row.keys() else None,
                    bonus_balance=row["bonus_balance"] if "bonus_balance" in row.keys() else 0,
                    active_promocode=row["active_promocode"] if "active_promocode" in row.keys() else None,
                    created_at=str(row["created_at"]),
                )

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

            self._language_cache[telegram_id] = language
            self._active_promo_cache[telegram_id] = None

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

    async def get_user(self, telegram_id: int) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            if row:
                return User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=row["username"],
                    first_name=row["first_name"],
                    language=row["language"] or "ru",
                    referrer_id=row["referrer_id"] if "referrer_id" in row.keys() else None,
                    bonus_balance=row["bonus_balance"] if "bonus_balance" in row.keys() else 0,
                    active_promocode=row["active_promocode"] if "active_promocode" in row.keys() else None,
                    created_at=str(row["created_at"]),
                )
            return None

    async def get_user_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def set_user_active_promocode(self, telegram_id: int, promo_code: Optional[str]) -> None:
        norm_code = promo_code.strip().upper() if promo_code else None
        self._active_promo_cache[telegram_id] = norm_code
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET active_promocode = ? WHERE telegram_id = ?",
                (norm_code, telegram_id),
            )
            await db.commit()

    async def get_user_active_promocode(self, telegram_id: int) -> Optional[str]:
        if telegram_id in self._active_promo_cache:
            return self._active_promo_cache[telegram_id]
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT active_promocode FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            promo = row["active_promocode"] if row and "active_promocode" in row.keys() else None
            self._active_promo_cache[telegram_id] = promo
            return promo

    async def get_user_language(self, telegram_id: int) -> str:
        if telegram_id in self._language_cache:
            return self._language_cache[telegram_id]
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT language FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            lang = row["language"] if row and row["language"] else "ru"
            self._language_cache[telegram_id] = lang
            return lang

    async def set_user_language(self, telegram_id: int, language: str) -> None:
        self._language_cache[telegram_id] = language
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, telegram_id))
            await db.commit()

    async def get_user_bonus_balance(self, telegram_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT bonus_balance FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            if row and "bonus_balance" in row.keys() and row["bonus_balance"]:
                return row["bonus_balance"]
            return 0

    async def add_user_bonus(self, telegram_id: int, amount: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET bonus_balance = COALESCE(bonus_balance, 0) + ? WHERE telegram_id = ?",
                (amount, telegram_id),
            )
            await db.commit()
            return await self.get_user_bonus_balance(telegram_id)

    async def deduct_user_bonus(self, telegram_id: int, amount: int) -> bool:
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
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            invited_count = row[0] if row else 0

            cursor = await db.execute(
                """
                SELECT COUNT(o.id)
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

    async def get_user_referrer_id(self, telegram_id: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT referrer_id FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None

    async def get_user_paid_orders_count(self, telegram_id: int, exclude_order_id: Optional[int] = None) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            if exclude_order_id:
                cursor = await db.execute(
                    """
                    SELECT COUNT(*) FROM orders 
                    WHERE telegram_id = ? 
                      AND status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED') 
                      AND id != ?
                    """,
                    (telegram_id, exclude_order_id),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT COUNT(*) FROM orders 
                    WHERE telegram_id = ? 
                      AND status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED')
                    """,
                    (telegram_id,),
                )
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_all_users(self) -> list[User]:
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

    async def get_recent_users(self, limit: int = 20) -> list[User]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users ORDER BY id DESC LIMIT ?", (limit,))
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
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM promocodes WHERE id = ?", (promocode_id,))
            await db.commit()
            return True

    async def increment_promocode_usage(self, code: str) -> None:
        code_clean = code.strip().upper()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE promocodes SET used_count = used_count + 1 WHERE code = ?",
                (code_clean,),
            )
            await db.commit()

    async def rollback_promocode_usage(self, code: str) -> None:
        code_clean = code.strip().upper()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE promocodes SET used_count = MAX(0, used_count - 1) WHERE code = ?",
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
                    user_id, telegram_id, status, template_id, template_name, plan,
                    event_type, bride_name, groom_name, celebrant_name, parents_name, age_or_details,
                    wedding_date, wedding_time,
                    venue, address, phone,
                    1 if rsvp_enabled else 0, 1 if map_enabled else 0,
                    1 if music_enabled else 0, 1 if gallery_enabled else 0,
                    1 if dresscode_enabled else 0, 1 if schedule_enabled else 0,
                    1 if second_language_enabled else 0, total_price,
                    promocode, discount_amount, bonus_used,
                    PaymentStatus.UNPAID.value, reference_url,
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
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = await cursor.fetchone()
            if row:
                return self._row_to_order(row)
            return None

    async def get_user_orders(self, telegram_id: int) -> list[Order]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders WHERE telegram_id = ? ORDER BY id DESC", (telegram_id,))
            rows = await cursor.fetchall()
            return [self._row_to_order(row) for row in rows]

    async def get_orders_by_status(self, status: str, limit: int = 50) -> list[Order]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders WHERE status = ? ORDER BY id DESC LIMIT ?", (status, limit))
            rows = await cursor.fetchall()
            return [self._row_to_order(row) for row in rows]

    async def get_recent_orders(self, limit: int = 30) -> list[Order]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [self._row_to_order(row) for row in rows]

    async def get_all_orders(self) -> list[Order]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders ORDER BY id ASC")
            rows = await cursor.fetchall()
            return [self._row_to_order(row) for row in rows]

    async def get_orders_due_soon(self, days_ahead: int) -> list[Order]:
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

    async def update_order_status(self, order_id: int, status: str, payment_status: Optional[str] = None) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            if payment_status:
                await db.execute(
                    "UPDATE orders SET status = ?, payment_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, payment_status, order_id),
                )
            else:
                await db.execute(
                    "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, order_id),
                )
            await db.commit()

    async def set_order_receipt(self, order_id: int, file_id: str) -> None:
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
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE orders SET website_url = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (url, OrderStatus.PREVIEW.value, order_id),
            )
            await db.commit()

    async def set_order_revision(self, order_id: int, revision_text: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE orders SET revision_text = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (revision_text, OrderStatus.REVISION.value, order_id),
            )
            await db.commit()

    async def add_order_photo(self, order_id: int, file_id: str, file_unique_id: Optional[str] = None) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO order_photos (order_id, file_id, file_unique_id) VALUES (?, ?, ?)",
                (order_id, file_id, file_unique_id),
            )
            await db.commit()

    async def get_order_photos(self, order_id: int) -> list[OrderPhoto]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM order_photos WHERE order_id = ?", (order_id,))
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

    async def set_order_music(self, order_id: int, file_id: str, file_name: Optional[str] = None) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM order_music WHERE order_id = ?", (order_id,))
            await db.execute(
                "INSERT INTO order_music (order_id, file_id, file_name) VALUES (?, ?, ?)",
                (order_id, file_id, file_name),
            )
            await db.commit()

    async def get_order_music(self, order_id: int) -> Optional[OrderMusic]:
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

    async def get_statistics(self) -> dict[str, Any]:
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

            cursor = await db.execute("SELECT status, COUNT(*) as count FROM orders GROUP BY status")
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


class PostgresDatabase:
    """Реализация работы с облачной базой данных PostgreSQL (Supabase / Neon) через asyncpg."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None
        self._language_cache: dict[int, str] = {}
        self._active_promo_cache: dict[int, Optional[str]] = {}

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            if asyncpg is None:
                raise RuntimeError("asyncpg is required for PostgreSQL connection. Run: pip install asyncpg")
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                statement_cache_size=0,
                command_timeout=15,
                max_inactive_connection_lifetime=300,
            )
        return self._pool

    async def init(self) -> None:
        """Создает таблицы и индексы в PostgreSQL (Supabase) при первом запуске."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    language TEXT DEFAULT 'ru',
                    referrer_id BIGINT,
                    bonus_balance INTEGER DEFAULT 0,
                    active_promocode TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS promocodes (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    discount_percent INTEGER DEFAULT 0,
                    discount_amount INTEGER DEFAULT 0,
                    max_uses INTEGER DEFAULT 100,
                    used_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    telegram_id BIGINT NOT NULL,
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

                CREATE TABLE IF NOT EXISTS order_photos (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    file_unique_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS order_music (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    file_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
                CREATE INDEX IF NOT EXISTS idx_orders_telegram_id ON orders(telegram_id);
                CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
                CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
                CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
                CREATE INDEX IF NOT EXISTS idx_promocodes_code ON promocodes(code);
            """)

            # Авто-гарантия постоянного промокода TAKLIVO50
            await conn.execute("""
                INSERT INTO promocodes (code, discount_percent, discount_amount, max_uses, used_count, is_active)
                VALUES ('TAKLIVO50', 50, 0, 100, 0, 1)
                ON CONFLICT (code) DO NOTHING;
            """)

    def create_backup_copy(self) -> str:
        return "cloud_supabase_active"

    # --- Пользователи ---

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        language: str = "ru",
        referrer_id: Optional[int] = None,
    ) -> User:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            if row:
                if (username and row["username"] != username) or (first_name and row["first_name"] != first_name):
                    await conn.execute(
                        "UPDATE users SET username = $1, first_name = $2 WHERE telegram_id = $3",
                        username, first_name, telegram_id
                    )
                lang = row["language"] or "ru"
                self._language_cache[telegram_id] = lang
                self._active_promo_cache[telegram_id] = row["active_promocode"]
                return User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=username or row["username"],
                    first_name=first_name or row["first_name"],
                    language=lang,
                    referrer_id=row["referrer_id"],
                    bonus_balance=row["bonus_balance"] or 0,
                    active_promocode=row["active_promocode"],
                    created_at=str(row["created_at"]),
                )

            valid_referrer = referrer_id if referrer_id and referrer_id != telegram_id else None
            initial_bonus = config.REFERRAL_WELCOME_BONUS if valid_referrer else 0

            user_id = await conn.fetchval(
                """
                INSERT INTO users (telegram_id, username, first_name, language, referrer_id, bonus_balance)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                telegram_id, username, first_name, language, valid_referrer, initial_bonus
            )

            self._language_cache[telegram_id] = language
            self._active_promo_cache[telegram_id] = None

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

    async def get_user(self, telegram_id: int) -> Optional[User]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            if row:
                return User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=row["username"],
                    first_name=row["first_name"],
                    language=row["language"] or "ru",
                    referrer_id=row["referrer_id"],
                    bonus_balance=row["bonus_balance"] or 0,
                    active_promocode=row["active_promocode"],
                    created_at=str(row["created_at"]),
                )
            return None

    async def get_user_count(self) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM users") or 0

    async def set_user_active_promocode(self, telegram_id: int, promo_code: Optional[str]) -> None:
        norm_code = promo_code.strip().upper() if promo_code else None
        self._active_promo_cache[telegram_id] = norm_code
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET active_promocode = $1 WHERE telegram_id = $2",
                norm_code, telegram_id
            )

    async def get_user_active_promocode(self, telegram_id: int) -> Optional[str]:
        if telegram_id in self._active_promo_cache:
            return self._active_promo_cache[telegram_id]
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            promo = await conn.fetchval("SELECT active_promocode FROM users WHERE telegram_id = $1", telegram_id)
            self._active_promo_cache[telegram_id] = promo
            return promo

    async def get_user_language(self, telegram_id: int) -> str:
        if telegram_id in self._language_cache:
            return self._language_cache[telegram_id]
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            lang = await conn.fetchval("SELECT language FROM users WHERE telegram_id = $1", telegram_id)
            selected_lang = lang or "ru"
            self._language_cache[telegram_id] = selected_lang
            return selected_lang

    async def set_user_language(self, telegram_id: int, language: str) -> None:
        self._language_cache[telegram_id] = language
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("UPDATE users SET language = $1 WHERE telegram_id = $2", language, telegram_id)

    async def get_user_bonus_balance(self, telegram_id: int) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            bal = await conn.fetchval("SELECT bonus_balance FROM users WHERE telegram_id = $1", telegram_id)
            return bal or 0

    async def add_user_bonus(self, telegram_id: int, amount: int) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            new_bal = await conn.fetchval(
                """
                UPDATE users SET bonus_balance = COALESCE(bonus_balance, 0) + $1 
                WHERE telegram_id = $2 
                RETURNING bonus_balance
                """,
                amount, telegram_id
            )
            return new_bal or 0

    async def deduct_user_bonus(self, telegram_id: int, amount: int) -> bool:
        current_balance = await self.get_user_bonus_balance(telegram_id)
        if current_balance < amount:
            return False
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET bonus_balance = GREATEST(0, bonus_balance - $1) WHERE telegram_id = $2",
                amount, telegram_id
            )
            return True

    async def get_referral_stats(self, telegram_id: int) -> dict[str, int]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            invited_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE referrer_id = $1", telegram_id) or 0
            orders_count = await conn.fetchval(
                """
                SELECT COUNT(o.id)
                FROM orders o
                JOIN users u ON o.telegram_id = u.telegram_id
                WHERE u.referrer_id = $1
                  AND o.status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED')
                """,
                telegram_id
            ) or 0
            bonus_balance = await self.get_user_bonus_balance(telegram_id)
            return {
                "invited_count": invited_count,
                "orders_count": orders_count,
                "bonus_balance": bonus_balance,
            }

    async def get_user_referrer_id(self, telegram_id: int) -> Optional[int]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval("SELECT referrer_id FROM users WHERE telegram_id = $1", telegram_id)

    async def get_user_paid_orders_count(self, telegram_id: int, exclude_order_id: Optional[int] = None) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            if exclude_order_id:
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM orders 
                    WHERE telegram_id = $1 
                      AND status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED') 
                      AND id != $2
                    """,
                    telegram_id, exclude_order_id
                )
            else:
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM orders 
                    WHERE telegram_id = $1 
                      AND status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED')
                    """,
                    telegram_id
                )
            return count or 0

    async def get_all_users(self) -> list[User]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users ORDER BY id ASC")
            return [
                User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=row["username"],
                    first_name=row["first_name"],
                    language=row["language"] or "ru",
                    referrer_id=row["referrer_id"],
                    bonus_balance=row["bonus_balance"] or 0,
                    created_at=str(row["created_at"]),
                )
                for row in rows
            ]

    async def get_recent_users(self, limit: int = 20) -> list[User]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users ORDER BY id DESC LIMIT $1", limit)
            return [
                User(
                    id=row["id"],
                    telegram_id=row["telegram_id"],
                    username=row["username"],
                    first_name=row["first_name"],
                    language=row["language"] or "ru",
                    referrer_id=row["referrer_id"],
                    bonus_balance=row["bonus_balance"] or 0,
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
        code_clean = code.strip().upper()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            promocode_id = await conn.fetchval(
                """
                INSERT INTO promocodes (code, discount_percent, discount_amount, max_uses)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT(code) DO UPDATE SET
                    discount_percent = EXCLUDED.discount_percent,
                    discount_amount = EXCLUDED.discount_amount,
                    max_uses = EXCLUDED.max_uses,
                    is_active = 1
                RETURNING id
                """,
                code_clean, discount_percent, discount_amount, max_uses
            )
            return promocode_id

    async def get_promocode(self, code: str) -> Optional[PromoCode]:
        code_clean = code.strip().upper()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM promocodes WHERE code = $1 AND is_active = 1",
                code_clean
            )
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
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM promocodes ORDER BY id DESC")
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
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM promocodes WHERE id = $1", promocode_id)
            return True

    async def increment_promocode_usage(self, code: str) -> None:
        code_clean = code.strip().upper()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE promocodes SET used_count = used_count + 1 WHERE code = $1",
                code_clean
            )

    async def rollback_promocode_usage(self, code: str) -> None:
        code_clean = code.strip().upper()
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE promocodes SET used_count = GREATEST(0, used_count - 1) WHERE code = $1",
                code_clean
            )

    # --- Заказы ---

    def _row_to_order(self, row) -> Order:
        return Order(
            id=row["id"],
            user_id=row["user_id"],
            telegram_id=row["telegram_id"],
            status=row["status"],
            template_id=row["template_id"],
            template_name=row["template_name"],
            plan=row["plan"],
            event_type=row["event_type"] or "wedding",
            bride_name=row["bride_name"] or "",
            groom_name=row["groom_name"] or "",
            celebrant_name=row["celebrant_name"],
            parents_name=row["parents_name"],
            age_or_details=row["age_or_details"],
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
            promocode=row["promocode"],
            discount_amount=row["discount_amount"] or 0,
            bonus_used=row["bonus_used"] or 0,
            payment_status=row["payment_status"],
            payment_receipt_file_id=row["payment_receipt_file_id"],
            website_url=row["website_url"],
            reference_url=row["reference_url"],
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
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            order_id = await conn.fetchval(
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
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10, $11, $12,
                    $13, $14,
                    $15, $16, $17, $18, $19,
                    $20, $21, $22,
                    $23, $24, $25,
                    $26, $27, $28, $29, $30
                ) RETURNING id
                """,
                user_id, telegram_id, status, template_id, template_name, plan,
                event_type, bride_name, groom_name, celebrant_name, parents_name, age_or_details,
                wedding_date, wedding_time,
                venue, address, phone,
                1 if rsvp_enabled else 0, 1 if map_enabled else 0,
                1 if music_enabled else 0, 1 if gallery_enabled else 0,
                1 if dresscode_enabled else 0, 1 if schedule_enabled else 0,
                1 if second_language_enabled else 0, total_price,
                promocode, discount_amount, bonus_used,
                PaymentStatus.UNPAID.value, reference_url,
            )

            if promocode:
                await conn.execute(
                    "UPDATE promocodes SET used_count = used_count + 1 WHERE code = $1",
                    promocode.strip().upper()
                )

            if bonus_used > 0:
                await conn.execute(
                    "UPDATE users SET bonus_balance = GREATEST(0, bonus_balance - $1) WHERE telegram_id = $2",
                    bonus_used, telegram_id
                )

            return order_id

    async def get_order(self, order_id: int) -> Optional[Order]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM orders WHERE id = $1", order_id)
            if row:
                return self._row_to_order(row)
            return None

    async def get_user_orders(self, telegram_id: int) -> list[Order]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM orders WHERE telegram_id = $1 ORDER BY id DESC", telegram_id)
            return [self._row_to_order(row) for row in rows]

    async def get_orders_by_status(self, status: str, limit: int = 50) -> list[Order]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM orders WHERE status = $1 ORDER BY id DESC LIMIT $2", status, limit)
            return [self._row_to_order(row) for row in rows]

    async def get_recent_orders(self, limit: int = 30) -> list[Order]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM orders ORDER BY id DESC LIMIT $1", limit)
            return [self._row_to_order(row) for row in rows]

    async def get_all_orders(self) -> list[Order]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM orders ORDER BY id ASC")
            return [self._row_to_order(row) for row in rows]

    async def get_orders_due_soon(self, days_ahead: int) -> list[Order]:
        target_date_obj = datetime.now() + timedelta(days=days_ahead)
        target_str = target_date_obj.strftime("%d.%m.%Y")
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM orders
                WHERE wedding_date = $1
                  AND status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'COMPLETED')
                """,
                target_str
            )
            return [self._row_to_order(row) for row in rows]

    async def update_order_status(self, order_id: int, status: str, payment_status: Optional[str] = None) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            if payment_status:
                await conn.execute(
                    "UPDATE orders SET status = $1, payment_status = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $3",
                    status, payment_status, order_id
                )
            else:
                await conn.execute(
                    "UPDATE orders SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                    status, order_id
                )

    async def set_order_receipt(self, order_id: int, file_id: str) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE orders
                SET payment_receipt_file_id = $1, status = $2, payment_status = $3, updated_at = CURRENT_TIMESTAMP
                WHERE id = $4
                """,
                file_id, OrderStatus.PAYMENT_REVIEW.value, PaymentStatus.REVIEW.value, order_id
            )

    async def set_order_website_url(self, order_id: int, url: str) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE orders SET website_url = $1, status = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $3",
                url, OrderStatus.PREVIEW.value, order_id
            )

    async def set_order_revision(self, order_id: int, revision_text: str) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE orders SET revision_text = $1, status = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $3",
                revision_text, OrderStatus.REVISION.value, order_id
            )

    async def add_order_photo(self, order_id: int, file_id: str, file_unique_id: Optional[str] = None) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO order_photos (order_id, file_id, file_unique_id) VALUES ($1, $2, $3)",
                order_id, file_id, file_unique_id
            )

    async def get_order_photos(self, order_id: int) -> list[OrderPhoto]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM order_photos WHERE order_id = $1", order_id)
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

    async def set_order_music(self, order_id: int, file_id: str, file_name: Optional[str] = None) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM order_music WHERE order_id = $1", order_id)
            await conn.execute(
                "INSERT INTO order_music (order_id, file_id, file_name) VALUES ($1, $2, $3)",
                order_id, file_id, file_name
            )

    async def get_order_music(self, order_id: int) -> Optional[OrderMusic]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM order_music WHERE order_id = $1", order_id)
            if row:
                return OrderMusic(
                    id=row["id"],
                    order_id=row["order_id"],
                    file_id=row["file_id"],
                    file_name=row["file_name"],
                    created_at=str(row["created_at"]),
                )
            return None

    async def get_statistics(self) -> dict[str, Any]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users") or 0

            today_date = datetime.utcnow().strftime("%Y-%m-%d")
            today_users = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE to_char(created_at, 'YYYY-MM-DD') = $1",
                today_date
            ) or 0

            current_month = datetime.utcnow().strftime("%Y-%m")
            month_users_reg = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE to_char(created_at, 'YYYY-MM') = $1",
                current_month
            ) or 0

            uz_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE language = 'uz'") or 0
            ru_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE language = 'ru'") or 0
            total_orders = await conn.fetchval("SELECT COUNT(*) FROM orders") or 0

            status_counts_raw = await conn.fetch("SELECT status, COUNT(*) as count FROM orders GROUP BY status")
            status_counts = {row["status"]: row["count"] for row in status_counts_raw}

            total_revenue = await conn.fetchval("""
                SELECT SUM(total_price) 
                FROM orders 
                WHERE status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED')
                   OR payment_status = 'PAID'
            """) or 0

            month_stats = await conn.fetchrow(
                """
                SELECT COUNT(*) as month_orders, SUM(total_price) as month_revenue
                FROM orders
                WHERE to_char(created_at, 'YYYY-MM') = $1
                  AND (status IN ('PAID', 'IN_PROGRESS', 'PREVIEW', 'REVISION', 'COMPLETED') OR payment_status = 'PAID')
                """,
                current_month
            )
            month_orders = month_stats["month_orders"] if month_stats else 0
            month_revenue = month_stats["month_revenue"] if month_stats and month_stats["month_revenue"] else 0

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


class Database:
    """Единый фасад базы данных, автоматически выбирающий PostgreSQL или SQLite."""

    def __init__(self, db_path: str = config.DATABASE_PATH, database_url: Optional[str] = None):
        self._db_path = db_path
        self._database_url = database_url if database_url is not None else config.DATABASE_URL
        self._backend: Any = None
        self._setup_backend()

    def _setup_backend(self) -> None:
        if self._database_url and self._database_url.startswith(("postgres://", "postgresql://")):
            logger.info("Подключение к облачной базе данных PostgreSQL (Supabase)...")
            self._backend = PostgresDatabase(self._database_url)
        else:
            logger.info(f"Подключение к локальной базе данных SQLite: {self._db_path}")
            self._backend = SqliteDatabase(self._db_path)

    @property
    def db_path(self) -> str:
        return self._db_path

    @db_path.setter
    def db_path(self, new_path: str) -> None:
        self._db_path = new_path
        self._database_url = None
        self._backend = SqliteDatabase(new_path)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._backend, name)


db = Database()
