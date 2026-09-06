"""
REST API модуль для сайтов-приглашений (HTML / Next.js / Astro).
Предоставляет эндпоинты для проверки статуса оплаты, демо-режима, водяного знака, полных данных заказа,
приема RSVP ответов от гостей, а также раздачи шаблонов сайтов (/demo/...).
"""
from datetime import datetime, timezone
import logging
import os
from typing import Any, Optional
from aiohttp import web

from bot.database import db, PaymentStatus, OrderStatus
from bot.services.site_generator import SiteGeneratorService

logger = logging.getLogger(__name__)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}

_bot_instance: Optional[Any] = None


def set_api_bot(bot: Any) -> None:
    """Сохраняет экземпляр бота для отправки уведомлений о RSVP гостях."""
    global _bot_instance
    _bot_instance = bot


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


async def handle_order_rsvp(request: web.Request) -> web.Response:
    """
    Принимает подтверждение присутствия (RSVP) от гостей с веб-сайта:
    POST /api/order/{order_id}/rsvp
    """
    order_id_str = request.match_info.get("order_id", "")
    try:
        order_id = int(order_id_str)
    except ValueError:
        return web.json_response(
            {"error": "Invalid order_id"},
            status=400,
            headers=CORS_HEADERS,
        )

    order = await db.get_order(order_id)
    if not order:
        return web.json_response(
            {"error": "Order not found"},
            status=404,
            headers=CORS_HEADERS,
        )

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    name = str(payload.get("name", "Mehmon")).strip()
    phone = str(payload.get("phone", "")).strip()
    status = str(payload.get("status", "Albatta boraman")).strip()
    message = str(payload.get("message", "")).strip()

    logger.info(f"RSVP received for order #{order_id} from {name} ({phone}): {status}")

    # Отправка уведомления владельцу заказа в Telegram
    if _bot_instance and order.telegram_id:
        try:
            status_emoji = "✅" if "boraman" in status.lower() or "приду" in status.lower() else "❌"
            rsvp_msg = (
                f"💌 <b>Yangi RSVP javobi! (Buyurtma #{order.id})</b>\n\n"
                f"👤 <b>Mehmon:</b> {name}\n"
                f"📞 <b>Telefon:</b> {phone}\n"
                f"{status_emoji} <b>Holat:</b> {status}\n"
            )
            if message:
                rsvp_msg += f"💬 <b>Tilak:</b> <i>«{message}»</i>\n"
            await _bot_instance.send_message(
                chat_id=order.telegram_id,
                text=rsvp_msg,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление о RSVP клиенту {order.telegram_id}: {e}")

    return web.json_response(
        {"success": True, "message": "RSVP successfully submitted"},
        headers=CORS_HEADERS,
    )


def setup_api_routes(app: web.Application) -> None:
    """Регистрирует маршруты API и раздачу шаблонов в aiohttp."""
    # REST API эндпоинты
    app.router.add_options("/api/order/{order_id}/status", handle_options)
    app.router.add_get("/api/order/{order_id}/status", get_order_status)
    app.router.add_options("/api/order/{order_id}", handle_options)
    app.router.add_get("/api/order/{order_id}", get_order_full_data)
    app.router.add_options("/api/order/{order_id}/rsvp", handle_options)
    app.router.add_post("/api/order/{order_id}/rsvp", handle_order_rsvp)

    # Веб-шаблоны и демо-витрина
    templates_demo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "demo")

    if os.path.exists(templates_demo_dir):
        async def serve_demo_catalog(request: web.Request) -> web.Response:
            """Отдает главную витрину со всеми дизайнами."""
            if not request.path.endswith("/"):
                raise web.HTTPMovedPermanently(f"{request.path}/")
            index_path = os.path.join(templates_demo_dir, "index.html")
            if os.path.exists(index_path):
                return web.FileResponse(index_path)
            return web.Response(text="TAKLIVO Demo Showcase", status=200)

        async def serve_demo_template(request: web.Request) -> web.Response:
            """Отдает конкретный шаблон сайта (luxury-gold, floral, dark-luxury, minimal, modern...)."""
            template = request.match_info.get("template", "").strip().lower().replace("_", "-")
            # Критически важно: без завершающего слэша браузер ищет style.css в /demo/style.css вместо /demo/{template}/style.css
            if not request.path.endswith("/"):
                raise web.HTTPMovedPermanently(f"{request.path}/")

            template_path = os.path.join(templates_demo_dir, template, "index.html")
            if os.path.exists(template_path):
                return web.FileResponse(template_path)
            return web.Response(text=f"Шаблон '{template}' не найден.", status=404)

        app.router.add_get("/demo", serve_demo_catalog)
        app.router.add_get("/demo/", serve_demo_catalog)
        app.router.add_get("/demo/{template}", serve_demo_template)
        app.router.add_get("/demo/{template}/", serve_demo_template)
        app.router.add_static("/demo", templates_demo_dir)
        
        # Резервный маршрут для общих assets engine.css/engine.js
        assets_dir = os.path.join(templates_demo_dir, "assets")
        if os.path.exists(assets_dir):
            app.router.add_static("/assets", assets_dir)

        logger.info(f"Веб-шаблоны (/demo/*) успешно подключены из: {templates_demo_dir}")

    # Сайты готовых заказов клиентов (/orders/{order_id})
    templates_orders_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "orders")
    os.makedirs(templates_orders_dir, exist_ok=True)

    async def serve_client_order(request: web.Request) -> web.Response:
        """Отдает персональный сайт заказа клиента (/orders/{order_id} или /order/{order_id})."""
        order_id = request.match_info.get("order_id", "").strip()
        if not request.path.endswith("/"):
            raise web.HTTPMovedPermanently(f"{request.path}/")

        site_path = os.path.join(templates_orders_dir, order_id, "index.html")
        if os.path.exists(site_path):
            return web.FileResponse(site_path)
        # Fallback на динамический демо-шаблон по номеру заказа
        if order_id.isdigit():
            order = await db.get_order(int(order_id))
            if order:
                template_folder = order.template_id.replace("_", "-")
                tmpl_path = os.path.join(templates_demo_dir, template_folder, "index.html")
                if os.path.exists(tmpl_path):
                    return web.FileResponse(tmpl_path)
        return web.Response(text=f"Сайт для заказа #{order_id} не найден.", status=404)

    app.router.add_get("/orders/{order_id}", serve_client_order)
    app.router.add_get("/orders/{order_id}/", serve_client_order)
    app.router.add_get("/order/{order_id}", serve_client_order)
    app.router.add_get("/order/{order_id}/", serve_client_order)
    app.router.add_static("/orders", templates_orders_dir)

    logger.info("REST API маршруты для сайтов-приглашений (/api/order/...) успешно зарегистрированы.")
