"""
Emoji constants for Discord bot reactions and messages
Sử dụng Unicode emojis để tương thích với mọi server
"""

# Game States
START = "⚔️"
END = "🏁"
SCROLL = "📜"

# Responses
CORRECT = "✅"
FIRE = "🔥"
HUNDRED = "💯"
WRONG = "❌"
SKULL = "💀"
MIND_BLOWN = "🤯"

# Timing
TIMEOUT = "⏰"
SNAIL = "🐌"
HOURGLASS = "⏳"

# Leaderboard
CROWN = "👑"
TROPHY = "🏆"
MEDAL_1ST = "🥇"
MEDAL_2ND = "🥈"
MEDAL_3RD = "🥉"

# Powerups
HINT = "💡"
PASS = "⏭️"
JOKER = "🃏"

# Bot Challenge
ROBOT = "🤖"
SWORD = "⚔️"
VS = "🆚"

# Misc
STAR = "⭐"
SPARKLES = "✨"
THINKING = "🤔"
CELEBRATION = "🎉"
SAD = "😢"
LIGHTNING = "⚡"

def get_rank_emoji(rank: int) -> str:
    """Trả về emoji dựa trên thứ hạng"""
    if rank == 1:
        return MEDAL_1ST
    elif rank == 2:
        return MEDAL_2ND
    elif rank == 3:
        return MEDAL_3RD
    elif rank <= 10:
        return TROPHY
    else:
        return STAR

def get_random_correct_emoji() -> str:
    """Trả về emoji ngẫu nhiên cho câu trả lời đúng"""
    import random
    return random.choice([CORRECT, FIRE, HUNDRED, SPARKLES, LIGHTNING])

def get_random_wrong_emoji() -> str:
    """Trả về emoji ngẫu nhiên cho câu trả lời sai"""
    import random
    return random.choice([WRONG, SKULL, MIND_BLOWN, SAD])
