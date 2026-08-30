"""
Конфигурация проекта TAKLIVO.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class TemplateInfo:
    id: str
    name_ru: str
    name_uz: str
    description_ru: str
    description_uz: str
    demo_url: str
    emoji: str


class Config:
    # Telegram Bot Token
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

    # Telegram ID администраторов
    ADMIN_ID_RAW: str = os.getenv("ADMIN_ID", "").strip()
    ADMIN_IDS: list[int] = []
    if ADMIN_ID_RAW:
        for item in ADMIN_ID_RAW.split(","):
            clean_item = item.strip()
            if clean_item.isdigit():
                ADMIN_IDS.append(int(clean_item))

    # Юзернейм администратора для связи и поддержки клиентов
    SUPPORT_ADMIN: str = os.getenv("SUPPORT_ADMIN", "@Abdulaziz5335").strip()

    # Instagram аккаунт сервиса
    INSTAGRAM_URL: str = os.getenv("INSTAGRAM_URL", "https://www.instagram.com/wedding_websites_uzbekistan/").strip()
    INSTAGRAM_HANDLE: str = "@wedding_websites_uzbekistan"

    # Реквизиты оплаты
    PAYMENT_DETAILS: str = os.getenv(
        "PAYMENT_DETAILS",
        "💳 Карта: 5614 6812 5985 0075 (Humo/Uzcard)\n👤 Получатель: Abdulaziz Sidikov",
    ).replace(r"\n", "\n")

    # База данных
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", os.getenv("DB_PATH", "data/wedding_bot.db"))

    # Базовая стоимость создания сайта
    BASE_PRICE: int = int(os.getenv("BASE_PRICE", "50000"))

    # Цены на дополнительные функции (в сумах)
    TIMER_PRICE: int = int(os.getenv("TIMER_PRICE", "10000"))
    RSVP_PRICE: int = int(os.getenv("RSVP_PRICE", "20000"))
    MAP_PRICE: int = int(os.getenv("MAP_PRICE", "10000"))
    GALLERY_PRICE: int = int(os.getenv("GALLERY_PRICE", "20000"))
    MUSIC_PRICE: int = int(os.getenv("MUSIC_PRICE", "10000"))
    DRESSCODE_PRICE: int = int(os.getenv("DRESSCODE_PRICE", "10000"))
    SCHEDULE_PRICE: int = int(os.getenv("SCHEDULE_PRICE", "10000"))
    SECOND_LANGUAGE_PRICE: int = int(os.getenv("SECOND_LANGUAGE_PRICE", "10000"))

    # Каталог свадебных шаблонов
    TEMPLATES: dict[str, TemplateInfo] = {
        "floral": TemplateInfo(
            id="floral",
            name_ru="🌸 Floral",
            name_uz="🌸 Floral",
            description_ru="Нежный романтичный дизайн с цветочными акварельными иллюстрациями и плавной анимацией.",
            description_uz="Gulli akvarel rasmlar va mayin animatsiyalarga ega romantik nafis dizayn.",
            demo_url=os.getenv("DEMO_FLORAL_URL", "https://taklivo.uz/demo/floral"),
            emoji="🌸",
        ),
        "luxury_gold": TemplateInfo(
            id="luxury_gold",
            name_ru="🥂 Luxury Gold",
            name_uz="🥂 Luxury Gold",
            description_ru="Элегантная золотая классика для пышного торжества с золотым тиснением и шрифтами с засечками.",
            description_uz="Hashamatli to‘y uchun tillarang va nafis klassik uslubdagi premium dizayn.",
            demo_url=os.getenv("DEMO_LUXURY_GOLD_URL", "https://taklivo.uz/demo/luxury-gold"),
            emoji="🥂",
        ),
        "dark_luxury": TemplateInfo(
            id="dark_luxury",
            name_ru="🖤 Dark Luxury",
            name_uz="🖤 Dark Luxury",
            description_ru="Глубокий темный фон, золотые неоновые элементы и кинематографичный стиль.",
            description_uz="To‘q fon, oltin neon effektlar va kinematik jozibadorlik.",
            demo_url=os.getenv("DEMO_DARK_LUXURY_URL", "https://taklivo.uz/demo/dark-luxury"),
            emoji="🖤",
        ),
        "minimal": TemplateInfo(
            id="minimal",
            name_ru="🤍 Minimal",
            name_uz="🤍 Minimal",
            description_ru="Идеальная чистота, много пространства, утонченная типографика и легкость восприятия.",
            description_uz="Mukammal tozalik, ko‘p bo‘sh joy, nafis tipografika va yengil uslub.",
            demo_url=os.getenv("DEMO_MINIMAL_URL", "https://taklivo.uz/demo/minimal"),
            emoji="🤍",
        ),
        "boho": TemplateInfo(
            id="boho",
            name_ru="🌿 Boho",
            name_uz="🌿 Boho",
            description_ru="Природные пастельные тона, сухоцветы, пампасная трава и уютная теплая эстетика.",
            description_uz="Tabiiy pastel ranglar, quritilgan gullar va iliq shinam estetika.",
            demo_url=os.getenv("DEMO_BOHO_URL", "https://taklivo.uz/demo/boho"),
            emoji="🌿",
        ),
        "oriental": TemplateInfo(
            id="oriental",
            name_ru="🕌 Oriental",
            name_uz="🕌 Oriental",
            description_ru="Восточные национальные орнаменты, вензеля и торжественное величие традиций.",
            description_uz="Sharqona milliy naqshlar, bezaklar va milliy an’analarning go‘zalligi.",
            demo_url=os.getenv("DEMO_ORIENTAL_URL", "https://taklivo.uz/demo/oriental"),
            emoji="🕌",
        ),
        "modern": TemplateInfo(
            id="modern",
            name_ru="✨ Modern",
            name_uz="✨ Modern",
            description_ru="Современный динамичный стиль со стильными карточками, интерактивными свайпами и таймером.",
            description_uz="Zamonaviy interaktiv kartochkalar, animatsiyalar va dinamik ko‘rinish.",
            demo_url=os.getenv("DEMO_MODERN_URL", "https://taklivo.uz/demo/modern"),
            emoji="✨",
        ),
    }

    @classmethod
    def get_extra_options_prices(cls) -> dict[str, int]:
        """Возвращает цены на все опции конструктора."""
        return {
            "timer": cls.TIMER_PRICE,
            "rsvp": cls.RSVP_PRICE,
            "map": cls.MAP_PRICE,
            "gallery": cls.GALLERY_PRICE,
            "music": cls.MUSIC_PRICE,
            "dresscode": cls.DRESSCODE_PRICE,
            "schedule": cls.SCHEDULE_PRICE,
            "second_language": cls.SECOND_LANGUAGE_PRICE,
        }

    @classmethod
    def validate(cls) -> None:
        """Проверка обязательных настроек перед запуском бота."""
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print(
                "❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не задан в .env файле!\n"
                "Создайте файл .env и укажите токен от @BotFather.",
                file=sys.stderr,
            )
            sys.exit(1)


config = Config()
