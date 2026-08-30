"""
Пакет сервисов.
"""
from bot.services.calculator import calculator, PriceCalculator, calculate_total
from bot.services.order_service import order_service, OrderService
from bot.services.notifications import notifications, NotificationService
from bot.services.site_generator import site_generator, SiteGeneratorService, generate_site

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
    "generate_site",
]
