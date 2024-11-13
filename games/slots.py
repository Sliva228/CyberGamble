from dataclasses import dataclass
import random
from typing import List, Tuple

@dataclass
class Symbol:
    emoji: str
    name: str
    multiplier: int

class SlotMachine:
    def __init__(self):
        self.symbols = [
            Symbol('7️⃣', 'seven', 10),
            Symbol('🍒', 'cherry', 5),
            Symbol('🍋', 'lemon', 4),
            Symbol('🍊', 'orange', 3),
            Symbol('🫐', 'berry', 2),
            Symbol('🍎', 'apple', 2)
        ]
        self.reels = 3
        
    def spin(self, bet: int) -> Tuple[List[Symbol], int]:
        result = [random.choice(self.symbols) for _ in range(self.reels)]
        win_amount = self._calculate_win(result, bet)
        return result, win_amount
        
    def _calculate_win(self, symbols: List[Symbol], bet: int) -> int:
        if all(s.name == symbols[0].name for s in symbols):
            return bet * symbols[0].multiplier
        return 0
        
    def get_animation_frames(self) -> List[str]:
        frames = []
        symbols = [s.emoji for s in self.symbols]
        
        for _ in range(3):  # 3 animation frames
            frame = ' '.join(random.choice(symbols) for _ in range(self.reels))
            frames.append(frame)
            
        return frames