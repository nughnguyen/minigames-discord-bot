import discord
from discord.ext import commands
from discord import app_commands
import platform
import datetime
from utils import emojis
import config

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.bot = bot
        
        # Link Buttons
        self.add_item(discord.ui.Button(
            label="Website", 
            style=discord.ButtonStyle.link, 
            url="https://quochung.id.vn", 
            emoji=emojis.EMOJI_LINK
        ))
        self.add_item(discord.ui.Button(
            label="Support Server", 
            style=discord.ButtonStyle.link, 
            url="https://dsc.gg/thenoicez", 
            emoji=emojis.EMOJI_DISCORD
        ))
        self.add_item(discord.ui.Button(
            label="Invite", 
            style=discord.ButtonStyle.link, 
            url="https://discord.com/oauth2/authorize?client_id=1305035261897343026&permissions=8&integration_type=0&scope=bot", 
            emoji=emojis.EMOJI_INVITE # Facebook or generic website emoji
        ))

    @discord.ui.select(
        placeholder="Marble Soda Menu",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Games Commands", description="Word Chain, Vua Tiếng Việt, Bầu Cua", emoji="🎮"),
            discord.SelectOption(label="Leaderboard Commands", description="View rankings", emoji="🏆"),
            discord.SelectOption(label="Admin Commands", description="Admin tools", emoji="🛡️"),
            discord.SelectOption(label="Utility Commands", description="Bot info & others", emoji="🛠️"),
            discord.SelectOption(label="Donation", description="Support the bot", emoji=emojis.EMOJI_MOMO_PAY),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        
        embed = discord.Embed(
            title=f"{choice}",
            color=config.COLOR_INFO,
            timestamp=datetime.datetime.now()
        )
        
        if choice == "Games Commands":
            embed.description = "Hướng dẫn chi tiết các trò chơi:"
            
            # Word Chain Info
            embed.add_field(
                name="🔤 **Nối Từ (Word Chain)**",
                value=(
                    f"• **Luật chơi**: Nối tiếp từ bắt đầu bằng chữ cái cuối của từ trước.\n"
                    f"• **Lệnh**:\n"
                    f"  `/start` - Bắt đầu game\n"
                    f"  `/stop` - Dừng game (Kết thúc & trao giải)\n"
                    f"  `/challenge-bot` - ⚔️ Thách đấu Bot (Solo)\n"
                    f"• **Hỗ trợ**:\n"
                    f"  `/hint` - Gợi ý nhận ký tự tiếp theo ({config.HINT_COST} coinz)\n"
                    f"  `/pass` - Bỏ lượt an toàn ({config.PASS_COST} coinz)\n"
                    f"• **Điểm Thưởng & Phạt**:\n"
                    f"  ✅ **Đúng**: +10 coinz (+Bonus Level/Từ dài)\n"
                    f"  ⚡ **Tốc độ**: <5s (+100), <10s (+50), <20s (+20)\n"
                    f"  ❌ **Sai**: -2 coinz/lần (Tối đa 5 lần/lượt)\n"
                    f"  🐌 **Timeout**: -10 coinz (Mất lượt)"
                ),
                inline=False
            )
            
            # Vua Tieng Viet Info
            embed.add_field(
                name="👑 **Vua Tiếng Việt**",
                value=(
                    f"• **Luật chơi**: Sắp xếp ký tự bị xáo trộn thành từ có nghĩa.\n"
                    f"• **Lệnh**:\n"
                    f"  `/start` - Bắt đầu game tại kênh VTV\n"
                    f"  `/stop` - Dừng game\n"
                    f"• **Cách chơi**: Gõ đáp án trực tiếp vào chat.\n"
                    f"• **Phần thưởng**: Từ {config.POINTS_VUA_TIENG_VIET:,} đến {config.POINTS_VUA_TIENG_VIET_SIEU_KHO:,} coinz (Tùy độ khó)!"
                ),
                inline=False
            )

            # Bau Cua Info
            embed.add_field(
                name="🎲 **Bầu Cua Tôm Cá (Space Edition)**",
                value=(
                    f"• **Luật chơi**: Đặt cược vào 6 cửa (Nai, Bầu, Mèo, Cá, Cua, Tôm).\n"
                    f"• **Lệnh**:\n"
                    f"  `/start` - Bắt đầu game tại kênh Bầu Cua\n"
                    f"• **Cách chơi**: Dùng các nút bấm để đặt cược (Max 500k/lần).\n"
                    f"• **Tỷ lệ thắng**: x1, x2, x3 tùy số mặt xúc xắc xuất hiện."
                ),
                inline=False
            )

        elif choice == "Leaderboard Commands":
            embed.description = "Xem bảng xếp hạng người chơi:"
            embed.add_field(
                name="📊 **Thống Kê**",
                value=(
                    "`/leaderboard` - Xem Top Server\n"
                    "`/stats [user]` - Xem thông tin cá nhân (Rank, Coinz, WinRate...)"
                ),
                inline=False
            )
            
        elif choice == "Admin Commands":
            embed.description = "Các lệnh quản lý (chỉ dành cho Admin):"
            embed.add_field(
                name="⚙️ **Cài Đặt Game**",
                value=(
                    "`/kenh-noi-tu-vn` - Set kênh Nối Từ (VN)\n"
                    "`/kenh-noi-tu-en` - Set kênh Nối Từ (EN)\n"
                    "`/kenh-vua-tieng-viet` - Set kênh VTV\n"
                    "`/kenh-bau-cua` - Set kênh Bầu Cua\n"
                    "`/set-game-channel` - Cài đặt nâng cao"
                ),
                inline=False
            )
            embed.add_field(
                name="💰 **Quản Lý Coinz/Stats**",
                value=(
                    "`/add-coinz [user] [amount]` - Cộng coinz\n"
                    "`/subtract-coinz [user] [amount]` - Trừ coinz\n"
                    "`/reset-coinz [user]` - Set coinz về 0\n"
                    "`/reset-stats [user]` - Reset toàn bộ chỉ số game"
                ),
                inline=False
            )
            
        elif choice == "Utility Commands":
            embed.description = "Thông tin khác về Bot:"
            embed.add_field(
                name="ℹ️ **Thông Tin**",
                value=(
                    f"• **Developer**: Quốc Hưng\n"
                    f"• **Prefix**: `{config.COMMAND_PREFIX}`\n"
                    f"• **Version**: 2.2.0"
                ),
                inline=False
            )
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Hiển thị menu hướng dẫn")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="HELP MENU",
            color=0x2b2d31, # Dark background color
            timestamp=datetime.datetime.now()
        )
        
        # Bot Info
        embed.add_field(
            name=f"{emojis.ANIMATED_EMOJI_DISCORD} **BOT INFO** {emojis.ANIMATED_EMOJI_DISCORD}",
            value=f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Prefix: `{config.COMMAND_PREFIX}`",
            inline=False
        )
        
        # Bot's Commands (listing categories)
        commands_list = (
            f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Games Commands\n"
            f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Leaderboard Commands\n"
            f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Admin Commands\n"
            f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Utility Commands"
        )
            
        embed.add_field(
            name=f"{emojis.ANIMATED_EMOJI_DISCORD} **BOT'S COMMANDS** {emojis.ANIMATED_EMOJI_DISCORD}",
            value=commands_list,
            inline=False
        )
        
        # Bot's Status
        ping = round(self.bot.latency * 1000)
        server_count = len(self.bot.guilds)
        user_count = sum(guild.member_count for guild in self.bot.guilds)
        # Count app commands (slash commands) since most are app_commands
        command_count = len(self.bot.tree.get_commands())
        
        status_text = (
            f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Current Ping: {ping}ms\n"
            f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Total Commands: {command_count}\n"
            f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Total Users: {user_count}\n"
            f"{emojis.BAR} {emojis.ANIMATED_EMOJI_DOT} Total Servers: {server_count}"
        )
        
        embed.add_field(
            name=f"{emojis.ANIMATED_EMOJI_DISCORD} **BOT'S STATUS** {emojis.ANIMATED_EMOJI_DISCORD}",
            value=status_text,
            inline=False
        )
        
        # Image banner if available in config or user preference, otherwise skip or add empty field
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        view = HelpView(self.bot)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Help(bot))
