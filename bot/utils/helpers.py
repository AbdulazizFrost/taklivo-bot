"""
Вспомогательные функции для форматирования и обработки данных.
"""
from datetime import datetime
import html
from bot.locales import t


def format_currency(amount: int, lang: str = "ru") -> str:
    """
    Форматирует число в денежную строку: 349000 -> '349 000 сум' (или '349 000 so‘m').
    """
    # Разделяем тысячи пробелом
    formatted_num = f"{amount:,}".replace(",", " ")
    currency_suffix = "so‘m" if lang == "uz" else "сум"
    return f"{formatted_num} {currency_suffix}"


def format_date_pretty(date_str: str, lang: str = "ru") -> str:
    """
    Преобразует 15.09.2026 в красивый вид: 15 сентября 2026 или 15-sentabr 2026.
    """
    months_ru = [
        "", "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    months_uz = [
        "", "yanvar", "fevral", "mart", "aprel", "may", "iyun",
        "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"
    ]
    
    try:
        dt = datetime.strptime(date_str.strip(), "%d.%m.%Y")
        if lang == "uz":
            return f"{dt.day}-{months_uz[dt.month]} {dt.year}-yil"
        return f"{dt.day} {months_ru[dt.month]} {dt.year} г."
    except Exception:
        return date_str


def get_status_badge(status: str, lang: str = "ru") -> str:
    """
    Возвращает локализованный статус с эмодзи.
    """
    key = f"status_{status}"
    return t(key, lang=lang)


def escape(text: str | None) -> str:
    """
    Экранирует HTML-теги для безопасного вывода в Telegram.
    """
    if not text:
        return ""
    return html.escape(str(text))
