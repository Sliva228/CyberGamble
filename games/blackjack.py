import random
from typing import List, Tuple

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank}{self.suit}"

class Blackjack:
    def __init__(self):
        self.suits = ['♠️', '♥️', '♣️', '♦️']
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.deck = [Card(suit, rank) for suit in self.suits for rank in self.ranks]
        self.reset_game()

    def reset_game(self):
        random.shuffle(self.deck)
        self.player_hands: dict[int, List[Card]] = {}
        self.dealer_hand: List[Card] = []
        self.game_state: dict[int, str] = {}
        self.bets: dict[int, int] = {}

    def start_game(self, user_id: int, bet: int) -> Tuple[List[str], List[str], bool, int]:
        self.player_hands[user_id] = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.game_state[user_id] = 'playing'
        self.bets[user_id] = bet
        
        player_value = self.calculate_hand(self.player_hands[user_id])
        is_blackjack = player_value == 21
        win_amount = bet * 3 if is_blackjack else 0
        
        return (
            [str(card) for card in self.player_hands[user_id]],
            [str(self.dealer_hand[0]), '🂠'],
            is_blackjack,
            win_amount
        )

    def calculate_hand(self, hand: List[Card]) -> int:
        value = 0
        aces = 0
        
        for card in hand:
            if card.rank in ['J', 'Q', 'K']:
                value += 10
            elif card.rank == 'A':
                aces += 1
            else:
                value += int(card.rank)
        
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
                
        return value

    def hit(self, user_id: int) -> Tuple[List[str], int, bool]:
        self.player_hands[user_id].append(self.deck.pop())
        hand_value = self.calculate_hand(self.player_hands[user_id])
        
        if hand_value > 21:
            self.game_state[user_id] = 'bust'
            return (
                [str(card) for card in self.player_hands[user_id]],
                hand_value,
                True
            )
            
        return (
            [str(card) for card in self.player_hands[user_id]],
            hand_value,
            False
        )

    def stand(self, user_id: int) -> Tuple[List[str], List[str], int, int, int]:
        player_value = self.calculate_hand(self.player_hands[user_id])
        
        while self.calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
            
        dealer_value = self.calculate_hand(self.dealer_hand)
        
        if dealer_value > 21 or player_value > dealer_value:
            self.game_state[user_id] = 'win'
            win_amount = self.bets[user_id] * 2
        elif dealer_value > player_value:
            self.game_state[user_id] = 'lose'
            win_amount = 0
        else:
            self.game_state[user_id] = 'draw'
            win_amount = self.bets[user_id]
            
        return (
            [str(card) for card in self.player_hands[user_id]],
            [str(card) for card in self.dealer_hand],
            player_value,
            dealer_value,
            win_amount
        )