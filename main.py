import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.command import Command
from database import Database
from games.blackjack import Blackjack
from games.roulette import Roulette, BetType
from games.slots import SlotMachine
from keyboards import KeyboardManager
from config import Config
import importlib

logging.basicConfig(level=logging.INFO)

config = Config()
bot = Bot(token="TOKEN")
dp = Dispatcher()
db = Database()
kb = KeyboardManager()
blackjack_games = {}
roulette_games = {}
slot_machines = {}

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
    locale = get_locale(message.from_user.id)
    
    if len(args) < 2:
        await message.answer(
            locale['registration_required'],
            reply_markup=None
        )
        return

    username = args[1]
    
    if db.is_registered(message.from_user.id):
        await message.answer(
            locale['already_registered'],
            reply_markup=None
        )
        return

    if db.register_user(message.from_user.id, username):
        await message.answer(
            locale['registration_success'],
            reply_markup=kb.get_main_keyboard('vertical', 'ru')
        )
        
        # Send welcome message after successful registration
        await message.answer(
            locale['welcome'],
            reply_markup=kb.get_main_keyboard('vertical', 'ru')
        )
    else:
        await message.answer(
            locale['invalid_username'],
            reply_markup=None
        )

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
        # Profile button
        if callback.data == 'profile':
            await callback.message.edit_text(
                locale['profile'].format(
                    user['balance'],
                    user['games_played'],
                    user['wins'],
                    user['rating']
                ),
                reply_markup=kb.get_main_keyboard(user['layout_type'], user['language'])
            )

        # Games menu
        elif callback.data == 'games':
            await callback.message.edit_text(
                "🎮 Выберите игру:",
                reply_markup=kb.get_games_keyboard(user['layout_type'], user['language'])
            )

        # Settings menu
        elif callback.data == 'settings':
            await callback.message.edit_text(
                locale['settings'],
                reply_markup=kb.get_settings_keyboard(user['layout_type'], user['language'])
            )

        # Layout settings
        elif callback.data == 'layout_settings':
            await callback.message.edit_text(
                locale['layout'],
                reply_markup=kb.get_layout_keyboard(user['layout_type'], user['language'])
            )

        # Change layout
        elif callback.data.startswith('set_layout_'):
            layout = callback.data.replace('set_layout_', '')
            db.update_settings(user_id, layout_type=layout)
            await callback.message.edit_text(
                locale['layout'],
                reply_markup=kb.get_layout_keyboard(layout, user['language'])
            )

        # Language settings
        elif callback.data == 'language_settings':
            await callback.message.edit_text(
                locale['language'],
                reply_markup=kb.get_language_keyboard(user['language'])
            )

        # Change language
        elif callback.data.startswith('set_lang_'):
            lang = callback.data.replace('set_lang_', '')
            db.update_settings(user_id, language=lang)
            locale = get_locale(user_id)
            await callback.message.edit_text(
                locale['settings'],
                reply_markup=kb.get_settings_keyboard(user['layout_type'], lang)
            )

        # Rating
        elif callback.data == 'rating':
            top_players = db.get_top_players(10)
            top_text = "\n".join(
                f"{i+1}. {player['username']} - {player['rating']} 🏆"
                for i, player in enumerate(top_players)
            )
            await callback.message.edit_text(
                locale['top_players'].format(top_text),
                reply_markup=kb.get_main_keyboard(user['layout_type'], user['language'])
            )

        # Rules
        elif callback.data == 'rules':
            await callback.message.edit_text(
                locale['rules'],
                reply_markup=kb.get_main_keyboard(user['layout_type'], user['language'])
            )

        # Main menu
        elif callback.data == 'main_menu':
            await callback.message.edit_text(
                locale['welcome'],
                reply_markup=kb.get_main_keyboard(user['layout_type'], user['language'])
            )

        # Slots game
        elif callback.data == 'slots':
            if not db.check_daily_limit(user_id):
                await callback.answer(locale['daily_limit_reached'], show_alert=True)
                return

            if user_id not in slot_machines:
                slot_machines[user_id] = SlotMachine()

            await callback.message.edit_text(
                locale['slots_welcome'],
                reply_markup=kb.get_slots_keyboard(user['layout_type'], user['language'])
            )

        # Slots bet
        elif callback.data.startswith('slots_bet_'):
            bet = int(callback.data.replace('slots_bet_', ''))
            
            if user['balance'] < bet:
                await callback.answer(locale['insufficient_balance'], show_alert=True)
                return
                
            game = slot_machines[user_id]
            db.update_balance(user_id, -bet)
            
            # Animate spinning
            msg = await callback.message.edit_text(
                locale['slots_spinning'].format('🎰 | 🎰 | 🎰')
            )
            
            for frame in game.get_animation_frames():
                await asyncio.sleep(0.5)
                await msg.edit_text(locale['slots_spinning'].format(frame))
            
            # Final result
            result, win_amount = game.spin(bet)
            result_display = ' '.join(s.emoji for s in result)
            
            if win_amount > 0:
                db.update_balance(user_id, win_amount)
                db.update_stats(user_id, 'win')
                await msg.edit_text(
                    locale['slots_win'].format(result_display, win_amount),
                    reply_markup=kb.get_slots_keyboard(user['layout_type'], user['language'])
                )
            else:
                db.update_stats(user_id, 'lose')
                await msg.edit_text(
                    locale['slots_lose'].format(result_display),
                    reply_markup=kb.get_slots_keyboard(user['layout_type'], user['language'])
                )

        # Roulette game
        elif callback.data == 'roulette':
            if not db.check_daily_limit(user_id):
                await callback.answer(locale['daily_limit_reached'], show_alert=True)
                return

            if user_id not in roulette_games:
                roulette_games[user_id] = Roulette()

            await callback.message.edit_text(
                locale['roulette_welcome'],
                reply_markup=kb.get_roulette_keyboard(user['layout_type'], user['language'])
            )

        # Roulette bets
        elif callback.data.startswith('roulette_'):
            if user_id not in roulette_games:
                roulette_games[user_id] = Roulette()

            game = roulette_games[user_id]
            action = callback.data.replace('roulette_', '')

            if action == 'spin':
                if not game.get_active_bets(user_id):
                    await callback.answer(locale['no_bets'], show_alert=True)
                    return

                result, win_amount = game.spin(user_id)
                if win_amount > 0:
                    db.update_balance(user_id, win_amount)
                    db.update_stats(user_id, 'win')
                    await callback.message.edit_text(
                        locale['roulette_win'].format(str(result), win_amount),
                        reply_markup=kb.get_roulette_keyboard(user['layout_type'], user['language'])
                    )
                else:
                    db.update_stats(user_id, 'lose')
                    await callback.message.edit_text(
                        locale['roulette_lose'].format(str(result)),
                        reply_markup=kb.get_roulette_keyboard(user['layout_type'], user['language'])
                    )
            else:
                bet_parts = action.split('_')
                if len(bet_parts) == 2:
                    bet_type, value = bet_parts
                    if game.place_bet(user_id, BetType[bet_type.upper()], value, 10):
                        await callback.answer(locale['bet_placed'])

        # Blackjack game
        elif callback.data == 'blackjack':
            if not db.check_daily_limit(user_id):
                await callback.answer(locale['daily_limit_reached'], show_alert=True)
                return

            await callback.message.edit_text(
                locale['select_bet'],
                reply_markup=kb.get_bet_keyboard(user['layout_type'], user['language'])
            )

        # Blackjack bet
        elif callback.data.startswith('bet_'):
            bet = int(callback.data.replace('bet_', ''))
            
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

        # Blackjack actions
        elif callback.data.startswith('blackjack_'):
            game = blackjack_games.get(user_id)
            if not game:
                await callback.answer(locale['game_not_found'], show_alert=True)
                return

            action = callback.data.replace('blackjack_', '')
            
            if action == 'hit':
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
                    
            elif action == 'stand':
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
