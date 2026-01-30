"""
Модуль для управления конфигурацией приложения.
Сохраняет и загружает токен API и org_id из .env файла.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv, set_key


class ConfigManager:
    """Управление конфигурационными параметрами приложения."""

    def __init__(self):
        """Инициализация менеджера конфигурации."""
        self.config_dir = Path.home() / ".y360_disk_owner"
        self.env_file = self.config_dir / ".env"

    def exists(self) -> bool:
        """
        Проверяет, существует ли файл конфигурации.

        Returns:
            True если файл существует, иначе False
        """
        return self.env_file.exists()

    def load(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Загружает конфигурацию из .env файла.

        Returns:
            Кортеж (token, org_id) или (None, None) если файл не найден
        """
        if not self.exists():
            return None, None

        load_dotenv(self.env_file)
        token = os.getenv("API_TOKEN")
        org_id = os.getenv("ORG_ID")

        return token, org_id

    def save(self, token: str, org_id: str) -> None:
        """
        Сохраняет конфигурацию в .env файл.

        Args:
            token: OAuth токен для доступа к API
            org_id: Идентификатор организации
        """
        # Создаем директорию если её нет
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Создаем файл если его нет
        if not self.env_file.exists():
            self.env_file.touch(mode=0o600)  # Создаем с ограниченными правами

        # Сохраняем параметры
        set_key(self.env_file, "API_TOKEN", token)
        set_key(self.env_file, "ORG_ID", org_id)

        # Устанавливаем права доступа только для владельца
        os.chmod(self.env_file, 0o600)

    def get_masked_token(self, token: str) -> str:
        """
        Возвращает частично скрытый токен для безопасного отображения.

        Args:
            token: Полный токен

        Returns:
            Замаскированный токен в формате "ya_oauth_xxxx...xxxx1234"
        """
        if not token or len(token) < 12:
            return "***"

        # Показываем первые 9 символов и последние 4
        prefix = token[:9] if len(token) > 9 else token[:3]
        suffix = token[-4:] if len(token) > 4 else ""

        return f"{prefix}...{suffix}"

    def delete(self) -> None:
        """Удаляет файл конфигурации."""
        if self.env_file.exists():
            self.env_file.unlink()

    def get_config_path(self) -> str:
        """
        Возвращает путь к файлу конфигурации.

        Returns:
            Строка с полным путём к .env файлу
        """
        return str(self.env_file)
