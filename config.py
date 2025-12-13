"""
Configuration file for Discord Word Chain Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '/')

# Game Settings
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'vi')
REGISTRATION_TIMEOUT = int(os.getenv('REGISTRATION_TIMEOUT', 30))  # Thời gian đăng ký (giây)
TURN_TIMEOUT = int(os.getenv('TURN_TIMEOUT', 30))  # Thời gian mỗi lượt (giây)

# Points System
POINTS_CORRECT = int(os.getenv('POINTS_CORRECT', 100))
POINTS_LONG_WORD = int(os.getenv('POINTS_LONG_WORD', 200))
POINTS_RARE_WORD = int(os.getenv('POINTS_RARE_WORD', 50))
POINTS_WRONG = int(os.getenv('POINTS_WRONG', -50))
POINTS_TIMEOUT = int(os.getenv('POINTS_TIMEOUT', -150))
MAX_WRONG_ATTEMPTS = int(os.getenv('MAX_WRONG_ATTEMPTS', 5))

# Time-Based Scoring (seconds) - unused in code but kept for reference
POINTS_FAST_REPLY = int(os.getenv('POINTS_FAST_REPLY', 100))
POINTS_MEDIUM_REPLY = int(os.getenv('POINTS_MEDIUM_REPLY', 50)) 
POINTS_SLOW_REPLY = int(os.getenv('POINTS_SLOW_REPLY', 20))

# Advanced Word Scoring
MIN_WORD_LENGTH_EN = int(os.getenv('MIN_WORD_LENGTH_EN', 3))
LONG_WORD_THRESHOLD = int(os.getenv('LONG_WORD_THRESHOLD', 10))

# English Level Scoring
# Max bonus: 1000 (Academic/C2), Min: 0 (A1)
LEVEL_BONUS = {
    'a1': 0,
    'a2': 10,
    'b1': 50,
    'b2': 150,
    'c1': 500,
    'c2': 800,
    'academic': 1000,
    'formal': 300,
    'specialized': 600,
    'technical': 600,
    'literary': 700,
    'ielts': 600,
    'toeic': 600
}

# Powerups
HINT_COST = int(os.getenv('HINT_COST', 100))
PASS_COST = int(os.getenv('PASS_COST', 50))

# Database
DATABASE_PATH = 'data/wordchain.db'

# Word Lists
WORDS_VI_PATH = 'data/words_vi.txt'
WORDS_EN_PATH = 'data/words_en.txt'

# Embed Colors (Hex)
COLOR_SUCCESS = 0x00FF00  # Green
COLOR_ERROR = 0xFF0000    # Red
COLOR_INFO = 0x3498DB     # Blue
COLOR_WARNING = 0xFFA500  # Orange
COLOR_GOLD = 0xFFD700     # Gold
COLOR_NEUTRAL = 0x95A5A6  # Grey

# Dictionary API Settings
USE_DICTIONARY_API = os.getenv('USE_DICTIONARY_API', 'true').lower() == 'true'
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 5))  # seconds
ENABLE_WORD_CACHE = os.getenv('ENABLE_WORD_CACHE', 'true').lower() == 'true'
CACHE_SIZE = int(os.getenv('CACHE_SIZE', 1000))

# Languages
SUPPORTED_LANGUAGES = ['vi', 'en']

# Vua Tieng Viet Game
POINTS_VUA_TIENG_VIET = 5000
POINTS_VUA_TIENG_VIET_KHO = 10000
POINTS_VUA_TIENG_VIET_SIEU_KHO = 50000
DATA_VUA_TIENG_VIET_PATH = 'data/vua_tieng_viet.json'
