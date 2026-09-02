"""
Пакет базы данных.
"""
from bot.database.database import db, Database
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

__all__ = [
    "db",
    "Database",
    "User",
    "Order",
    "OrderPhoto",
    "OrderMusic",
    "OrderStatus",
    "PaymentStatus",
    "EventType",
    "PromoCode",
]
