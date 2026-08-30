"""
Пакет обработчиков команд и сообщений.
"""
from bot.handlers.client import router as client_router
from bot.handlers.order import router as order_router
from bot.handlers.admin import router as admin_router

__all__ = ["client_router", "order_router", "admin_router"]
