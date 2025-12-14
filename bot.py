"""
Author: Developed by QUoc Hung with ❤️
Version: 1.0.0
"""
import discord
from discord.ext import commands
import asyncio
import os

import config
from utils import emojis
from database.db_manager import DatabaseManager

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True


class WordChainBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None  # Sử dụng custom help command
        )
        self.db = DatabaseManager(config.DATABASE_PATH)
    
    async def setup_hook(self):
        """Load all cogs and initialize services"""
        print("🔄 Initializing services...")
        
        # Explicitly remove default help command to prevent conflict
        if self.get_command('help'):
            self.remove_command('help')
            print("  ✅ Removed default help command")
        
        # Initialize Dictionary API Service
        from utils.dictionary_api import init_dictionary_service

        # Initialize Database
        await self.db.initialize()
        print("  ✅ Database initialized")
        
        # Load fallback word lists từ files
        fallback_words = {'vi': set(), 'en': set()}
        
        try:
            with open(config.WORDS_VI_PATH, 'r', encoding='utf-8') as f:
                fallback_words['vi'] = set(line.strip().lower() for line in f if line.strip())
            print(f"  ✅ Loaded {len(fallback_words['vi'])} Vietnamese fallback words")
        except Exception as e:
            print(f"  ⚠️  Could not load Vietnamese words: {e}")
        
        try:
            with open(config.WORDS_EN_PATH, 'r', encoding='utf-8') as f:
                fallback_words['en'] = set(line.strip().lower() for line in f if line.strip())
            print(f"  ✅ Loaded {len(fallback_words['en'])} English fallback words")
        except Exception as e:
            print(f"  ⚠️  Could not load English words: {e}")
        
        # Initialize service với API enabled và fallback words
        await init_dictionary_service(
            use_api=config.USE_DICTIONARY_API,
            fallback_words=fallback_words
        )
        
        if config.USE_DICTIONARY_API:
            print(f"  ✅ Cambridge Dictionary enabled (primary for English)")
            print(f"  ✅ Free Dictionary enabled (backup for English)")
            print(f"  ✅ Tracau API enabled (for Vietnamese)")
        else:
            print(f"  ℹ️  Using local dictionary only")
        
        print("🔄 Loading cogs...")
        
        # Load cogs
        cogs = [
            'cogs.game',
            'cogs.leaderboard',
            'cogs.admin',
            'cogs.vua_tieng_viet',
            'cogs.bau_cua',
            'cogs.lobby',
            'cogs.help',
            'cogs.donation'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"  ✅ Loaded {cog}")
            except Exception as e:
                print(f"  ❌ Failed to load {cog}: {e}")
        
        # Sync commands
        print("🔄 Syncing slash commands...")
        try:
            synced = await self.tree.sync()
            print(f"  ✅ Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"  ❌ Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Bot is ready"""
        print("\n" + "="*50)
        print(f"{emojis.CELEBRATION} Bot is ready!")
        print(f"  👤 Logged in as: {self.user.name}")
        print(f"  🆔 Bot ID: {self.user.id}")
        print(f"  🌍 Servers: {len(self.guilds)}")
        print(f"  👥 Users: {sum(g.member_count for g in self.guilds)}")
        print("="*50 + "\n")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f"Marble Soda | /help"
            ),
            status=discord.Status.online
        )
    
    async def on_guild_join(self, guild: discord.Guild):
        """Bot joins a new server"""
        print(f"{emojis.CELEBRATION} Joined new server: {guild.name} (ID: {guild.id})")
        
        # Tìm kênh hệ thống hoặc kênh text đầu tiên
        channel = guild.system_channel or guild.text_channels[0] if guild.text_channels else None
        
        if channel:
            embed = discord.Embed(
                title=f"{emojis.START} Cảm ơn đã thêm Marble Soda!",
                description=(
                    f"Xin chào {emojis.CELEBRATION}! Tôi là Marble Soda, có rất nhiều trò chơi thú vị.\n\n"
                    f"Để bắt đầu, gõ `/start` trong kênh minigame tương ứng!\n"
                    f"Gõ `/help` để xem hướng dẫn chi tiết."
                ),
                color=config.COLOR_SUCCESS
            )
            
            embed.add_field(
                name=f"{emojis.STAR} Tính Năng Nổi Bật",
                value=(
                    "🇻🇳 Hỗ trợ Tiếng Việt & Tiếng Anh\n"
                    f"{emojis.ROBOT} Chế độ thách đấu Bot\n"
                    f"{emojis.TROPHY} Bảng xếp hạng\n"
                    f"{emojis.HINT} Gợi ý & Powerups"
                ),
                inline=False
            )
            
            try:
                await channel.send(embed=embed)
            except:
                pass  # Không có quyền gửi tin nhắn
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return  # Bỏ qua lệnh không tồn tại
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(f"{emojis.WRONG} Bạn không có quyền sử dụng lệnh này!")
        
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(f"{emojis.WRONG} Bot không có quyền thực hiện hành động này!")
        
        else:
            print(f"❌ Error: {error}")
            await ctx.send(f"{emojis.WRONG} Đã xảy ra lỗi: {str(error)}")


    async def close(self):
        """Cleanup khi bot shutdown"""
        from utils.dictionary_api import close_dictionary_service
        
        print(f"\n{emojis.END} Shutting down...")
        await close_dictionary_service()
        await super().close()


def main():
    """Main function to run the bot"""
    # Check for token
    if not config.DISCORD_TOKEN:
        print(f"{emojis.WRONG} ERROR: Discord token not found!")
        print("Please create a .env file and add your DISCORD_TOKEN")
        print("See .env.example for reference")
        return
    
    # Create data directory if not exists
    os.makedirs('data', exist_ok=True)
    
    # Create and run bot
    bot = WordChainBot()
    
    try:
        print(f"{emojis.START} Starting Word Chain Bot...")
        print(f"  📝 Loading configuration...")
        print(f"  🗄️  Database: {config.DATABASE_PATH}")
        print(f"  🌍 Default Language: {config.DEFAULT_LANGUAGE}")
        print(f"  ⏰ Turn Timeout: {config.TURN_TIMEOUT}s")
        print()
        
        bot.run(config.DISCORD_TOKEN)
    
    except discord.LoginFailure:
        print(f"{emojis.WRONG} ERROR: Invalid Discord token!")
        print("Please check your DISCORD_TOKEN in .env file")
    
    except KeyboardInterrupt:
        print(f"\n{emojis.END} Bot stopped by user")
    
    except Exception as e:
        print(f"{emojis.WRONG} ERROR: {e}")


if __name__ == "__main__":
    main()
