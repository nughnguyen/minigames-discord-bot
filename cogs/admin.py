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
    @app_commands.command(name="kenh-noi-tu", description="⚙️ Đặt kênh này làm kênh Nối Từ")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_wordchain_channel(self, interaction: discord.Interaction):
        """Đặt kênh nối từ"""
        await self.db.set_channel_config(interaction.channel_id, interaction.guild_id, "wordchain")
        await interaction.response.send_message(f"✅ Đã đặt kênh này làm kênh chuyên **Nối Từ**!\nGõ `/start` để chơi ngay.", ephemeral=True)

    @app_commands.command(name="kenh-vua-tieng-viet", description="⚙️ Đặt kênh này làm kênh Vua Tiếng Việt")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_vuatiengviet_channel(self, interaction: discord.Interaction):
        """Đặt kênh vua tiếng việt"""
        await self.db.set_channel_config(interaction.channel_id, interaction.guild_id, "vuatiengviet")
        await interaction.response.send_message(f"✅ Đã đặt kênh này làm kênh chuyên **Vua Tiếng Việt**!\nGõ `/start` để chơi ngay.", ephemeral=True)
    
    @app_commands.command(name="help", description="❓ Hướng dẫn sử dụng bot")
    async def help_command(self, interaction: discord.Interaction):
        """Hiển thị hướng dẫn"""
        view = HelpView()
        
        embed = discord.Embed(
            title=f"{emojis.SCROLL} Hướng Dẫn Bot MiniGames",
            description="Hãy chọn một danh mục bên dưới để xem chi tiết các lệnh!",
            color=config.COLOR_INFO
        )
        embed.set_footer(text=f"Bot được phát triển bởi Quốc Hưng | Prefix: {config.COMMAND_PREFIX}")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Nối Từ (Word Chain)", 
                description="Lệnh và cách chơi Nối Từ", 
                emoji="🔤", 
                value="wordchain"
            ),
            discord.SelectOption(
                label="Vua Tiếng Việt", 
                description="Lệnh và cách chơi Vua Tiếng Việt", 
                emoji="👑", 
                value="vtv"
            ),
            discord.SelectOption(
                label="Hệ Thống & Admin", 
                description="Lệnh thống kê và cài đặt", 
                emoji="🛠️", 
                value="system"
            ),
            discord.SelectOption(
                label="Thông Tin", 
                description="Thông tin bot và dev", 
                emoji="ℹ️", 
                value="info"
            )
        ]
        super().__init__(
            placeholder="Chọn danh mục cần tra cứu...", 
            min_values=1, 
            max_values=1, 
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        
        if value == "wordchain":
            embed = discord.Embed(
                title="🔤 Hướng Dẫn - Nối Từ",
                description="Luật chơi: Nối tiếp từ bắt đầu bằng chữ cái cuối của từ trước đó.",
                color=config.COLOR_INFO
            )
            embed.add_field(
                name="🎮 Lệnh Game",
                value=(
                    "`/start` - Bắt đầu game (cần set kênh trước)\n"
                    "`/stop` - Dừng game đang chơi\n"
                    "`/challenge-bot` - Thách đấu solo với Bot\n"
                    "`/status` - Xem trạng thái lượt chơi hiện tại"
                ),
                inline=False
            )
            embed.add_field(
                name="💡 Hỗ Trợ",
                value=(
                    f"`/hint` - Gợi ý chữ cái tiếp theo ({config.HINT_COST} coinz)\n"
                    f"`/pass` - Bỏ lượt an toàn ({config.PASS_COST} coinz)\n"
                    f"**Timeout:** {config.TURN_TIMEOUT}s (Trừ {config.POINTS_TIMEOUT} coinz)"
                ),
                inline=False
            )
            embed.add_field(
                name="🏆 Điểm Thưởng",
                value=(
                    f"• Đúng: +{config.POINTS_CORRECT}\n"
                    f"• Từ dài/Khó: +{config.POINTS_LONG_WORD}/+{config.POINTS_ADVANCED_WORD}\n"
                    f"• Sai: {config.POINTS_WRONG}"
                ),
                inline=False
            )
            
        elif value == "vtv":
            embed = discord.Embed(
                title="👑 Hướng Dẫn - Vua Tiếng Việt",
                description="Sắp xếp các ký tự bị đảo lộn thành từ/câu có nghĩa.",
                color=config.COLOR_GOLD
            )
            embed.add_field(
                name="🎮 Lệnh Game",
                value=(
                    "`/start` - Bắt đầu game (cần set kênh trước)\n"
                    "`/stop` - Dừng game"
                ),
                inline=False
            )
            embed.add_field(
                name="📖 Cách Chơi",
                value=(
                    "• Bot đưa ra một chuỗi ký tự bị xáo trộn.\n"
                    "• Gõ trực tiếp đáp án vào kênh chat.\n"
                    "• Sau 45s sẽ có gợi ý (bị trừ điểm thưởng).\n"
                    "• Trả lời càng nhanh và ít gợi ý càng nhiều điểm!"
                ),
                inline=False
            )
            
        elif value == "system":
            embed = discord.Embed(
                title="🛠️ Lệnh Hệ Thống & Admin",
                description="Các lệnh chức năng và quản lý",
                color=config.COLOR_NEUTRAL
            )
            embed.add_field(
                name="📊 Thống Kê",
                value=(
                    "`/leaderboard` - Xem Bảng Xếp Hạng Top Server\n"
                    "`/stats [user]` - Xem thông tin cá nhân"
                ),
                inline=False
            )
            embed.add_field(
                name="⚙️ Admin (Quản Lý Kênh)",
                value=(
                    "`/kenh-noi-tu` - Đặt kênh hiện tại là kênh Nối Từ\n"
                    "`/kenh-vua-tieng-viet` - Đặt kênh hiện tại là kênh VTV\n"
                    "`/set-game-channel` - Cài đặt nâng cao\n"
                    "`/add-coinz` - Cộng coinz cho thành viên\n"
                    "`/reset-stats` - Reset dữ liệu chơi"
                ),
                inline=False
            )

        elif value == "info":
            embed = discord.Embed(
                title="ℹ️ Thông Tin Bot",
                description="Bot MiniGames Discord - Giải trí và học tập",
                color=config.COLOR_SUCCESS
            )
            embed.add_field(
                name="👨‍💻 Developer",
                value="Quốc Hưng",
                inline=True
            )
            embed.add_field(
                name="🤖 Phiên bản",
                value="2.1.0",
                inline=True
            )
            embed.add_field(
                name="📝 Liên hệ",
                value="Báo lỗi hoặc góp ý trực tiếp cho admin.",
                inline=False
            )

        # Set footer chung
        embed.set_footer(text=f"Bot MiniGames | Prefix: {config.COMMAND_PREFIX}")
        
        # Update message
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpDropdown())


async def setup(bot: commands.Bot):
    """Setup function cho cog"""
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(AdminCog(bot, db))
