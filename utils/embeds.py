"""
Discord Embed utilities for beautiful messages
Tạo các embeds đẹp mắt và rực rỡ cho bot
"""
import discord
from datetime import datetime
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
    """Tạo embed cho câu trả lời đúng"""
    emoji = emojis.get_random_correct_emoji()
    
    embed = discord.Embed(
        title=f"{emoji} Chính Xác!",
        description=f"{player_mention} đã nối từ **{word.upper()}**",
        color=config.COLOR_SUCCESS,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name=f"{emojis.STAR} Điểm Nhận Được",
        value=f"+{points} điểm",
        inline=True
    )
    
    if reason:
        embed.add_field(
            name=f"{emojis.SPARKLES} Bonus",
            value=reason,
            inline=True
        )
    
    return embed

def create_wrong_answer_embed(player_mention: str, word: str, reason: str) -> discord.Embed:
    """Tạo embed cho câu trả lời sai"""
    emoji = emojis.get_random_wrong_emoji()
    
    embed = discord.Embed(
        title=f"{emoji} Sai Rồi!",
        description=f"{player_mention} - Từ **{word}** không hợp lệ",
        color=config.COLOR_ERROR,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="Lý Do",
        value=reason,
        inline=False
    )
    
    embed.add_field(
        name="Điểm Bị Trừ",
        value=f"{config.POINTS_WRONG} điểm",
        inline=True
    )
    
    return embed

def create_timeout_embed(player_mention: str) -> discord.Embed:
    """Tạo embed cho hết giờ"""
    embed = discord.Embed(
        title=f"{emojis.TIMEOUT} Hết Giờ!",
        description=f"{player_mention} {emojis.SNAIL} đã không trả lời kịp thời!",
        color=config.COLOR_WARNING,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="Điểm Bị Trừ",
        value=f"{config.POINTS_WRONG} điểm",
        inline=True
    )
    
    return embed

def create_game_end_embed(winner_data: Dict, total_turns: int, used_words_count: int) -> discord.Embed:
    """Tạo embed cho kết thúc game"""
    embed = discord.Embed(
        title=f"{emojis.END} Trò Chơi Kết Thúc! {emojis.CELEBRATION}",
        description=f"Tổng số lượt chơi: **{total_turns}**\nTổng số từ đã dùng: **{used_words_count}**",
        color=config.COLOR_GOLD,
        timestamp=datetime.utcnow()
    )
    
    if winner_data:
        embed.add_field(
            name=f"{emojis.CROWN} Người Chiến Thắng",
            value=f"<@{winner_data['user_id']}> với **{winner_data['points']} điểm**!",
            inline=False
        )
    
    embed.set_footer(text="Cảm ơn đã chơi!")
    
    return embed

def create_leaderboard_embed(leaderboard_data: List[Dict], server_name: str) -> discord.Embed:
    """Tạo embed cho bảng xếp hạng"""
    embed = discord.Embed(
        title=f"{emojis.TROPHY} Bảng Xếp Hạng - {server_name}",
        description=f"{emojis.STAR} Top 10 Người Chơi Xuất Sắc Nhất",
        color=config.COLOR_GOLD,
        timestamp=datetime.utcnow()
    )
    
    if not leaderboard_data:
        embed.add_field(
            name="Trống",
            value="Chưa có người chơi nào!",
            inline=False
        )
        return embed
    
    leaderboard_text = ""
    for idx, player in enumerate(leaderboard_data, 1):
        rank_emoji = emojis.get_rank_emoji(idx)
        leaderboard_text += f"{rank_emoji} **#{idx}** <@{player['user_id']}> - {player['total_points']} điểm\n"
    
    embed.add_field(
        name="Xếp Hạng",
        value=leaderboard_text,
        inline=False
    )
    
    embed.set_footer(text="Tiếp tục chơi để leo hạng!")
    
    return embed

def create_hint_embed(hint: str, cost: int) -> discord.Embed:
    """Tạo embed cho gợi ý"""
    embed = discord.Embed(
        title=f"{emojis.HINT} Gợi Ý",
        description=f"Từ tiếp theo bắt đầu bằng: **{hint}**",
        color=config.COLOR_INFO,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name="Chi Phí",
        value=f"-{cost} điểm",
        inline=True
    )
    
    return embed

def create_status_embed(game_state: Dict) -> discord.Embed:
    """Tạo embed cho trạng thái game"""
    embed = discord.Embed(
        title=f"{emojis.SCROLL} Trạng Thái Game",
        color=config.COLOR_INFO,
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(
        name=f"{emojis.SWORD} Lưu Ý",
        value="Bot sẽ luôn chọn từ khó và dài!\nChúc bạn may mắn!",
        inline=False
    )
    
    return embed
