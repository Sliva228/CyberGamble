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
            'ru': ['👤 Профиль', '🎮 Игры', '⚙️ Настройки', '🏆 Рейтинг', '📜 Правила'],
            'en': ['👤 Profile', '🎮 Games', '⚙️ Settings', '🏆 Rating', '📜 Rules']
        }
        
        buttons = [
            {'text': text, 'callback_data': data}
            for text, data in zip(texts[lang], ['profile', 'games', 'settings', 'rating', 'rules'])
        ]
        
        return InlineKeyboardMarkup(
            inline_keyboard=self.layouts[layout_type](buttons)
        )

    def get_games_keyboard(self, layout_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': ['🎲 21 (Блэкджек)', '🎰 Рулетка', '🎰 Слоты', '🔙 Назад'],
            'en': ['🎲 21 (Blackjack)', '🎰 Roulette', '🎰 Slots', '🔙 Back']
        }
        
        buttons = [
            {'text': texts[lang][0], 'callback_data': 'blackjack'},
            {'text': texts[lang][1], 'callback_data': 'roulette'},
            {'text': texts[lang][2], 'callback_data': 'slots'},
            {'text': texts[lang][3], 'callback_data': 'main_menu'}
        ]
        
        return InlineKeyboardMarkup(
            inline_keyboard=self.layouts[layout_type](buttons)
        )

    def get_slots_keyboard(self, layout_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': {
                'bets': ['💰 10', '💰 50', '💰 100'],
                'back': '🔙 Назад'
            },
            'en': {
                'bets': ['💰 10', '💰 50', '💰 100'],
                'back': '🔙 Back'
            }
        }
        
        buttons = [
            {'text': bet, 'callback_data': f'slots_bet_{bet.split()[1]}'}
            for bet in texts[lang]['bets']
        ]
        buttons.append({'text': texts[lang]['back'], 'callback_data': 'games'})
        
        return InlineKeyboardMarkup(
            inline_keyboard=self.layouts[layout_type](buttons)
        )

    def get_roulette_keyboard(self, layout_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        texts = {
            'ru': {
                'colors': ['🔴 Красное', '⚫️ Чёрное', '🟢 Зеро'],
                'parity': ['2️⃣ Чёт', '1️⃣ Нечет'],
                'dozens': ['1️⃣ 1-12', '2️⃣ 13-24', '3️⃣ 25-36'],
                'halves': ['⬇️ 1-18', '⬆️ 19-36'],
                'actions': ['🎯 Крутить', '🔙 Назад']
            },
            'en': {
                'colors': ['🔴 Red', '⚫️ Black', '🟢 Zero'],
                'parity': ['2️⃣ Even', '1️⃣ Odd'],
                'dozens': ['1️⃣ 1-12', '2️⃣ 13-24', '3️⃣ 25-36'],
                'halves': ['⬇️ 1-18', '⬆️ 19-36'],
                'actions': ['🎯 Spin', '🔙 Back']
            }
        }

        buttons = []
        
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f'roulette_color_{color}')
            for text, color in zip(texts[lang]['colors'], ['red', 'black', 'green'])
        ])
        
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f'roulette_parity_{parity}')
            for text, parity in zip(texts[lang]['parity'], ['even', 'odd'])
        ])
        
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f'roulette_dozen_{i+1}')
            for i, text in enumerate(texts[lang]['dozens'])
        ])
        
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f'roulette_half_{i+1}')
            for i, text in enumerate(texts[lang]['halves'])
        ])
        
        buttons.append([
            InlineKeyboardButton(text=texts[lang]['actions'][0], callback_data='roulette_spin'),
            InlineKeyboardButton(text=texts[lang]['actions'][1], callback_data='games')
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)