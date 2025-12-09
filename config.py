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
TURN_TIMEOUT = int(os.getenv('TURN_TIMEOUT', 45))  # Thời gian mỗi lượt (giây)

# Points System
POINTS_CORRECT = int(os.getenv('POINTS_CORRECT', 1))
POINTS_LONG_WORD = int(os.getenv('POINTS_LONG_WORD', 5))
POINTS_RARE_WORD = int(os.getenv('POINTS_RARE_WORD', 10))
POINTS_WRONG = int(os.getenv('POINTS_WRONG', -2))

# Time-Based Scoring (seconds)
POINTS_FAST_REPLY = int(os.getenv('POINTS_FAST_REPLY', 3))  # < 10s
POINTS_MEDIUM_REPLY = int(os.getenv('POINTS_MEDIUM_REPLY', 2))  # 10-20s
POINTS_SLOW_REPLY = int(os.getenv('POINTS_SLOW_REPLY', 1))  # > 20s

# Advanced Word Scoring
POINTS_ADVANCED_WORD = int(os.getenv('POINTS_ADVANCED_WORD', 5))  # IELTS 7+, long words
MIN_WORD_LENGTH_EN = int(os.getenv('MIN_WORD_LENGTH_EN', 3))  # Minimum 3 letters for English
LONG_WORD_THRESHOLD = int(os.getenv('LONG_WORD_THRESHOLD', 7))  # 7+ letters = long word

# Powerups
HINT_COST = int(os.getenv('HINT_COST', 10))
PASS_COST = int(os.getenv('PASS_COST', 20))

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

# Dictionary API Settings
USE_DICTIONARY_API = os.getenv('USE_DICTIONARY_API', 'true').lower() == 'true'
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 5))  # seconds
ENABLE_WORD_CACHE = os.getenv('ENABLE_WORD_CACHE', 'true').lower() == 'true'
CACHE_SIZE = int(os.getenv('CACHE_SIZE', 1000))

# Languages
SUPPORTED_LANGUAGES = ['vi', 'en']
