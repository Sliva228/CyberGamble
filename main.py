import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.command import Command
from database import Database
from games.blackjack import Blackjack
from keyboards import KeyboardManager
from config import Config
import importlib

logging.basicConfig(level=logging.INFO)

config = Config()
bot = Bot(token="7760745056:AAE0q8rG-VwBnkffJQXMAfCrFnu9PCQ7_qA")
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
    try:
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

        elif callback.data == "games":
            await callback.message.edit_text(
                "🎮 Выберите игру:",
                reply_markup=kb.get_games_keyboard(user['layout_type'], user['language'])
            )

        elif callback.data == "settings":
            await callback.message.edit_text(
                locale['settings'],
                reply_markup=kb.get_settings_keyboard(user['layout_type'], user['language'])
            )

        elif callback.data == "main_menu":
            await callback.message.edit_text(
                locale['welcome'],
                reply_markup=kb.get_main_keyboard(user['layout_type'], user['language'])
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

        elif callback.data == "blackjack":
            if not db.check_daily_limit(user_id):
                await callback.answer(locale['daily_limit_reached'], show_alert=True)
                return

            await callback.message.edit_text(
                locale['select_bet'],
                reply_markup=kb.get_bet_keyboard(user['layout_type'], user['language'])
            )

        elif callback.data.startswith("bet_"):
            bet = int(callback.data.replace("bet_", ""))
            
            if user['balance'] < bet:
                await callback.answer(locale['insufficient_balance'], show_alert=True)
                return

            game = Blackjack()
            blackjack_games[user_id] = game
            player_cards, dealer_cards, is_blackjack, win_amount = game.start_game(user_id, bet)
            
            if is_blackjack:
                db.update_balance(user_id, win_amount)
                db.update_stats(user_id, 'win')
                await callback.message.edit_text(
                    locale['blackjack_win'].format(win_amount),
                    reply_markup=kb.get_games_keyboard(user['layout_type'], user['language'])
                )
            else:
                player_value = game.calculate_hand(game.player_hands[user_id])
                dealer_card = str(game.dealer_hand[0])
                await callback.message.edit_text(
                    locale['blackjack_game'].format(
                        ' '.join(str(card) for card in player_cards),
                        player_value,
                        f"{dealer_card} 🂠",
                        bet
                    ),
                    reply_markup=kb.get_blackjack_keyboard(user['layout_type'], user['language'])
                )

        elif callback.data == "blackjack_hit":
            game = blackjack_games.get(user_id)
            if not game:
                await callback.answer(locale['game_not_found'], show_alert=True)
                return
                
            player_cards, hand_value, is_bust = game.hit(user_id)
            
            if is_bust:
                bet = game.bets[user_id]
                db.update_balance(user_id, -bet)
                db.update_stats(user_id, 'lose')
                await callback.message.edit_text(
                    locale['blackjack_bust'].format(bet),
                    reply_markup=kb.get_games_keyboard(user['layout_type'], user['language'])
                )
                del blackjack_games[user_id]
            else:
                dealer_card = str(game.dealer_hand[0])
                await callback.message.edit_text(
                    locale['blackjack_game'].format(
                        ' '.join(str(card) for card in player_cards),
                        hand_value,
                        f"{dealer_card} 🂠",
                        game.bets[user_id]
                    ),
                    reply_markup=kb.get_blackjack_keyboard(user['layout_type'], user['language'])
                )

        elif callback.data == "blackjack_stand":
            game = blackjack_games.get(user_id)
            if not game:
                await callback.answer(locale['game_not_found'], show_alert=True)
                return
                
            player_cards, dealer_cards, player_value, dealer_value, win_amount = game.stand(user_id)
            
            result_text = locale['blackjack_result'].format(
                ' '.join(str(card) for card in player_cards),
                player_value,
                ' '.join(str(card) for card in dealer_cards),
                dealer_value
            )

            if win_amount > game.bets[user_id]:
                db.update_balance(user_id, win_amount)
                db.update_stats(user_id, 'win')
                result_text += '\n' + locale['blackjack_win'].format(win_amount)
            elif win_amount == game.bets[user_id]:
                db.update_balance(user_id, win_amount)
                result_text += '\n' + locale['blackjack_draw']
            else:
                db.update_balance(user_id, -game.bets[user_id])
                db.update_stats(user_id, 'lose')
                result_text += '\n' + locale['blackjack_lose'].format(game.bets[user_id])
            
            await callback.message.edit_text(
                result_text,
                reply_markup=kb.get_games_keyboard(user['layout_type'], user['language'])
            )
            del blackjack_games[user_id]

    except Exception as e:
        if isinstance(e, TelegramBadRequest) and "message is not modified" in str(e):
            pass
        else:
            logging.error(f"Error in callback handler: {e}")
            await callback.answer(locale['error_occurred'], show_alert=True)

    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())