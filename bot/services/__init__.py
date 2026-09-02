"""
Пакет сервисов.
"""
from bot.services.calculator import calculator, PriceCalculator, calculate_total
from bot.services.order_service import order_service, OrderService
from bot.services.notifications import notifications, NotificationService
from bot.services.site_generator import site_generator, SiteGeneratorService
from bot.services.exporter import exporter, ExporterService
from bot.services.broadcaster import broadcaster, BroadcasterService
from bot.services.reminder import reminder, ReminderService

__all__ = [
    "calculator",
    "PriceCalculator",
    "calculate_total",
    "order_service",
    "OrderService",
    "notifications",
    "NotificationService",
    "site_generator",
    "SiteGeneratorService",
    "exporter",
    "ExporterService",
    "broadcaster",
    "BroadcasterService",
    "reminder",
    "ReminderService",
]
