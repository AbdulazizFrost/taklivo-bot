"""
REST API модуль для сайтов-приглашений (HTML / Next.js / Astro).
Предоставляет эндпоинты для проверки статуса оплаты, демо-режима, водяного знака и полных данных заказа.
"""
from datetime import datetime, timezone
import logging
from typing import Optional
from aiohttp import web

from bot.database import db, PaymentStatus, OrderStatus
from bot.services.site_generator import SiteGeneratorService

logger = logging.getLogger(__name__)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}


def parse_db_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Парсит строку времени из SQLite или PostgreSQL в UTC datetime."""
    if not ts_str:
        return None
    cleaned = ts_str.strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            dt = datetime.strptime(cleaned.split("+")[0], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


async def handle_options(request: web.Request) -> web.Response:
    """Обработчик CORS preflight OPTIONS запросов."""
    return web.Response(status=204, headers=CORS_HEADERS)


async def get_order_status(request: web.Request) -> web.Response:
    """
    Эндпоинт проверки статуса заказа:
    GET /api/order/{order_id}/status
    Возвращает is_paid, is_demo, is_expired, watermark, demo_remaining_seconds.
    """
    order_id_str = request.match_info.get("order_id", "")
    try:
        order_id = int(order_id_str)
    except ValueError:
        return web.json_response(
            {"error": "Invalid order_id", "order_id": order_id_str},
            status=400,
            headers=CORS_HEADERS,
        )

    order = await db.get_order(order_id)
    if not order:
        return web.json_response(
            {"error": "Order not found", "order_id": order_id},
            status=404,
            headers=CORS_HEADERS,
        )

    is_paid = (order.payment_status == PaymentStatus.PAID.value) or (order.status == OrderStatus.COMPLETED.value)
    is_demo = not is_paid

    # 24-часовой таймер демо-доступа
    is_expired = False
    demo_remaining_seconds = 0

    if is_demo:
        timestamp_to_use = order.updated_at if order.website_url else (order.created_at or order.updated_at)
        ref_dt = parse_db_timestamp(timestamp_to_use)
        if ref_dt:
            elapsed = (datetime.now(timezone.utc) - ref_dt).total_seconds()
            demo_remaining_seconds = max(0, int(86400 - elapsed))
            if demo_remaining_seconds == 0 and elapsed >= 86400:
                is_expired = True
        else:
            demo_remaining_seconds = 86400

    response_data = {
        "order_id": order.id,
        "status": order.status,
        "payment_status": order.payment_status,
        "is_paid": is_paid,
        "is_demo": is_demo,
        "is_expired": is_expired,
        "demo_remaining_seconds": demo_remaining_seconds,
        "watermark": "TAKLIVO DEMO PREVIEW" if is_demo else None,
        "website_url": order.website_url,
        "event_type": order.event_type,
        "template_id": order.template_id,
        "couple": {
            "bride_name": order.bride_name,
            "groom_name": order.groom_name,
        } if order.event_type == "wedding" else None,
        "celebrant": {
            "name": order.celebrant_name,
            "parents_name": order.parents_name,
            "age_or_details": order.age_or_details,
        } if order.event_type in ("birthday", "sunnat") else None,
    }
    return web.json_response(response_data, headers=CORS_HEADERS)


async def get_order_full_data(request: web.Request) -> web.Response:
    """
    Эндпоинт получения всех данных заказа для статических генераторов (Astro/Next.js):
    GET /api/order/{order_id}
    """
    order_id_str = request.match_info.get("order_id", "")
    try:
        order_id = int(order_id_str)
    except ValueError:
        return web.json_response(
            {"error": "Invalid order_id", "order_id": order_id_str},
            status=400,
            headers=CORS_HEADERS,
        )

    order = await db.get_order(order_id)
    if not order:
        return web.json_response(
            {"error": "Order not found", "order_id": order_id},
            status=404,
            headers=CORS_HEADERS,
        )

    photos = await db.get_order_photos(order_id)
    music = await db.get_order_music(order_id)
    data = SiteGeneratorService.export_order_to_dict(order, photos, music)

    # Добавляем статус демо и таймер
    is_paid = (order.payment_status == PaymentStatus.PAID.value) or (order.status == OrderStatus.COMPLETED.value)
    is_demo = not is_paid
    is_expired = False
    demo_remaining = 0
    if is_demo:
        timestamp_to_use = order.updated_at if order.website_url else (order.created_at or order.updated_at)
        ref_dt = parse_db_timestamp(timestamp_to_use)
        if ref_dt:
            elapsed = (datetime.now(timezone.utc) - ref_dt).total_seconds()
            demo_remaining = max(0, int(86400 - elapsed))
            if demo_remaining == 0 and elapsed >= 86400:
                is_expired = True
        else:
            demo_remaining = 86400

    data["is_paid"] = is_paid
    data["is_expired"] = is_expired
    data["demo_remaining_seconds"] = demo_remaining

    return web.json_response(data, headers=CORS_HEADERS)


def setup_api_routes(app: web.Application) -> None:
    """Регистрирует маршруты API в приложении aiohttp."""
    app.router.add_options("/api/order/{order_id}/status", handle_options)
    app.router.add_get("/api/order/{order_id}/status", get_order_status)
    app.router.add_options("/api/order/{order_id}", handle_options)
    app.router.add_get("/api/order/{order_id}", get_order_full_data)
    logger.info("REST API маршруты для сайтов-приглашений (/api/order/...) успешно зарегистрированы.")
