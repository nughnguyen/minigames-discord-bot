"""
Database Manager - Quản lý SQLite database cho game
Lưu trữ: game states, player stats, leaderboard
"""
import aiosqlite
import json
from typing import Dict, List, Optional
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def initialize(self):
        """Tạo các bảng cần thiết"""
        async with aiosqlite.connect(self.db_path) as db:
            # Bảng game states (trạng thái game đang chơi)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS game_states (
                    channel_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    language TEXT NOT NULL,
                    current_word TEXT NOT NULL,
                    current_player_id INTEGER NOT NULL,
                    used_words TEXT NOT NULL,
                    players TEXT NOT NULL,
                    turn_count INTEGER DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_bot_challenge INTEGER DEFAULT 0,
                    turn_start_time REAL DEFAULT 0
                )
            """)
            
            # Migration check for existing tables (add turn_start_time if missing)
            try:
                await db.execute("ALTER TABLE game_states ADD COLUMN turn_start_time REAL DEFAULT 0")
            except Exception:
                pass  # Column likely exists
            
            # Bảng player stats (thống kê người chơi)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS player_stats (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    total_points INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    words_submitted INTEGER DEFAULT 0,
                    correct_words INTEGER DEFAULT 0,
                    wrong_words INTEGER DEFAULT 0,
                    longest_word TEXT DEFAULT '',
                    longest_word_length INTEGER DEFAULT 0,
                    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            # Bảng game history (lịch sử các game)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    language TEXT NOT NULL,
                    winner_id INTEGER,
                    total_turns INTEGER DEFAULT 0,
                    total_words INTEGER DEFAULT 0,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
    
    # ===== GAME STATE METHODS =====
    
    async def create_game(self, channel_id: int, guild_id: int, language: str, 
                         first_word: str, first_player_id: int, is_bot_challenge: bool = False):
        """Tạo game mới"""
        import time
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO game_states 
                (channel_id, guild_id, language, current_word, current_player_id, 
                 used_words, players, turn_count, is_bot_challenge, turn_start_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (channel_id, guild_id, language, first_word, first_player_id,
                  json.dumps([first_word.lower()]), json.dumps([first_player_id]), 
                  0, 1 if is_bot_challenge else 0, time.time()))
            await db.commit()
    
    async def get_game_state(self, channel_id: int) -> Optional[Dict]:
        """Lấy trạng thái game hiện tại"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM game_states WHERE channel_id = ?", 
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                # Check row length to handle schema changes gracefully if select * is used
                # Current schema has 11 columns
                turn_start_time = row[10] if len(row) > 10 else 0
                
                return {
                    'channel_id': row[0],
                    'guild_id': row[1],
                    'language': row[2],
                    'current_word': row[3],
                    'current_player_id': row[4],
                    'used_words': json.loads(row[5]),
                    'players': json.loads(row[6]),
                    'turn_count': row[7],
                    'started_at': row[8],
                    'is_bot_challenge': bool(row[9]),
                    'turn_start_time': turn_start_time
                }
    
    async def update_game_turn(self, channel_id: int, new_word: str, next_player_id: int):
        """Cập nhật lượt chơi"""
        import time
        async with aiosqlite.connect(self.db_path) as db:
            # Lấy state hiện tại
            game_state = await self.get_game_state(channel_id)
            if not game_state:
                return
            
            # Cập nhật used_words và players
            used_words = game_state['used_words']
            used_words.append(new_word.lower())
            
            players = game_state['players']
            if next_player_id not in players:
                players.append(next_player_id)
            
            # Update database
            await db.execute("""
                UPDATE game_states 
                SET current_word = ?, 
                current_player_id = ?, 
                used_words = ?,
                players = ?,
                turn_count = turn_count + 1,
                turn_start_time = ?
                WHERE channel_id = ?
            """, (new_word, next_player_id, json.dumps(used_words), 
                  json.dumps(players), time.time(), channel_id))
            await db.commit()
    
    async def delete_game(self, channel_id: int):
        """Xóa game (kết thúc)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM game_states WHERE channel_id = ?", (channel_id,))
            await db.commit()
    
    async def is_game_active(self, channel_id: int) -> bool:
        """Kiểm tra có game đang chơi không"""
        game_state = await self.get_game_state(channel_id)
        return game_state is not None
    
    # ===== PLAYER STATS METHODS =====
    
    async def add_points(self, user_id: int, guild_id: int, points: int):
        """Thêm điểm cho người chơi"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO player_stats (user_id, guild_id, total_points)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    total_points = total_points + ?
            """, (user_id, guild_id, points, points))
            await db.commit()
    
    async def update_player_stats(self, user_id: int, guild_id: int, 
                                  word: str, is_correct: bool):
        """Cập nhật thống kê người chơi"""
        async with aiosqlite.connect(self.db_path) as db:
            if is_correct:
                await db.execute("""
                    INSERT INTO player_stats 
                    (user_id, guild_id, words_submitted, correct_words, longest_word, longest_word_length)
                    VALUES (?, ?, 1, 1, ?, ?)
                    ON CONFLICT(user_id, guild_id) DO UPDATE SET
                        words_submitted = words_submitted + 1,
                        correct_words = correct_words + 1,
                        longest_word = CASE WHEN ? > longest_word_length THEN ? ELSE longest_word END,
                        longest_word_length = CASE WHEN ? > longest_word_length THEN ? ELSE longest_word_length END,
                        last_played = CURRENT_TIMESTAMP
                """, (user_id, guild_id, word, len(word), 
                      len(word), word, len(word), len(word)))
            else:
                await db.execute("""
                    INSERT INTO player_stats 
                    (user_id, guild_id, words_submitted, wrong_words)
                    VALUES (?, ?, 1, 1)
                    ON CONFLICT(user_id, guild_id) DO UPDATE SET
                        words_submitted = words_submitted + 1,
                        wrong_words = wrong_words + 1,
                        last_played = CURRENT_TIMESTAMP
                """, (user_id, guild_id))
            
            await db.commit()
    
    async def get_player_points(self, user_id: int, guild_id: int) -> int:
        """Lấy điểm của người chơi"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT total_points FROM player_stats WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Lấy bảng xếp hạng"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, total_points, games_played, correct_words, longest_word
                FROM player_stats
                WHERE guild_id = ?
                ORDER BY total_points DESC
                LIMIT ?
            """, (guild_id, limit)) as cursor:
                rows = await cursor.fetchall()
                
                return [
                    {
                        'user_id': row[0],
                        'total_points': row[1],
                        'games_played': row[2],
                        'correct_words': row[3],
                        'longest_word': row[4]
                    }
                    for row in rows
                ]
    
    # ===== GAME HISTORY METHODS =====
    
    async def save_game_history(self, channel_id: int, guild_id: int, 
                                language: str, winner_id: Optional[int], 
                                total_turns: int, total_words: int, started_at: str):
        """Lưu lịch sử game"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO game_history 
                (channel_id, guild_id, language, winner_id, total_turns, total_words, started_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (channel_id, guild_id, language, winner_id, total_turns, total_words, started_at))
            await db.commit()
