from dataclasses import dataclass
from enum import Enum
import random
from typing import List, Tuple, Dict

class BetType(Enum):
    NUMBER = 'number'
    COLOR = 'color'
    PARITY = 'parity'
    DOZEN = 'dozen'
    HALF = 'half'

@dataclass
class Bet:
    type: BetType
    value: str
    amount: int

class RouletteNumber:
    def __init__(self, number: int):
        self.number = number
        self.color = 'red' if number in [
            1, 3, 5, 7, 9, 12, 14, 16, 18, 19,
            21, 23, 25, 27, 30, 32, 34, 36
        ] else 'black' if number > 0 else 'green'
        self.parity = 'even' if number > 0 and number % 2 == 0 else 'odd'
        self.dozen = 1 if number <= 12 else 2 if number <= 24 else 3
        self.half = 1 if number <= 18 else 2

    def __str__(self) -> str:
        color_emoji = '🔴' if self.color == 'red' else '⚫️' if self.color == 'black' else '🟢'
        return f"{color_emoji} {self.number}"

class Roulette:
    def __init__(self):
        self.numbers = [RouletteNumber(i) for i in range(37)]
        self.multipliers = {
            BetType.NUMBER: 35,
            BetType.COLOR: 2,
            BetType.PARITY: 2,
            BetType.DOZEN: 3,
            BetType.HALF: 2
        }
        self.active_games: Dict[int, List[Bet]] = {}

    def place_bet(self, user_id: int, bet_type: BetType, value: str, amount: int) -> bool:
        if user_id not in self.active_games:
            self.active_games[user_id] = []
            
        bet = Bet(bet_type, value, amount)
        self.active_games[user_id].append(bet)
        return True

    def spin(self, user_id: int) -> Tuple[RouletteNumber, int]:
        if user_id not in self.active_games:
            return None, 0
            
        result = random.choice(self.numbers)
        total_win = 0
        
        for bet in self.active_games[user_id]:
            win = self._check_win(bet, result)
            if win:
                total_win += bet.amount * self.multipliers[bet.type]
                
        del self.active_games[user_id]
        return result, total_win

    def _check_win(self, bet: Bet, result: RouletteNumber) -> bool:
        if bet.type == BetType.NUMBER:
            return int(bet.value) == result.number
        elif bet.type == BetType.COLOR:
            return bet.value == result.color
        elif bet.type == BetType.PARITY:
            return bet.value == result.parity
        elif bet.type == BetType.DOZEN:
            return int(bet.value) == result.dozen
        elif bet.type == BetType.HALF:
            return int(bet.value) == result.half
        return False

    def get_active_bets(self, user_id: int) -> List[Bet]:
        return self.active_games.get(user_id, [])