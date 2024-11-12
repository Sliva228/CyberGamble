import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import re

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('casino.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            balance INTEGER DEFAULT 1000,
            games_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            last_game TIMESTAMP,
            rating INTEGER DEFAULT 1000,
            layout_type TEXT DEFAULT 'vertical',
            language TEXT DEFAULT 'ru',
            is_banned INTEGER DEFAULT 0,
            registration_date TIMESTAMP,
            games_today INTEGER DEFAULT 0,
            last_daily_reset TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_type TEXT,
            bet_amount INTEGER,
            win_amount INTEGER,
            timestamp TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS moderation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moderator_id INTEGER,
            user_id INTEGER,
            action TEXT,
            reason TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        self.conn.commit()

    def register_user(self, user_id: int, username: str) -> bool:
        if not self.is_valid_username(username):
            return False
            
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO users (user_id, username, registration_date)
            VALUES (?, ?, ?)
            ''', (user_id, username, datetime.now()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def is_valid_username(self, username: str) -> bool:
        if not 3 <= len(username) <= 32:
            return False
        return bool(re.match('^[a-zA-Z0-9]+$', username))

    def is_registered(self, user_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

    def is_banned(self, user_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result and result[0] == 1

    def get_user(self, user_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            return None
            
        return {
            'user_id': user[0],
            'username': user[1],
            'balance': user[2],
            'games_played': user[3],
            'wins': user[4],
            'last_game': user[5],
            'rating': user[6],
            'layout_type': user[7],
            'language': user[8],
            'is_banned': user[9],
            'registration_date': user[10],
            'games_today': user[11],
            'last_daily_reset': user[12]
        }

    def get_top_players(self, limit: int = 10) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT username, rating, wins, games_played
        FROM users
        WHERE is_banned = 0
        ORDER BY rating DESC
        LIMIT ?
        ''', (limit,))
        
        return [
            {
                'username': row[0],
                'rating': row[1],
                'wins': row[2],
                'games_played': row[3]
            }
            for row in cursor.fetchall()
        ]

    def update_settings(self, user_id: int, layout_type: Optional[str] = None, language: Optional[str] = None):
        cursor = self.conn.cursor()
        if layout_type:
            cursor.execute('UPDATE users SET layout_type = ? WHERE user_id = ?', (layout_type, user_id))
        if language:
            cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        self.conn.commit()

    def update_balance(self, user_id: int, amount: int):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET balance = balance + ?
        WHERE user_id = ?
        ''', (amount, user_id))
        self.conn.commit()

    def update_stats(self, user_id: int, result: str):
        cursor = self.conn.cursor()
        updates = []
        params = []

        updates.append('games_played = games_played + 1')
        updates.append('last_game = ?')
        params.append(datetime.now())
        updates.append('games_today = games_today + 1')

        if result == 'win':
            updates.append('wins = wins + 1')
            updates.append('rating = rating + 25')
        elif result == 'lose':
            updates.append('rating = MAX(0, rating - 15)')

        query = f'''
        UPDATE users 
        SET {', '.join(updates)}
        WHERE user_id = ?
        '''
        params.append(user_id)

        cursor.execute(query, params)
        self.conn.commit()

    def ban_user(self, user_id: int, moderator_id: int, reason: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
        cursor.execute('''
        INSERT INTO moderation_logs (moderator_id, user_id, action, reason, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', (moderator_id, user_id, 'ban', reason, datetime.now()))
        self.conn.commit()

    def unban_user(self, user_id: int, moderator_id: int, reason: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
        cursor.execute('''
        INSERT INTO moderation_logs (moderator_id, user_id, action, reason, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', (moderator_id, user_id, 'unban', reason, datetime.now()))
        self.conn.commit()

    def check_daily_limit(self, user_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT games_today, last_daily_reset
        FROM users
        WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        if not result:
            return False
            
        games_today, last_reset = result
        
        now = datetime.now()
        if last_reset and (now - datetime.fromisoformat(last_reset)).days >= 1:
            cursor.execute('''
            UPDATE users
            SET games_today = 0, last_daily_reset = ?
            WHERE user_id = ?
            ''', (now, user_id))
            self.conn.commit()
            return True
            
        return games_today < 100