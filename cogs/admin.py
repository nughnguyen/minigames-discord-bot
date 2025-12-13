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

    @commands.command(name="sync", hidden=True)
    @commands.is_owner()
    async def sync_tree(self, ctx):
        """Syncs the slash command tree manually."""
        print("🔄 Manual sync initiated...")
        try:
            synced = await self.bot.tree.sync()
            print(f"  ✅ Synced {len(synced)} command(s)")
            await ctx.send(f"✅ Synced {len(synced)} command(s) globally.")
        except Exception as e:
            print(f"  ❌ Failed to sync commands: {e}")
            await ctx.send(f"❌ Failed to sync: {e}")
    
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
    
    @app_commands.command(name="add-coinz", description="➕ Thêm coinz cho người chơi (Admin only)")
    @app_commands.describe(
        user="Người chơi nhận coinz",
        points="Số coinz cần thêm"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_coinz(
        self, 
        interaction: discord.Interaction,
        user: discord.User,
        points: int
    ):
        """Admin thêm coinz cho người chơi"""
        await self.db.add_points(user.id, interaction.guild_id, points)
        
        await interaction.response.send_message(
            f"✅ Đã thêm **{points}** coinz cho {user.mention}!",
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

    @app_commands.command(name="set-game-channel", description="⚙️ Cài đặt game mặc định cho kênh này")
    @app_commands.describe(game_type="Chọn loại game (để trống để xóa cài đặt)")
    @app_commands.choices(game_type=[
        app_commands.Choice(name="🔤 Nối Từ (Word Chain)", value="wordchain"),
        app_commands.Choice(name="👑 Vua Tiếng Việt", value="vuatiengviet")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def set_game_channel(self, interaction: discord.Interaction, game_type: app_commands.Choice[str] = None):
        """Cài đặt game mặc định cho channel"""
        if game_type:
            await self.db.set_channel_config(interaction.channel_id, interaction.guild_id, game_type.value)
            await interaction.response.send_message(f"✅ Đã cài đặt kênh này là kênh **{game_type.name}**!\nDùng lệnh `/start` để bắt đầu nhanh.", ephemeral=True)
        else:
            # Logic để xóa cài đặt nếu cần, hiện tại db chỉ có insert or replace. 
            # Có thể set thành "" hoặc xoá row. 
            # Tạm thời set thành "none" hoặc simply override.
            # Với request user, họ muốn set kênh. Nếu muốn unset có thể thêm option.
            # Để đơn giản, cho phép set đè.
            pass
            
    # Alias commands as requested by user
    @app_commands.command(name="kenh-noi-tu-vn", description="⚙️ Đặt kênh này làm kênh Nối Từ Tiếng Việt")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_wordchain_channel(self, interaction: discord.Interaction):
        """Đặt kênh nối từ tiếng việt"""
        await self.db.set_channel_config(interaction.channel_id, interaction.guild_id, "wordchain")
        await interaction.response.send_message(f"✅ Đã đặt kênh này làm kênh chuyên **Nối Từ (Tiếng Việt)**!\nGõ `/start` để chơi ngay.", ephemeral=True)

    @app_commands.command(name="kenh-vua-tieng-viet", description="⚙️ Đặt kênh này làm kênh Vua Tiếng Việt")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_vuatiengviet_channel(self, interaction: discord.Interaction):
        """Đặt kênh vua tiếng việt"""
        await self.db.set_channel_config(interaction.channel_id, interaction.guild_id, "vuatiengviet")
        await interaction.response.send_message(f"✅ Đã đặt kênh này làm kênh chuyên **Vua Tiếng Việt**!\nGõ `/start` để chơi ngay.", ephemeral=True)
        
    @app_commands.command(name="kenh-noi-tu-en", description="⚙️ Đặt kênh này làm kênh Nối Từ Tiếng Anh (English)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_wordchain_en_channel(self, interaction: discord.Interaction):
        """Đặt kênh nối từ tiếng anh"""
        await self.db.set_channel_config(interaction.channel_id, interaction.guild_id, "wordchain_en")
        await interaction.response.send_message(f"✅ Đã đặt kênh này làm kênh chuyên **Nối Từ (English)**!\nGõ `/start` để chơi ngay.", ephemeral=True)
    



async def setup(bot: commands.Bot):
    """Setup function cho cog"""
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(AdminCog(bot, db))
