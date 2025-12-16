"""
Discord Embed utilities for beautiful messages
Tạo các embeds đẹp mắt và rực rỡ cho bot
"""
import discord
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import config
from utils import emojis

def create_game_start_embed(language: str, first_word: str, player_mention: str) -> discord.Embed:
    """Tạo embed cho game bắt đầu"""
    lang_flag = "🇻🇳" if language == "vi" else "🇬🇧"
    
    embed = discord.Embed(
        title=f"{emojis.START} Trò Chơi Nối Từ Bắt Đầu! {emojis.START}",
        description=f"**Ngôn ngữ:** {lang_flag} {'Tiếng Việt' if language == 'vi' else 'English'}",
        color=config.COLOR_SUCCESS,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    embed.add_field(
        name=f"{emojis.SCROLL} Từ Đầu Tiên",
        value=f"```{first_word.upper()}```",
        inline=False
    )
    
    embed.add_field(
        name=f"{emojis.HOURGLASS} Người Chơi Hiện Tại",
        value=player_mention,
        inline=True
    )
    
    embed.add_field(
        name=f"{emojis.TIMEOUT} Thời Gian",
        value=f"{config.TURN_TIMEOUT} giây",
        inline=True
    )
    
    embed.set_footer(text="Gửi từ tiếp theo trong kênh này!")
    
    return embed

def create_turn_embed(current_word: str, player_mention: str, time_left: int) -> discord.Embed:
    """Tạo embed cho lượt chơi"""
    embed = discord.Embed(
        title=f"{emojis.THINKING} Lượt Tiếp Theo",
        color=config.COLOR_INFO,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    embed.add_field(
        name="Từ Hiện Tại",
        value=f"```{current_word.upper()}```",
        inline=False
    )
    
    embed.add_field(
        name="Người Chơi",
        value=player_mention,
        inline=True
    )
    
    embed.add_field(
        name=f"{emojis.TIMEOUT} Thời Gian Còn Lại",
        value=f"{time_left}s",
        inline=True
    )
    
    return embed


def create_correct_answer_embed(player_mention: str, word: str, points: int, reason: str = "") -> discord.Embed:
    """Tạo embed cho câu trả lời đúng (Simple version)"""
    emoji = emojis.get_random_correct_emoji()
    
    embed = discord.Embed(
        title=f"{emoji} Chính Xác!",
        description=f"{player_mention} đã nối từ **{word.upper()}**",
        color=config.COLOR_SUCCESS,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    embed.add_field(
        name=f"{emojis.STAR} Coiz Nhận Được",
        value=f"+{points:,} Coiz {emojis.ANIMATED_EMOJI_COIZ}",
        inline=True
    )
    
    if reason:
        embed.add_field(
            name=f"{emojis.SPARKLES} Bonus",
            value=reason,
            inline=True
        )
    
    return embed

def create_rich_correct_answer_embed(
    author: discord.User, 
    word: str, 
    word_info: dict, 
    meaning_vi: str, 
    points: int, 
    bonus_reason: str
) -> List[discord.Embed]:
    """Tạo bộ embed câu trả lời đúng (Merged version)"""
    
    # === Embed 1: Main Embed ===
    embed = discord.Embed(
        title=f"{word.upper()}", # Title is the WORD (Big text)
        color=config.COLOR_SUCCESS,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    # Author Info
    embed.set_author(
        name=f"Chính xác! - {author.display_name}",
        icon_url=author.display_avatar.url
    )
    
    # Description: Phonetic + Meaning
    desc_lines = []
    
    phonetic = ""
    if word_info and word_info.get('phonetic'):
        phonetic = f" /{word_info['phonetic']}/"
        
    if phonetic:
        desc_lines.append(f"`{phonetic}`")
    
    if meaning_vi:
        desc_lines.append(f"\n🇻🇳 Nghĩa:\n**{meaning_vi}**")
        
    embed.description = "".join(desc_lines)
    
    # Add clickable link if audio exists
    if word_info and word_info.get('audio_url'):
        embed.url = word_info['audio_url']
        
    # === Add Points Fields ===
    if points > 0:
        # Field 1: Base Points
        embed.add_field(
            name="Từ hợp lệ",
            value=f"+{config.POINTS_CORRECT:,}",
            inline=True
        )
        
        # Field 2...n: Bonuses
        bonuses = []
        if bonus_reason:
            if isinstance(bonus_reason, list):
                 bonuses = bonus_reason
            else:
                 bonuses = [b.strip() for b in bonus_reason.split('\n') if b.strip()]
        
        for bonus in bonuses:
            embed.add_field(
                name="Bonus",
                value=bonus,
                inline=True
            )
            
        # Total Row
        if bonuses:
            embed.add_field(
                name="Tổng cộng",
                value=f"**+{points:,}** {emojis.ANIMATED_EMOJI_COIZ}",
                inline=False
            )
    
    return [embed]

def create_wrong_answer_embed(player_mention: str, word: str, reason: str) -> discord.Embed:
    """Tạo embed cho câu trả lời sai"""
    emoji = emojis.get_random_wrong_emoji()
    
    embed = discord.Embed(
        title=f"{emoji} Sai Rồi!",
        description=f"{player_mention} - Từ **{word}** không hợp lệ",
        color=config.COLOR_ERROR,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    embed.add_field(
        name="Lý Do",
        value=reason,
        inline=False
    )
    
    embed.add_field(
        name="Coiz Bị Trừ",
        value=f"{config.POINTS_WRONG:,} Coiz {emojis.ANIMATED_EMOJI_COIZ}",
        inline=True
    )
    
    return embed

def create_timeout_embed(player_mention: str) -> discord.Embed:
    """Tạo embed cho hết giờ"""
    embed = discord.Embed(
        title=f"{emojis.TIMEOUT} Hết Giờ!",
        description=f"{player_mention} {emojis.SNAIL} đã không trả lời kịp thời!",
        color=config.COLOR_WARNING,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    embed.add_field(
        name="Coiz Bị Trừ",
        value=f"{config.POINTS_WRONG:,} Coiz {emojis.ANIMATED_EMOJI_COIZ}",
        inline=True
    )
    
    return embed

def create_game_end_embed(winner_data: Dict, total_turns: int, used_words_count: int) -> discord.Embed:
    """Tạo embed cho kết thúc game"""
    embed = discord.Embed(
        title=f"{emojis.END} Trò Chơi Kết Thúc! {emojis.CELEBRATION}",
        description=f"Tổng số lượt chơi: **{total_turns}**\nTổng số từ đã dùng: **{used_words_count}**",
        color=config.COLOR_GOLD,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    if winner_data:
        # winner_data contains: 'user_id', 'session_points', 'total_points'
        session_text = f"**{winner_data['session_points']:,} Coiz** {emojis.ANIMATED_EMOJI_COIZ}"
        
        embed.add_field(
            name=f"{emojis.CROWN} Người Chiến Thắng",
            value=f"<@{winner_data['user_id']}> vòng này kiếm được: {session_text}",
            inline=False
        )
    
    embed.set_footer(text="Cảm ơn đã chơi!")
    
    return embed

def create_leaderboard_embed(leaderboard_data: List[Dict], server_name: str) -> discord.Embed:
    """Tạo embed cho bảng xếp hạng"""
    embed = discord.Embed(
        title=f"{emojis.TROPHY} Bảng Xếp Hạng Top 10 Tỷ Phú - {server_name}",
        description=f"{emojis.STAR} Danh sách những đại gia giàu nhất server",
        color=config.COLOR_GOLD,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    if not leaderboard_data:
        embed.add_field(
            name="Trống",
            value="Chưa có tỷ phú nào!",
            inline=False
        )
        return embed
    
    leaderboard_text = ""
    for idx, player in enumerate(leaderboard_data, 1):
        rank_emoji = emojis.get_rank_emoji(idx)
        leaderboard_text += f"{rank_emoji} **#{idx}** <@{player['user_id']}> - **{player['total_points']:,}** Coiz {emojis.ANIMATED_EMOJI_COIZ}\n"
    
    embed.add_field(
        name="Danh Sách Tỷ Phú",
        value=leaderboard_text,
        inline=False
    )
    
    embed.set_footer(text="Cày game để leo top tỷ phú!")
    
    return embed

def create_hint_embed(hint: str, cost: int) -> discord.Embed:
    """Tạo embed cho gợi ý"""
    embed = discord.Embed(
        title=f"{emojis.HINT} Gợi Ý",
        description=f"Từ tiếp theo bắt đầu bằng: **{hint}**",
        color=config.COLOR_INFO,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    embed.add_field(
        name="Chi Phí",
        value=f"-{cost:,} Coiz {emojis.ANIMATED_EMOJI_COIZ}",
        inline=True
    )
    
    return embed

def create_status_embed(game_state: Dict) -> discord.Embed:
    """Tạo embed cho trạng thái game"""
    embed = discord.Embed(
        title=f"{emojis.SCROLL} Trạng Thái Game",
        color=config.COLOR_INFO,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    embed.add_field(
        name="Từ Hiện Tại",
        value=f"```{game_state['current_word'].upper()}```",
        inline=False
    )
    
    embed.add_field(
        name="Người Chơi Hiện Tại",
        value=f"<@{game_state['current_player']}>",
        inline=True
    )
    
    embed.add_field(
        name="Số Từ Đã Dùng",
        value=str(game_state['words_used']),
        inline=True
    )
    
    embed.add_field(
        name="Số Lượt",
        value=str(game_state['turn_count']),
        inline=True
    )
    
    return embed

def create_bot_challenge_embed(difficulty: str) -> discord.Embed:
    """Tạo embed cho chế độ đấu bot"""
    embed = discord.Embed(
        title=f"{emojis.ROBOT} {emojis.VS} Thách Đấu Bot!",
        description=f"Bạn đang thách đấu bot ở chế độ **{difficulty.upper()}**!",
        color=config.COLOR_WARNING,
        timestamp=datetime.now(timezone(timedelta(hours=7)))
    )
    
    embed.add_field(
        name=f"{emojis.SWORD} Lưu Ý",
        value="Bot sẽ luôn chọn từ khó và dài!\nChúc bạn may mắn!",
        inline=False
    )
    
    return embed
