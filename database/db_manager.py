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
                    turn_start_time REAL DEFAULT 0,
                    wrong_attempts INTEGER DEFAULT 0,
                    scores TEXT DEFAULT '{}'
                )
            """)
            
            # Migration check for existing tables (add new columns if missing)
            try:
                await db.execute("ALTER TABLE game_states ADD COLUMN turn_start_time REAL DEFAULT 0")
            except Exception:
                pass  # Column likely exists
                
            try:
                await db.execute("ALTER TABLE game_states ADD COLUMN wrong_attempts INTEGER DEFAULT 0")
            except Exception:
                pass

            try:
                await db.execute("ALTER TABLE game_states ADD COLUMN scores TEXT DEFAULT '{}'")
            except Exception:
                pass
            
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
            
            # Channel Configs
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channel_configs (
                    channel_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    game_type TEXT NOT NULL
                )
            """)
            
            await db.commit()
            
            # Migrate points to global (guild_id = 0)
            await self.migrate_global_points(db)

    async def migrate_global_points(self, db):
        """Chuyển đổi điểm sang hệ thống global (guild_id=0)"""
        # Check specific user to see if migration needed or just run it idempotently?
        # Aggregating points to guild_id=0
        await db.execute("""
            INSERT INTO player_stats (user_id, guild_id, total_points)
            SELECT user_id, 0, SUM(total_points)
            FROM player_stats
            WHERE guild_id != 0 AND total_points > 0
            GROUP BY user_id
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                total_points = total_points + excluded.total_points
        """)
        
        # Reset local points to 0 to avoid double counting if we run this again? 
        # Actually safer to just set them to 0.
        await db.execute("UPDATE player_stats SET total_points = 0 WHERE guild_id != 0")
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
                 used_words, players, turn_count, is_bot_challenge, turn_start_time, wrong_attempts, scores)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (channel_id, guild_id, language, first_word, first_player_id,
                  json.dumps([first_word.lower()]), json.dumps([first_player_id]), 
                  0, 1 if is_bot_challenge else 0, time.time(), 0, '{}'))
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
                # Current schema has 13 columns
                turn_start_time = row[10] if len(row) > 10 else 0
                wrong_attempts = row[11] if len(row) > 11 else 0
                scores_json = row[12] if len(row) > 12 else '{}'
                
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
                    'turn_start_time': turn_start_time,
                    'wrong_attempts': wrong_attempts,
                    'scores': json.loads(scores_json)
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
                turn_start_time = ?,
                wrong_attempts = 0
                WHERE channel_id = ?
            """, (new_word, next_player_id, json.dumps(used_words), 
                  json.dumps(players), time.time(), channel_id))
            await db.commit()
            
    async def update_wrong_attempts(self, channel_id: int, attempts: int):
        """Cập nhật số lần trả lời sai"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE game_states 
                SET wrong_attempts = ?
                WHERE channel_id = ?
            """, (attempts, channel_id))
            await db.commit()

    async def update_game_score(self, channel_id: int, player_id: int, points_delta: int):
        """Cập nhật điểm trong phiên chơi hiện tại"""
        async with aiosqlite.connect(self.db_path) as db:
            # Lấy state hiện tại
            game_state = await self.get_game_state(channel_id)
            if not game_state:
                return
            
            scores = game_state['scores']
            player_key = str(player_id) # JSON dict keys are strings
            
            current_score = scores.get(player_key, 0)
            scores[player_key] = current_score + points_delta
            
            await db.execute("""
                UPDATE game_states 
                SET scores = ?
                WHERE channel_id = ?
            """, (json.dumps(scores), channel_id))
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
        """Thêm điểm cho người chơi (Global Points - Guild ID 0)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO player_stats (user_id, guild_id, total_points)
                VALUES (?, 0, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    total_points = total_points + ?
            """, (user_id, points, points))
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
        """Lấy điểm của người chơi (Global Points - Guild ID 0)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT total_points FROM player_stats WHERE user_id = ? AND guild_id = 0",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def get_leaderboard(self, member_ids: List[int], limit: int = 10) -> List[Dict]:
        """Lấy bảng xếp hạng top tỷ phú trong danh sách user_id được cung cấp (global points)"""
        if not member_ids:
            return []
            
        # Handle large lists by chunks to avoid SQL variable limit if needed, 
        # but for simplicity assuming server size < SQLITE_MAX_VARIABLE_NUMBER (default 999-32k)
        # If member_ids is huge, we make a formatted string of placeholders
        placeholders = ','.join('?' for _ in member_ids)
        
        # Optimization: if member_ids is huge (e.g > 2000), this query string building is heavy.
        # But for typical discord bot use cases (fetching top 10 from specific guild), it's acceptable.
        
        query = f"""
            SELECT user_id, total_points, games_played, correct_words, longest_word
            FROM player_stats
            WHERE guild_id = 0 AND user_id IN ({placeholders})
            ORDER BY total_points DESC
            LIMIT ?
        """
        
        # Args: list of ids + limit
        args = list(member_ids) + [limit]
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                async with db.execute(query, args) as cursor:
                    rows = await cursor.fetchall()
            except Exception as e:
                # If too many vars, fall back to fetching all global top and filtering in python
                print(f"⚠️ SQL Limit hit or error: {e}. Falling back to python filtering.")
                async with db.execute("""
                    SELECT user_id, total_points, games_played, correct_words, longest_word
                    FROM player_stats
                    WHERE guild_id = 0
                    ORDER BY total_points DESC
                """) as cursor:
                    all_rows = await cursor.fetchall()
                    
                member_set = set(member_ids)
                rows = []
                for row in all_rows:
                    if row[0] in member_set:
                        rows.append(row)
                        if len(rows) >= limit:
                            break
            
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

    # ===== CHANNEL CONFIG METHODS =====
    
    async def set_channel_config(self, channel_id: int, guild_id: int, game_type: str):
        """Cài đặt game mặc định cho channel"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO channel_configs (channel_id, guild_id, game_type)
                VALUES (?, ?, ?)
            """, (channel_id, guild_id, game_type))
            await db.commit()
            
    async def get_channel_config(self, channel_id: int) -> Optional[str]:
        """Lấy game_type mặc định của channel"""
        async with aiosqlite.connect(self.db_path) as db:
             # Ensure table exists first (lazy check)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channel_configs (
                    channel_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    game_type TEXT NOT NULL
                )
            """)
            
            async with db.execute(
                "SELECT game_type FROM channel_configs WHERE channel_id = ?",
                (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
