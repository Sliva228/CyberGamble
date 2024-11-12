from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict

class KeyboardManager:
    def __init__(self):
        self.layouts = {
            'vertical': self._create_vertical_layout,
            'horizontal': self._create_horizontal_layout
        }

    def get_keyboard(self, keyboard_type: str, layout_type: str = 'vertical', **kwargs) -> InlineKeyboardMarkup:
        keyboard_method = getattr(self, f'get_{keyboard_type}_keyboard', None)
        if not keyboard_method:
            raise ValueError(f"Unknown keyboard type: {keyboard_type}")
            
        return keyboard_method(layout_type, **kwargs)

    def _create_vertical_layout(self, buttons: List[Dict]) -> List[List[InlineKeyboardButton]]:
        return [[InlineKeyboardButton(**button)] for button in buttons]

    def _create_horizontal_layout(self, buttons: List[Dict]) -> List[List[InlineKeyboardButton]]:
        return [
            [InlineKeyboardButton(**button) for button in buttons[i:i+3]]
            for i in range(0, len(buttons), 3)
        ]

    def get_main_keyboard(self, layout_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': ['👤 Профиль', '🎮 Игры', '⚙️ Настройки', '🏆 Рейтинг'],
            'en': ['👤 Profile', '🎮 Games', '⚙️ Settings', '🏆 Rating']
        }
        
        buttons = [
            {'text': text, 'callback_data': data}
            for text, data in zip(texts[lang], ['profile', 'games', 'settings', 'rating'])
        ]
        
        return InlineKeyboardMarkup(
            inline_keyboard=self.layouts[layout_type](buttons)
        )

    def get_settings_keyboard(self, layout_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': ['📱 Расположение кнопок', '🌍 Язык', '🔙 Назад'],
            'en': ['📱 Button Layout', '🌍 Language', '🔙 Back']
        }
        
        buttons = [
            {'text': texts[lang][0], 'callback_data': 'layout_settings'},
            {'text': texts[lang][1], 'callback_data': 'language_settings'},
            {'text': texts[lang][2], 'callback_data': 'main_menu'}
        ]
        
        return InlineKeyboardMarkup(
            inline_keyboard=self.layouts[layout_type](buttons)
        )

    def get_layout_keyboard(self, current_layout: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': {
                'vertical': '📊 Вертикальное [✓]',
                'not_vertical': '📊 Вертикальное',
                'horizontal': '📈 Горизонтальное [✓]',
                'not_horizontal': '📈 Горизонтальное',
                'back': '🔙 Назад'
            },
            'en': {
                'vertical': '📊 Vertical [✓]',
                'not_vertical': '📊 Vertical',
                'horizontal': '📈 Horizontal [✓]',
                'not_horizontal': '📈 Horizontal',
                'back': '🔙 Back'
            }
        }
        
        buttons = [
            [InlineKeyboardButton(
                text=texts[lang]['vertical' if current_layout == 'vertical' else 'not_vertical'],
                callback_data='set_layout_vertical'
            )],
            [InlineKeyboardButton(
                text=texts[lang]['horizontal' if current_layout == 'horizontal' else 'not_horizontal'],
                callback_data='set_layout_horizontal'
            )],
            [InlineKeyboardButton(text=texts[lang]['back'], callback_data='settings')]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def get_language_keyboard(self, current_lang: str) -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(
                text=f"🇷🇺 Русский {'[✓]' if current_lang == 'ru' else ''}",
                callback_data='set_lang_ru'
            )],
            [InlineKeyboardButton(
                text=f"🇬🇧 English {'[✓]' if current_lang == 'en' else ''}",
                callback_data='set_lang_en'
            )],
            [InlineKeyboardButton(text='🔙 Назад/Back', callback_data='settings')]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def get_games_keyboard(self, layout_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': ['🎲 21 (Блэкджек)', '🔙 Назад'],
            'en': ['🎲 21 (Blackjack)', '🔙 Back']
        }
        
        buttons = [
            {'text': texts[lang][0], 'callback_data': 'blackjack'},
            {'text': texts[lang][1], 'callback_data': 'main_menu'}
        ]
        
        return InlineKeyboardMarkup(
            inline_keyboard=self.layouts[layout_type](buttons)
        )

    def get_bet_keyboard(self, layout_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': {
                'bets': ['💰 100', '💰 250', '💰 500', '💰 1000'],
                'back': '🔙 Назад'
            },
            'en': {
                'bets': ['💰 100', '💰 250', '💰 500', '💰 1000'],
                'back': '🔙 Back'
            }
        }
        
        buttons = [
            {'text': bet, 'callback_data': f'bet_{bet.split()[1]}'}
            for bet in texts[lang]['bets']
        ]
        buttons.append({'text': texts[lang]['back'], 'callback_data': 'games'})
        
        return InlineKeyboardMarkup(
            inline_keyboard=self.layouts[layout_type](buttons)
        )

    def get_blackjack_keyboard(self, layout_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': ['🎯 Взять карту', '✋ Хватит', '🔙 Выйти'],
            'en': ['🎯 Hit', '✋ Stand', '🔙 Exit']
        }
        
        buttons = [
            {'text': texts[lang][0], 'callback_data': 'blackjack_hit'},
            {'text': texts[lang][1], 'callback_data': 'blackjack_stand'},
            {'text': texts[lang][2], 'callback_data': 'games'}
        ]
        
        return InlineKeyboardMarkup(
            inline_keyboard=self.layouts[layout_type](buttons)
        )