"""
Главный модуль приложения.
Содержит основную логику и entry point.
"""

import sys
from typing import Optional, Tuple

from .api_client import YandexAPIClient, YandexAPIError
from .config import ConfigManager
from .ui import UI
from .url_parser import URLParseError, normalize_url


class Application:
    """Основной класс приложения."""

    def __init__(self):
        """Инициализация приложения."""
        self.ui = UI()
        self.config = ConfigManager()
        self.api_client: Optional[YandexAPIClient] = None

    def run(self):
        """Запуск приложения."""
        try:
            # Показываем приветствие
            self.ui.show_welcome()

            # Проверяем и настраиваем конфигурацию
            if not self.setup_config():
                self.ui.show_goodbye()
                return

            # Основной цикл работы
            self.main_loop()

        except KeyboardInterrupt:
            self.ui.console.print("\n")
            self.ui.show_info("Работа прервана пользователем")
            self.ui.show_goodbye()
        except Exception as e:
            self.ui.show_error(f"Непредвиденная ошибка: {e}")
            sys.exit(1)
        finally:
            if self.api_client:
                self.api_client.close()

    def setup_config(self) -> bool:
        """
        Настройка конфигурации.

        Returns:
            True если конфигурация успешно настроена, False если пользователь отменил
        """
        # Проверяем наличие конфигурации
        if self.config.exists():
            # Загружаем существующую конфигурацию
            token, org_id = self.config.load()
            
            if token and org_id:
                # Показываем текущие настройки
                masked_token = self.config.get_masked_token(token)
                self.ui.show_config_info(masked_token, org_id)
                
                # Спрашиваем, что делать
                choice = self.ui.show_config_menu()
                
                if choice == "1":
                    # Продолжаем с текущими настройками
                    self.api_client = YandexAPIClient(token)
                    return True
                elif choice == "2":
                    # Изменяем настройки
                    return self.configure_new()
                else:
                    # Выход
                    return False
        
        # Первоначальная настройка
        return self.configure_new()

    def configure_new(self) -> bool:
        """
        Настройка новой конфигурации.

        Returns:
            True если конфигурация успешно создана
        """
        while True:
            # Запрашиваем токен
            token = self.ui.prompt_token()
            
            if not token:
                self.ui.show_error("Токен не может быть пустым")
                continue

            # Проверяем токен через whoami
            try:
                temp_client = YandexAPIClient(token)
                whoami_data = temp_client.whoami()
                
                login = whoami_data.get("login", "неизвестно")
                org_ids = whoami_data.get("orgIds", [])
                scopes = whoami_data.get("scopes", [])
                
                # Показываем информацию о токене
                self.ui.show_token_validation(login, org_ids)
                
                # Проверяем scope
                is_valid, missing_scopes = temp_client.validate_scopes(scopes)
                self.ui.show_scope_validation(is_valid, missing_scopes)
                
                if not is_valid:
                    self.ui.show_warning("Токен не имеет необходимых прав доступа")
                    continue

                # Запрашиваем org_id
                org_id = self.ui.prompt_org_id(org_ids if org_ids else None)
                
                if not org_id:
                    self.ui.show_error("Organization ID не может быть пустым")
                    continue

                # Проверяем, что org_id является числом
                try:
                    org_id_int = int(org_id)
                except ValueError:
                    self.ui.show_error("Organization ID должен быть числом")
                    continue

                # Если org_ids известны, проверяем что выбранный org_id в списке
                if org_ids and org_id_int not in org_ids:
                    self.ui.show_warning(
                        f"Organization ID {org_id_int} не найден в списке доступных организаций.\n"
                        "Всё равно сохранить?"
                    )
                    if not self.ui.ask_continue():
                        continue

                # Сохраняем конфигурацию
                self.config.save(token, org_id)
                self.ui.show_config_saved()
                
                # Создаём API клиент
                self.api_client = YandexAPIClient(token)
                temp_client.close()
                
                return True

            except YandexAPIError as e:
                self.ui.show_error(f"Ошибка проверки токена: {e}")
                self.ui.show_warning("Попробуйте ввести токен ещё раз")
                continue
            except Exception as e:
                self.ui.show_error(f"Непредвиденная ошибка: {e}")
                return False

    def main_loop(self):
        """Основной цикл работы приложения."""
        # Показываем инструкции
        self.ui.show_main_instructions()

        while True:
            # Запрашиваем URL
            url = self.ui.prompt_url()
            
            if url is None:
                # Пользователь хочет выйти
                break

            if not url:
                self.ui.show_error("URL не может быть пустым")
                continue

            # Обрабатываем URL
            self.process_url(url)

            # Спрашиваем, продолжить ли
            if not self.ui.ask_continue():
                break

        self.ui.show_goodbye()

    def process_url(self, url: str):
        """
        Обрабатывает URL и показывает информацию о владельце.

        Args:
            url: URL для обработки
        """
        try:
            # Нормализуем URL
            self.ui.show_processing("Проверка URL")
            normalized_url = normalize_url(url)
            self.ui.clear_processing()

            # Получаем владельца ресурса
            self.ui.show_processing("Получение информации о ресурсе")
            owner_uid, resource_org_id = self.api_client.get_resource_owner(normalized_url)
            self.ui.clear_processing()

            # Получаем org_id из конфигурации
            _, config_org_id = self.config.load()
            
            # Используем org_id из ресурса (он более точный)
            org_id_to_use = resource_org_id

            # Получаем информацию о пользователе
            self.ui.show_processing("Получение данных пользователя")
            user_data = self.api_client.get_user_info(org_id_to_use, owner_uid)
            self.ui.clear_processing()

            # Показываем результат
            self.ui.show_user_info(user_data)

        except URLParseError as e:
            self.ui.clear_processing()
            self.ui.show_error(f"Некорректный URL: {e}")
        except YandexAPIError as e:
            self.ui.clear_processing()
            self.ui.show_error(str(e))
        except Exception as e:
            self.ui.clear_processing()
            self.ui.show_error(f"Непредвиденная ошибка: {e}")


def main():
    """Entry point приложения."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
