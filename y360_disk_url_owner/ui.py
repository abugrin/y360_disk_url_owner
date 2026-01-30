"""
Модуль для работы с пользовательским интерфейсом.
Использует библиотеку Rich для создания красивого TUI.
"""

import sys
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text


class UI:
    """Класс для управления пользовательским интерфейсом."""

    def __init__(self):
        """Инициализация UI."""
        self.console = Console()

    def clear_screen(self):
        """Очищает экран."""
        self.console.clear()

    def show_welcome(self):
        """Показывает приветственное сообщение."""
        self.console.print()
        welcome_text = Text()
        welcome_text.append("Добро пожаловать в ", style="bold cyan")
        welcome_text.append("Y360 Disk URL Owner", style="bold yellow")
        welcome_text.append("!", style="bold cyan")
        
        panel = Panel(
            welcome_text,
            title="🔍 Поиск владельца файла на Яндекс Диске",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()

    def show_config_info(self, masked_token: str, org_id: str):
        """
        Показывает информацию о текущей конфигурации.

        Args:
            masked_token: Замаскированный токен
            org_id: ID организации
        """
        self.console.print()
        self.console.print("[bold]Текущие настройки:[/bold]")
        self.console.print(f"  [cyan]Token:[/cyan] {masked_token}")
        self.console.print(f"  [cyan]Organization ID:[/cyan] {org_id}")
        self.console.print()

    def show_config_menu(self) -> str:
        """
        Показывает меню выбора действия с конфигурацией.

        Returns:
            Выбранное действие: "1", "2", или "3"
        """
        self.console.print("[bold]Выберите действие:[/bold]")
        self.console.print("  [1] Продолжить с текущими настройками")
        self.console.print("  [2] Изменить настройки")
        self.console.print("  [3] Выход")
        self.console.print()

        while True:
            choice = Prompt.ask("Ваш выбор", choices=["1", "2", "3"], default="1")
            return choice

    def prompt_token(self) -> str:
        """
        Запрашивает у пользователя токен.

        Returns:
            Введённый токен
        """
        self.console.print()
        self.console.print("[yellow]Введите OAuth токен для доступа к Яндекс 360 API[/yellow]")
        self.console.print()
        
        token = Prompt.ask("Token")
        return token.strip()

    def prompt_org_id(self) -> str:
        """
        Запрашивает у пользователя ID организации.

        Returns:
            Введённый org_id
        """
        self.console.print()
        self.console.print("[yellow]Введите ID организации (org_id)[/yellow]")
        org_id = Prompt.ask("Organization ID")
        return org_id.strip()

    def show_token_info(self, login: str):
        """
        Показывает информацию о токене.
        Теперь ничего не отображает при успешной проверке.

        Args:
            login: Логин пользователя (не используется)
        """
        # Не отображаем ничего при успешной проверке
        pass

    def show_scope_validation(self, is_valid: bool, missing_scopes: list):
        """
        Показывает результат проверки scope.
        Отображает сообщение только при ошибке.

        Args:
            is_valid: True если все scope присутствуют
            missing_scopes: Список недостающих scope
        """
        if not is_valid:
            self.console.print()
            self.console.print("[bold red]✗ Недостаточно прав доступа![/bold red]")
            self.console.print("[yellow]Отсутствуют следующие scope:[/yellow]")
            for scope in missing_scopes:
                self.console.print(f"  • {scope}")
            self.console.print()
            self.console.print("[dim]Пожалуйста, получите токен с необходимыми правами[/dim]")
            self.console.print()

    def show_config_saved(self):
        """Показывает сообщение об успешном сохранении конфигурации."""
        self.console.print("[green]✓[/green] Настройки сохранены")
        self.console.print()

    def show_main_instructions(self):
        """Показывает инструкции для основной работы."""
        self.console.print()
        instructions = (
            "[bold cyan]Вставьте ссылку на файл в Яндекс Диске[/bold cyan]\n\n"
            "Поддерживаемые форматы:\n"
            "  • Короткая: https://disk.yandex.ru/d/...\n"
            "  • Полная: https://disk.yandex.ru/public/?hash=...\n"
            "  • Хеш: dAEMkc1Q...\n\n"
            "[dim]Для вставки используйте Ctrl+V (Cmd+V на macOS)\n"
            "Для выхода введите 'q' или 'quit'[/dim]"
        )
        panel = Panel(instructions, border_style="blue", padding=(1, 2))
        self.console.print(panel)
        self.console.print()

    def prompt_url(self) -> Optional[str]:
        """
        Запрашивает у пользователя URL.

        Returns:
            Введённый URL или None если пользователь хочет выйти
        """
        url = Prompt.ask("[bold]URL")
        url = url.strip()
        
        if url.lower() in ['q', 'quit', 'exit']:
            return None
        
        return url

    def show_processing(self, message: str = "Обработка"):
        """
        Показывает сообщение о процессе обработки.

        Args:
            message: Сообщение для отображения
        """
        self.console.print(f"[yellow]⟳[/yellow] {message}...")

    def clear_processing(self):
        """Очищает сообщение о процессе обработки."""
        # Ничего не делаем, сообщение остается на своей строке
        pass

    def show_user_info(self, user_data: Dict):
        """
        Показывает информацию о пользователе в виде таблицы.

        Args:
            user_data: Словарь с данными пользователя из API
        """
        self.console.print()

        # Создаём таблицу
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Поле", style="cyan", no_wrap=True)
        table.add_column("Значение", style="white")

        # Добавляем данные
        table.add_row("UID", str(user_data.get("id", "—")))
        table.add_row("Логин", user_data.get("nickname", "—"))
        table.add_row("Email", user_data.get("email", "—"))
        
        # ФИО
        name_data = user_data.get("name", {})
        first_name = name_data.get("first", "")
        last_name = name_data.get("last", "")
        
        if first_name:
            table.add_row("Имя", first_name)
        if last_name:
            table.add_row("Фамилия", last_name)

        # Выводим таблицу в панели
        panel = Panel(table, border_style="green", padding=(1, 2))
        self.console.print(panel)
        self.console.print()

    def show_error(self, error_message: str):
        """
        Показывает сообщение об ошибке.

        Args:
            error_message: Текст ошибки
        """
        self.console.print()
        self.console.print(f"[bold red]✗ Ошибка:[/bold red] {error_message}")
        self.console.print()

    def show_warning(self, warning_message: str):
        """
        Показывает предупреждение.

        Args:
            warning_message: Текст предупреждения
        """
        self.console.print()
        self.console.print(f"[yellow]⚠[/yellow]  {warning_message}")
        self.console.print()

    def show_info(self, info_message: str):
        """
        Показывает информационное сообщение.

        Args:
            info_message: Текст сообщения
        """
        self.console.print()
        self.console.print(f"[blue]ℹ[/blue]  {info_message}")
        self.console.print()


    def show_goodbye(self):
        """Показывает прощальное сообщение."""
        self.console.print()
        self.console.print("[cyan]До свидания! 👋[/cyan]")
        self.console.print()

    def pause(self):
        """Пауза с ожиданием нажатия Enter."""
        self.console.print()
        Prompt.ask("[dim]Нажмите Enter для продолжения[/dim]", default="")
