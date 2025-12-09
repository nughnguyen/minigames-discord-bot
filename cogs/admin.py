"""
Admin/Challenge Cog - Chế độ thách đấu bot và lệnh admin
"""
import discord
from discord.ext import commands
from discord import app_commands
import random

import config
from utils import embeds, emojis
from utils.validator import WordValidator
from database.db_manager import DatabaseManager


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.validators = {}
    
    async def cog_load(self):
        """Load validators"""
        # Load word lists
        try:
            with open(config.WORDS_VI_PATH, 'r', encoding='utf-8') as f:
                words_vi = [line.strip() for line in f if line.strip()]
            self.validators['vi'] = WordValidator('vi', words_vi)
        except Exception as e:
            print(f"❌ Error loading Vietnamese words: {e}")
        
        try:
            with open(config.WORDS_EN_PATH, 'r', encoding='utf-8') as f:
                words_en = [line.strip() for line in f if line.strip()]
            self.validators['en'] = WordValidator('en', words_en)
        except Exception as e:
            print(f"❌ Error loading English words: {e}")
    
    @app_commands.command(name="challenge-bot", description="🤖 Thách đấu bot 1vs1!")
    @app_commands.describe(
        language="Chọn ngôn ngữ",
        difficulty="Độ khó (chưa implement, bot luôn ở chế độ khó)"
    )
    @app_commands.choices(
        language=[
            app_commands.Choice(name="🇻🇳 Tiếng Việt", value="vi"),
            app_commands.Choice(name="🇬🇧 English", value="en")
        ]
    )
    async def challenge_bot(
        self, 
        interaction: discord.Interaction,
        language: app_commands.Choice[str] = None,
        difficulty: str = "hard"
    ):
        """Thách đấu bot 1vs1"""
        lang = language.value if language else config.DEFAULT_LANGUAGE
        
        # Kiểm tra game đang chơi
        if await self.db.is_game_active(interaction.channel_id):
            await interaction.response.send_message(
                f"{emojis.WRONG} Đã có game đang chơi! Dùng `/stop-wordchain` để kết thúc.",
                ephemeral=True
            )
            return
        
        # Chọn từ đầu tiên
        validator = self.validators.get(lang)
        if not validator:
            await interaction.response.send_message(
                f"{emojis.WRONG} Ngôn ngữ không được hỗ trợ!",
                ephemeral=True
            )
            return
        
        first_word = random.choice(list(validator.word_list))
        
        # Tạo game với bot
        await self.db.create_game(
            channel_id=interaction.channel_id,
            guild_id=interaction.guild_id,
            language=lang,
            first_word=first_word,
            first_player_id=interaction.user.id,
            is_bot_challenge=True
        )
        
        # Thêm bot vào danh sách người chơi
        game_state = await self.db.get_game_state(interaction.channel_id)
        players = game_state['players']
        players.append(self.bot.user.id)
        
        # Update lại database
        import aiosqlite
        async with aiosqlite.connect(config.DATABASE_PATH) as db:
            import json
            await db.execute(
                "UPDATE game_states SET players = ? WHERE channel_id = ?",
                (json.dumps(players), interaction.channel_id)
            )
            await db.commit()
        
        # Gửi thông báo bắt đầu
        challenge_embed = embeds.create_bot_challenge_embed(difficulty)
        start_embed = embeds.create_game_start_embed(lang, first_word, interaction.user.mention)
        
        await interaction.response.send_message(embeds=[challenge_embed, start_embed])
        
        # Lấy game cog để bắt đầu timeout
        game_cog = self.bot.get_cog('GameCog')
        if game_cog:
            await game_cog.start_turn_timeout(interaction.channel_id, interaction.user.id)
    
    @app_commands.command(name="add-points", description="➕ Thêm điểm cho người chơi (Admin only)")
    @app_commands.describe(
        user="Người chơi nhận điểm",
        points="Số điểm cần thêm"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_points(
        self, 
        interaction: discord.Interaction,
        user: discord.User,
        points: int
    ):
        """Admin thêm điểm cho người chơi"""
        await self.db.add_points(user.id, interaction.guild_id, points)
        
        await interaction.response.send_message(
            f"✅ Đã thêm **{points}** điểm cho {user.mention}!",
            ephemeral=True
        )
    
    @app_commands.command(name="reset-stats", description="🔄 Reset thống kê (Admin only)")
    @app_commands.describe(user="Người chơi cần reset (để trống để reset tất cả)")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_stats(
        self, 
        interaction: discord.Interaction,
        user: discord.User = None
    ):
        """Admin reset thống kê"""
        import aiosqlite
        
        async with aiosqlite.connect(config.DATABASE_PATH) as db:
            if user:
                # Reset 1 người
                await db.execute(
                    "DELETE FROM player_stats WHERE user_id = ? AND guild_id = ?",
                    (user.id, interaction.guild_id)
                )
                message = f"✅ Đã reset thống kê của {user.mention}!"
            else:
                # Reset tất cả
                await db.execute(
                    "DELETE FROM player_stats WHERE guild_id = ?",
                    (interaction.guild_id,)
                )
                message = "✅ Đã reset toàn bộ thống kê server!"
            
            await db.commit()
        
        await interaction.response.send_message(message, ephemeral=True)
    
    @app_commands.command(name="help", description="❓ Hướng dẫn sử dụng bot")
    async def help_command(self, interaction: discord.Interaction):
        """Hiển thị hướng dẫn"""
        embed = discord.Embed(
            title=f"{emojis.SCROLL} Hướng Dẫn Bot Nối Từ",
            description="Chào mừng đến với bot nối từ! Dưới đây là các lệnh và cách chơi:",
            color=config.COLOR_INFO
        )
        
        # Game Commands
        embed.add_field(
            name=f"{emojis.START} Lệnh Game",
            value=(
                "`/start-wordchain [ngôn_ngữ]` - Bắt đầu game\n"
                "`/stop-wordchain` - Kết thúc game\n"
                "`/status` - Xem trạng thái game\n"
                "`/challenge-bot [ngôn_ngữ]` - Thách đấu bot 1vs1"
            ),
            inline=False
        )
        
        # Powerup Commands
        embed.add_field(
            name=f"{emojis.JOKER} Lệnh Hỗ Trợ",
            value=(
                f"`/hint` - Gợi ý chữ cái tiếp theo ({config.HINT_COST} điểm)\n"
                f"`/pass` - Bỏ lượt không bị trừ điểm ({config.PASS_COST} điểm)"
            ),
            inline=False
        )
        
        # Stats Commands
        embed.add_field(
            name=f"{emojis.TROPHY} Lệnh Thống Kê",
            value=(
                "`/leaderboard` - Xem bảng xếp hạng\n"
                "`/stats [user]` - Xem thống kê cá nhân"
            ),
            inline=False
        )
        
        # How to Play
        embed.add_field(
            name=f"{emojis.THINKING} Cách Chơi",
            value=(
                "1️⃣ Bắt đầu game bằng `/start-wordchain`\n"
                "2️⃣ Nối từ bắt đầu bằng chữ cái cuối của từ trước\n"
                f"3️⃣ Bạn có **{config.TURN_TIMEOUT} giây** để trả lời\n"
                "4️⃣ Từ không được lặp lại trong cùng game\n"
                "5️⃣ Từ dài (>10 ký tự) nhận thêm điểm!"
            ),
            inline=False
        )
        
        # Points System
        embed.add_field(
            name=f"{emojis.STAR} Hệ Thống Điểm",
            value=(
                f"✅ Từ đúng: **+{config.POINTS_CORRECT}** điểm\n"
                f"🔥 Từ dài (>10 chữ): **+{config.POINTS_LONG_WORD}** điểm\n"
                f"❌ Từ sai/Hết giờ: **{config.POINTS_WRONG}** điểm"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Bot được phát triển bởi Quốc Hưng | Prefix: {config.COMMAND_PREFIX}")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function cho cog"""
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(AdminCog(bot, db))
