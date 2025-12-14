"""
Emoji constants for Discord bot reactions and messages
Sử dụng Unicode emojis để tương thích với mọi server
"""

# Game States
START = "⚔️"
END = "🏁"
SCROLL = "📜"
BAR = "┃"

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
STREAK = "<a:fire:1449633627628376189>"

# Custom Emoji
ANIMATED_EMOJI_CORRECT = "<a:tickmark:1449215039608459305>"
ANIMATED_EMOJI_WRONG = "<a:wrongmark:1449214999816830986>"
ANIMATED_EMOJI_DOT = "<a:bluedot:1375508734893363271>"
ANIMATED_EMOJI_COINZ = "<a:cattoken:1449205470861459546>"
ANIMATED_EMOJI_DISCORD = "<a:discord:1375511198036000899>"
EMOJI_DISCORD = "<discord:1449212058708213850>"
EMOJI_YOUTUBE = "<youtube:1449212122314838149>"
EMOJI_TIKTOK = "<tiktok:1449212222747447357>"
EMOJI_INSTAGRAM = "<instagram:1449212173673959454>"
EMOJI_FACEBOOK = "<facebook:1449211949861830908>"
EMOJI_INVITE = "<Invite:1449328307526176881>"
EMOJI_LINK = "<:link1:1449328347661471890>"
EMOJI_MOMO_PAY = "<:momo:1449636713247936512>"
EMOJI_GIVEAWAY = "<a:giveaway:1449637499470348339>"

# Bầu Cua (6 mặt của xúc xắc)
SIDE_1 = "<:nai:1449572167984611370>"
SIDE_2 = "<:bau:1449573245576548434>"
SIDE_3 = "<:meo:1449573262232260732>"
SIDE_4 = "<:ca:1449573251041722378>"
SIDE_5 = "<:cua:1449573256498512045>"
SIDE_6 = "<:tom:1449573240715612263>"

# Loading
LOADING = "<a:loading:1449348490269294773>"

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
    return random.choice([CORRECT, FIRE, HUNDRED, SPARKLES, LIGHTNING, ANIMATED_EMOJI_CORRECT, ANIMATED_EMOJI_FIRE, ANIMATED_EMOJI_HUNDRED])

def get_random_wrong_emoji() -> str:
    """Trả về emoji ngẫu nhiên cho câu trả lời sai"""
    import random
    return random.choice([WRONG, SKULL, MIND_BLOWN, SAD, ANIMATED_EMOJI_WRONG])
