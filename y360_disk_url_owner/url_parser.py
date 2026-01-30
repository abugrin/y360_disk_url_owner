"""
Модуль для парсинга и нормализации URL Яндекс Диска.
Поддерживает три формата:
1. Короткие ссылки: https://disk.yandex.ru/d/446d6f44-bb36-48bb-973c-4e1c71e33ccd
2. Полные ссылки: https://disk.yandex.ru/public/?hash=dAEMkc1Q...
3. Просто хеш: dAEMkc1QDY4SPb5+BlFnEKkx1oWX7/p5zYSCvHGQ5/6FQeE4ICFyXScld621gdJYq/J6bpmRyOJonT3VoXnDag==
"""

import re
from urllib.parse import parse_qs, unquote, urlparse


class URLParseError(Exception):
    """Исключение при ошибке парсинга URL."""
    pass


def normalize_url(url: str) -> str:
    """
    Нормализует URL Яндекс Диска к единому формату для API.

    Args:
        url: URL в любом из поддерживаемых форматов

    Returns:
        Нормализованный URL для передачи в API

    Raises:
        URLParseError: Если URL не соответствует ни одному из поддерживаемых форматов
    """
    # Убираем лишние пробелы
    url = url.strip()

    if not url:
        raise URLParseError("URL не может быть пустым")

    # Пытаемся определить тип URL
    # 1. Проверяем короткую ссылку: https://disk.yandex.ru/d/...
    short_pattern = r'https?://disk\.yandex\.ru/d/([a-zA-Z0-9\-]+)'
    short_match = re.match(short_pattern, url)
    if short_match:
        # Короткая ссылка валидна, возвращаем её как есть
        return url

    # 2. Проверяем полную ссылку: https://disk.yandex.ru/public/?hash=...
    if url.startswith('http'):
        parsed = urlparse(url)
        
        # Проверяем, что это disk.yandex.ru
        if 'disk.yandex.ru' not in parsed.netloc:
            raise URLParseError(f"URL не является ссылкой на Яндекс Диск: {parsed.netloc}")
        
        # Пытаемся извлечь hash из параметров
        query_params = parse_qs(parsed.query)
        if 'hash' in query_params:
            hash_value = query_params['hash'][0]
            # Декодируем если нужно
            hash_value = unquote(hash_value)
            # Возвращаем полный URL с хешем
            return f"https://disk.yandex.ru/public/?hash={hash_value}"
        
        # Если это /d/ ссылка без совпадения с паттерном выше
        if '/d/' in parsed.path:
            return url
        
        raise URLParseError("URL не содержит параметр hash или корректный путь /d/")

    # 3. Предполагаем, что это просто хеш
    # Хеш может содержать буквы, цифры, +, /, =
    hash_pattern = r'^[a-zA-Z0-9+/]+=*$'
    if re.match(hash_pattern, url):
        # Это похоже на хеш, возвращаем его как есть
        # API примет его напрямую
        return url

    raise URLParseError(
        "URL не соответствует ни одному из поддерживаемых форматов:\n"
        "1. Короткая ссылка: https://disk.yandex.ru/d/...\n"
        "2. Полная ссылка: https://disk.yandex.ru/public/?hash=...\n"
        "3. Хеш: dAEMkc1Q..."
    )


def is_valid_disk_url(url: str) -> bool:
    """
    Проверяет, является ли URL валидной ссылкой на Яндекс Диск.

    Args:
        url: URL для проверки

    Returns:
        True если URL валиден, иначе False
    """
    try:
        normalize_url(url)
        return True
    except URLParseError:
        return False


def get_url_type(url: str) -> str:
    """
    Определяет тип URL.

    Args:
        url: URL для анализа

    Returns:
        Один из: "short", "full", "hash", "unknown"
    """
    url = url.strip()

    # Короткая ссылка
    if re.match(r'https?://disk\.yandex\.ru/d/', url):
        return "short"

    # Полная ссылка
    if url.startswith('http'):
        parsed = urlparse(url)
        if 'disk.yandex.ru' in parsed.netloc:
            query_params = parse_qs(parsed.query)
            if 'hash' in query_params:
                return "full"

    # Хеш
    hash_pattern = r'^[a-zA-Z0-9+/]+=*$'
    if re.match(hash_pattern, url):
        return "hash"

    return "unknown"
