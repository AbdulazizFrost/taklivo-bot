"""
Сервис генерации свадебных сайтов и экспорта данных.
Готов к интеграции со статическими генераторами (Next.js / Astro / Vite).
"""
import json
import logging
from typing import Any, Optional
from bot.database.models import Order, OrderPhoto, OrderMusic

logger = logging.getLogger(__name__)


class SiteGeneratorService:
    @staticmethod
    def export_order_to_dict(
        order: Order,
        photos: Optional[list[OrderPhoto]] = None,
        music: Optional[OrderMusic] = None,
    ) -> dict[str, Any]:
        """Преобразует данные заказа в структурированный словарь."""
        return {
            "order_id": order.id,
            "status": order.status,
            "created_at": order.created_at,
            "couple": {
                "bride_name": order.bride_name,
                "groom_name": order.groom_name,
            },
            "event": {
                "wedding_date": order.wedding_date,
                "wedding_time": order.wedding_time,
                "venue": order.venue,
                "address": order.address,
                "phone": order.phone,
            },
            "design": {
                "template_id": order.template_id,
                "template_name": order.template_name,
                "plan": order.plan,
            },
            "options": {
                "rsvp": order.rsvp_enabled,
                "map": order.map_enabled,
                "music": order.music_enabled,
                "gallery": order.gallery_enabled,
                "dresscode": order.dresscode_enabled,
                "schedule": order.schedule_enabled,
                "second_language": order.second_language_enabled,
            },
            "assets": {
                "photo_file_ids": [p.file_id for p in (photos or [])],
                "photos_count": len(photos or []),
                "music_file_id": music.file_id if music else None,
                "music_filename": music.file_name if music else None,
            },
            "payment": {
                "total_price": order.total_price,
                "payment_status": order.payment_status,
                "receipt_file_id": order.payment_receipt_file_id,
            },
            "meta": {
                "telegram_id": order.telegram_id,
                "website_url": order.website_url,
                "revision_text": order.revision_text,
            },
        }

    @classmethod
    def export_order_to_json(
        cls,
        order: Order,
        photos: Optional[list[OrderPhoto]] = None,
        music: Optional[OrderMusic] = None,
    ) -> str:
        """Экспортирует данные заказа в отформатированную JSON строку."""
        data = cls.export_order_to_dict(order, photos, music)
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    async def generate_site(
        cls,
        order: Order,
        photos: Optional[list[OrderPhoto]] = None,
        music: Optional[OrderMusic] = None,
    ) -> str:
        """
        Асинхронный генератор сайта.
        Архитектурно готов к вызову headless build pipeline (Next.js / Astro / GitHub Pages / Vercel).
        """
        logger.info(f"Generating wedding site for order #{order.id} (Template: {order.template_id})")
        
        # Генерация красивого человекочитаемого слага
        slug = f"{order.groom_name.lower()}-{order.bride_name.lower()}".replace(" ", "-")
        generated_url = f"https://taklivo.uz/wedding/{slug}-{order.id}"
        
        return generated_url


site_generator = SiteGeneratorService()


async def generate_site(
    order: Order,
    photos: Optional[list[OrderPhoto]] = None,
    music: Optional[OrderMusic] = None,
) -> str:
    """Удобная функция генерации сайта."""
    return await site_generator.generate_site(order, photos, music)
