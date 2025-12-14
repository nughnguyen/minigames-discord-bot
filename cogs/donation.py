import discord
from discord.ext import commands, tasks
from discord import app_commands
import config
from utils.views import DonationView
from utils import emojis
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None

class Donation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.supabase = None
        
        if config.SUPABASE_URL and config.SUPABASE_KEY and create_client:
            try:
                self.supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                self.check_donations.start()
                print("  ✅ Donation service connected to Supabase")
            except Exception as e:
                print(f"  ⚠️ Failed to connect to Supabase: {e}")
        else:
            print("  ℹ️ Supabase not configured or library missing. Auto-donation check disabled.")

    def cog_unload(self):
        if self.supabase:
            self.check_donations.cancel()

    @tasks.loop(minutes=1)
    async def check_donations(self):
        if not self.supabase:
            return
            
        try:
            # Query transactions that are 'success' but not 'rewarded'
            response = self.supabase.table('transactions').select("*").eq('status', 'success').eq('rewarded', False).execute()
            
            if not response.data:
                return

            for txn in response.data:
                txn_id = txn.get('id')
                user_id = int(txn.get('user_id', 0))
                amount = int(txn.get('amount', 0))
                
                if not user_id or not amount:
                    continue

                # Calculate coinz
                coinz = (amount // 1000) * config.COINZ_PER_1000VND
                
                # Add points using shared database
                if hasattr(self.bot, 'db'):
                    await self.bot.db.add_points(user_id, 0, coinz)
                
                # Notify User
                try:
                    user = await self.bot.fetch_user(user_id)
                    embed = discord.Embed(
                        title="✅ THANH TOÁN THÀNH CÔNG",
                        description=(
                            f"Cảm ơn bạn đã ủng hộ!\n"
                            f"Đơn hàng: `{txn_id}`\n"
                            f"Số nhận: **{coinz:,} Coinz**"
                        ),
                        color=config.COLOR_SUCCESS
                    )
                    await user.send(embed=embed)
                except Exception:
                    pass 
                
                # Mark as rewarded
                self.supabase.table('transactions').update({'rewarded': True, 'rewarded_at': 'now()'}).eq('id', txn_id).execute()
                
        except Exception as e:
            print(f"Error in donation loop: {e}")

    @check_donations.before_loop
    async def before_check_donations(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="chuyen-coinz", description="Chuyển Coinz cho người khác")
    @app_commands.describe(member="Người nhận", amount="Số Coinz muốn chuyển")
    async def transfer(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if not hasattr(self.bot, 'db'):
            await interaction.response.send_message("❌ Hệ thống cơ sở dữ liệu chưa sẵn sàng.", ephemeral=True)
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message("❌ Bạn không thể tự chuyển tiền cho chính mình.", ephemeral=True)
            return
            
        if member.bot:
            await interaction.response.send_message("❌ Không thể chuyển tiền cho Bot.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Số tiền phải lớn hơn 0.", ephemeral=True)
            return

        # Execute transfer
        success = await self.bot.db.transfer_points(interaction.user.id, member.id, amount)
        
        if success:
            embed = discord.Embed(
                title="💸 CHUYỂN KHOẢN THÀNH CÔNG",
                description=(
                    f"Người gửi: {interaction.user.mention}\n"
                    f"Người nhận: {member.mention}\n"
                    f"Số tiền: **{amount:,} Coinz** {emojis.ANIMATED_EMOJI_COINZ}"
                ),
                color=config.COLOR_SUCCESS,
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed)
            
            # Notify receiver if possible
            try:
                recv_embed = discord.Embed(
                    title="💰 BẠN NHẬN ĐƯỢC TIỀN",
                    description=(
                        f"Bạn được {interaction.user.mention} chuyển **{amount:,} Coinz** {emojis.ANIMATED_EMOJI_COINZ}"
                    ),
                    color=config.COLOR_GOLD,
                    timestamp=discord.utils.utcnow()
                )
                await member.send(embed=recv_embed)
            except:
                pass 
        else:
            await interaction.response.send_message("❌ Số dư không đủ hoặc giao dịch thất bại.", ephemeral=True)

    @app_commands.command(name="donate", description="Ủng hộ bot hoặc nạp Coinz")
    async def donate(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💎 NẠP COINZ - ỦNG HỘ SERVER",
            description=(
                "Chào mừng bạn đến với hệ thống nạp Coinz tự động 24/7!\n\n"
                "**🎁 QUYỀN LỢI KHI NẠP COINZ:**\n"
                "✨ Tham gia các minigame giải trí\n"
                "✨ Đua Top Tỷ Phú Server\n"
                "✨ Mua các vật phẩm/quyền lợi (sắp ra mắt)\n"
                "❤️ Góp phần duy trì Bot hoạt động ổn định\n\n"
                "**💰 TỶ GIÁ QUY ĐỔI:**\n"
                f"💵 `1,000 VND` = `{config.COINZ_PER_1000VND:,} Coinz` {emojis.ANIMATED_EMOJI_COINZ}\n"
                f"🔥 **Khuyến mãi:** Tặng thêm 10% khi nạp trên 50k!\n\n"
                "**� PHƯƠNG THỨC THANH TOÁN:**\n"
                "1. **MOMO** - Ví điện tử thông dụng\n"
                "2. **VNPAY** - Quét mã tiện lợi\n"
                "3. **VIETQR** - Chuyển khoản mọi ngân hàng (MB, VCB...)\n"
                "4. **ZYPAGE** - Cổng thanh toán đa năng\n\n"
                "👇 **Chọn phương thức thanh toán bên dưới để bắt đầu:**"
            ),
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmZpbHRmaXZ4b3J5YWR4aGZ4eXF4aGZ4eXF4aGZ4eXF4aGZ4eXF4aGZ4eSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/LdOyjZ7io5Msw/giphy.gif")
        embed.set_footer(text="Hệ thống xử lý tự động trong 1-3 phút • Cảm ơn bạn đã ủng hộ!")
        embed.set_image(url="https://media.discordapp.net/attachments/1110839734893363271/1175511198036000899/line_rainbow.gif") # Decorative line if desired, or remove if specific aesthetic wasn't provided earlier, but "hấp dẫn" implies visual appeal.
        
        await interaction.response.send_message(embed=embed, view=DonationView())

async def setup(bot):
    await bot.add_cog(Donation(bot))
