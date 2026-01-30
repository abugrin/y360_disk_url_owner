"""
Клиент для работы с Яндекс 360 API.
Содержит методы для проверки токена, получения информации о владельце ресурса
и данных пользователей.
"""

from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import requests


class YandexAPIError(Exception):
    """Базовое исключение для ошибок API."""
    pass


class YandexAPIClient:
    """Клиент для работы с Яндекс 360 API."""

    # Базовые URL для API
    DIRECTORY_API_BASE = "https://api360.yandex.net"
    DISK_API_BASE = "https://cloud-api.yandex.net"

    # Требуемые scope для работы приложения
    REQUIRED_SCOPES = {
        "disk": ["cloud_api:disk.read", "cloud_api:disk.write"],
        "users": ["directory:read_users", "directory:write_users"],
    }

    def __init__(self, token: str):
        """
        Инициализация клиента.

        Args:
            token: OAuth токен для доступа к API
        """
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json",
        })

    def whoami(self) -> Dict:
        """
        Получает информацию о текущем токене.

        Returns:
            Словарь с полями: login, scopes, orgIds

        Raises:
            YandexAPIError: При ошибке запроса
        """
        url = f"{self.DIRECTORY_API_BASE}/whoami"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise YandexAPIError(f"Ошибка при вызове whoami: {e}")

    def validate_scopes(self, scopes: List[str]) -> Tuple[bool, List[str]]:
        """
        Проверяет наличие необходимых scope в токене.
        Учитывает, что scope на запись включают scope на чтение.

        Args:
            scopes: Список scope из токена

        Returns:
            Кортеж (is_valid, missing_scopes)
            - is_valid: True если все необходимые scope присутствуют
            - missing_scopes: Список недостающих scope
        """
        scopes_set = set(scopes)
        missing_scopes = []

        # Проверка disk scope
        has_disk = False
        for scope in self.REQUIRED_SCOPES["disk"]:
            if scope in scopes_set:
                has_disk = True
                break
        if not has_disk:
            missing_scopes.append("cloud_api:disk.read")

        # Проверка users scope
        has_users = False
        for scope in self.REQUIRED_SCOPES["users"]:
            if scope in scopes_set:
                has_users = True
                break
        if not has_users:
            missing_scopes.append("directory:read_users")

        is_valid = len(missing_scopes) == 0
        return is_valid, missing_scopes

    def get_resource_owner(self, public_url: str) -> Tuple[int, int]:
        """
        Получает владельца публичного ресурса по URL.

        Args:
            public_url: Публичная ссылка на ресурс (может быть в любом формате)

        Returns:
            Кортеж (owner_uid, org_id)

        Raises:
            YandexAPIError: При ошибке запроса или если владелец не найден
        """
        url = f"{self.DISK_API_BASE}/v1/disk/public/resources/admin/public-settings"
        
        # URL-encode публичного ключа
        encoded_key = quote(public_url, safe='')
        
        params = {"public_key": encoded_key}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Ищем владельца в списке accesses
            accesses = data.get("accesses", [])
            for access in accesses:
                if access.get("type") == "owner":
                    owner_uid = access.get("id")
                    org_id = access.get("org_id")
                    
                    if owner_uid is None or org_id is None:
                        raise YandexAPIError("Владелец найден, но данные неполные")
                    
                    return int(owner_uid), int(org_id)

            raise YandexAPIError("Владелец ресурса не найден в данных о доступе")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise YandexAPIError("Публичный ресурс не найден или не принадлежит вашей организации")
            elif e.response.status_code == 403:
                raise YandexAPIError("Недостаточно прав для доступа к информации о ресурсе")
            elif e.response.status_code == 401:
                raise YandexAPIError("Неверный токен авторизации")
            else:
                raise YandexAPIError(f"Ошибка HTTP {e.response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise YandexAPIError(f"Ошибка при получении информации о ресурсе: {e}")

    def get_user_info(self, org_id: int, user_id: int) -> Dict:
        """
        Получает информацию о пользователе.

        Args:
            org_id: Идентификатор организации
            user_id: Идентификатор пользователя (UID)

        Returns:
            Словарь с информацией о пользователе, включая:
            - id: UID пользователя
            - email: Email
            - name.first: Имя
            - name.last: Фамилия
            - name.middle: Отчество
            - nickname: Логин

        Raises:
            YandexAPIError: При ошибке запроса
        """
        url = f"{self.DIRECTORY_API_BASE}/directory/v1/org/{org_id}/users/{user_id}"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise YandexAPIError(f"Пользователь с ID {user_id} не найден в организации {org_id}")
            elif e.response.status_code == 403:
                raise YandexAPIError("Недостаточно прав для получения информации о пользователе")
            elif e.response.status_code == 401:
                raise YandexAPIError("Неверный токен авторизации")
            else:
                raise YandexAPIError(f"Ошибка HTTP {e.response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise YandexAPIError(f"Ошибка при получении информации о пользователе: {e}")

    def close(self):
        """Закрывает сессию."""
        self.session.close()
