"""
Модуль валидации пользовательского ввода.
"""
from datetime import datetime
import re
from urllib.parse import urlparse


def validate_date(text: str) -> tuple[bool, str | None]:
    """
    Валидирует строку с датой (ДД.ММ.ГГГГ).
    Возвращает (is_valid, formatted_date_or_error_msg).
    """
    cleaned = text.strip().replace("/", ".").replace("-", ".")
    pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    
    if not re.match(pattern, cleaned):
        return False, None
    
    try:
        parsed_date = datetime.strptime(cleaned, "%d.%m.%Y")
        # Проверяем, чтобы год был адекватным (например от текущего года до +5 лет)
        current_year = datetime.now().year
        if parsed_date.year < current_year - 1 or parsed_date.year > current_year + 5:
            return False, None
        return True, cleaned
    except ValueError:
        return False, None


def validate_time(text: str) -> tuple[bool, str | None]:
    """
    Валидирует строку со временем (ЧЧ:ММ).
    Возвращает (is_valid, formatted_time).
    """
    cleaned = text.strip().replace(".", ":").replace("-", ":")
    pattern = r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    
    if not re.match(pattern, cleaned):
        return False, None
    
    try:
        parsed_time = datetime.strptime(cleaned, "%H:%M")
        return True, parsed_time.strftime("%H:%M")
    except ValueError:
        return False, None


def validate_phone(text: str) -> tuple[bool, str | None]:
    """
    Валидирует номер телефона.
    Поддерживает форматы +998901234567, 998901234567, 8901234567 и т.д.
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", text.strip())
    
    if not cleaned:
        return False, None
    
    # Если начинается с +, проверяем цифры после +
    if cleaned.startswith("+"):
        digits = cleaned[1:]
    else:
        digits = cleaned
    
    if not digits.isdigit():
        return False, None
    
    # Длина номера от 9 до 15 цифр
    if len(digits) < 9 or len(digits) > 15:
        return False, None
    
    # Автоматически добавляем + если нет
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
        
    return True, cleaned


def validate_url(url: str) -> bool:
    """
    Проверяет валидность веб-ссылки (URL).
    """
    if not url:
        return False
    try:
        result = urlparse(url.strip())
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False
