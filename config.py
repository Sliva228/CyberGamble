from dataclasses import dataclass
from typing import Dict

@dataclass
class Config:
    MAX_USERNAME_LENGTH: int = 32
    MIN_USERNAME_LENGTH: int = 3
    DEFAULT_LANGUAGE: str = 'ru'
    AVAILABLE_LANGUAGES: Dict[str, str] = None
    MAX_DAILY_GAMES: int = 100
    ADMIN_IDS: list = None
    
    def __post_init__(self):
        self.AVAILABLE_LANGUAGES = {
            'ru': 'Русский',
            'en': 'English'
        }
        self.ADMIN_IDS = [
            123456789  # Замените на реальные ID администраторов
        ]