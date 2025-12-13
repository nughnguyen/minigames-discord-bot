import discord
from discord.ext import commands
from discord import app_commands
import config
from database.db_manager import DatabaseManager

class LobbyCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db

    @app_commands.command(name="start", description="🎮 Bắt đầu game mặc định của kênh")
    async def start_game(self, interaction: discord.Interaction):
        """Bắt đầu game dựa trên cấu hình kênh"""
        game_type = await self.db.get_channel_config(interaction.channel_id)
        
        if not game_type:
             await interaction.response.send_message(
                 "❓ Kênh này chưa được cài đặt game mặc định!\n"
                 "Admin hãy dùng lệnh `/kenh-(ten-game)` để cài đặt.", 
                 ephemeral=True
             )
             return

        if game_type == "wordchain":
            # Call WordChain start command directly
            game_cog = self.bot.get_cog("GameCog")
            if game_cog:
                await game_cog.start_wordchain(interaction, "vi") # Default to vietnamese for normal wordchain
            else:
                await interaction.response.send_message("❌ Lỗi: Game Nối Từ chưa được load.", ephemeral=True)

        elif game_type == "wordchain_en":
            # Call WordChain start command with English
            game_cog = self.bot.get_cog("GameCog")
            if game_cog:
                await game_cog.start_wordchain(interaction, "en")
            else:
                await interaction.response.send_message("❌ Lỗi: Game Nối Từ chưa được load.", ephemeral=True)

        elif game_type == "vuatiengviet":
            # Call Vua Tieng Viet start command
            vtv_cog = self.bot.get_cog("VuaTiengVietCog")
            if vtv_cog:
                 await vtv_cog.start_game(interaction)
            else:
                await interaction.response.send_message("❌ Lỗi: Game Vua Tiếng Việt chưa được load.", ephemeral=True)
        else:
             await interaction.response.send_message("❌ Loại game không hợp lệ.", ephemeral=True)

    @app_commands.command(name="stop", description="🛑 Dừng game hiện tại của kênh")
    async def stop_game(self, interaction: discord.Interaction):
        """Dừng game đang diễn ra"""
        game_type = await self.db.get_channel_config(interaction.channel_id)
        
        if not game_type:
            # Try to stop both just in case, or ask user to be specific.
            # But safer to just say no config.
            # Actually, if the user just wants to stop *whatever* is running, maybe we check active games?
            # Accessing other cogs' active_games is messy.
            # Let's check config first.
             await interaction.response.send_message(
                 "❓ Kênh này chưa được cài đặt game mặc định nên không dùng lệnh chung được.\n"
                 "Hãy liên hệ Admin để cài đặt kênh game.", 
                 ephemeral=True
             )
             return

        if game_type == "wordchain" or game_type == "wordchain_en":
            game_cog = self.bot.get_cog("GameCog")
            if game_cog:
                await game_cog.stop_wordchain(interaction)
            else:
                await interaction.response.send_message("❌ Lỗi cog.", ephemeral=True)

        elif game_type == "vuatiengviet":
            vtv_cog = self.bot.get_cog("VuaTiengVietCog")
            if vtv_cog:
                 await vtv_cog.stop_game(interaction)
            else:
                 await interaction.response.send_message("❌ Lỗi cog.", ephemeral=True)

async def setup(bot: commands.Bot):
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(LobbyCog(bot, db))
