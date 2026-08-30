"""
Модуль интернационализации i18n для бота TAKLIVO.
"""
from typing import Any
from bot.locales.ru import TEXTS as RU_TEXTS
from bot.locales.uz import TEXTS as UZ_TEXTS

LOCALES: dict[str, dict[str, str]] = {
    "ru": RU_TEXTS,
    "uz": UZ_TEXTS,
}


def get_text(language: str, key: str, **kwargs: Any) -> str:
    """
    Возвращает локализованный текст по языку и ключу.
    Если ключ отсутствует в выбранном языке, используется русский fallback.
    """
    locale_dict = LOCALES.get(language, RU_TEXTS)
    text = locale_dict.get(key)
    if text is None:
        text = RU_TEXTS.get(key, f"[{key}]")
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def t(key: str, lang: str = "ru", **kwargs: Any) -> str:
    """
    Алиас для get_text с дефолтным языком 'ru'.
    """
    return get_text(language=lang, key=key, **kwargs)
