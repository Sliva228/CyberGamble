import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from database import Database
from games.blackjack import Blackjack
from keyboards import KeyboardManager
from config import Config
import importlib

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация компонентов
config = Config()
bot = Bot(token="TOKEN")
dp = Dispatcher()
db = Database()
kb = KeyboardManager()
blackjack_games = {}

def get_locale(user_id: int):
    user = db.get_user(user_id)
    if not user:
        return importlib.import_module('locales.ru').messages
    return importlib.import_module(f'locales.{user["language"]}').messages

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user:
        locale = get_locale(message.from_user.id)
        await message.answer(
            locale['registration_required'],
            reply_markup=None
        )
        return

    locale = get_locale(message.from_user.id)
    await message.answer(
        locale['welcome'],
        reply_markup=kb.get_main_keyboard(user['layout_type'], user['language'])
    )

@dp.message(Command("register"))
async def cmd_register(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        locale = get_locale(message.from_user.id)
        await message.answer(locale['registration_required'])
        return

    username = args[1]
    locale = get_locale(message.from_user.id)
    
    if db.is_registered(message.from_user.id):
        await message.answer(locale['already_registered'])
        return

    if db.register_user(message.from_user.id, username):
        await message.answer(locale['registration_success'])
    else:
        await message.answer(locale['invalid_username'])

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    locale = get_locale(message.from_user.id)
    top_players = db.get_top_players(10)
    
    top_text = "\n".join(
        f"{i+1}. {player['username']} - {player['rating']} 🏆"
        for i, player in enumerate(top_players)
    )
    
    await message.answer(locale['top_players'].format(top_text))

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        locale = get_locale(user_id)
        await callback.answer(locale['registration_required'], show_alert=True)
        return

    if db.is_banned(user_id):
        await callback.answer("🚫 Вы заблокированы", show_alert=True)
        return

    locale = get_locale(user_id)

    if callback.data == "profile":
        await callback.message.edit_text(
            locale['profile'].format(
                user['balance'],
                user['games_played'],
                user['wins'],
                user['rating']
            ),
            reply_markup=kb.get_main_keyboard(user['layout_type'], user['language'])
        )

    elif callback.data == "settings":
        await callback.message.edit_text(
            locale['settings'],
            reply_markup=kb.get_settings_keyboard(user['layout_type'], user['language'])
        )

    elif callback.data == "layout_settings":
        await callback.message.edit_text(
            locale['layout'],
            reply_markup=kb.get_layout_keyboard(user['layout_type'], user['language'])
        )

    elif callback.data.startswith("set_layout_"):
        layout = callback.data.replace("set_layout_", "")
        db.update_settings(user_id, layout_type=layout)
        await callback.message.edit_text(
            locale['layout'],
            reply_markup=kb.get_layout_keyboard(layout, user['language'])
        )

    elif callback.data == "language_settings":
        await callback.message.edit_text(
            locale['language'],
            reply_markup=kb.get_language_keyboard(user['language'])
        )

    elif callback.data.startswith("set_lang_"):
        lang = callback.data.replace("set_lang_", "")
        db.update_settings(user_id, language=lang)
        locale = get_locale(user_id)
        await callback.message.edit_text(
            locale['settings'],
            reply_markup=kb.get_settings_keyboard(user['layout_type'], lang)
        )

    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())