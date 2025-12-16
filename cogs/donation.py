import discord
from discord.ext import commands, tasks
from discord import app_commands
import config
from utils.views import DonationView
from utils import emojis
try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import supabase in donation.py: {e}")
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
            
            if response.data:
                for txn in response.data:
                    txn_id = txn.get('id')
                    user_id = int(txn.get('user_id', 0))
                    amount = int(txn.get('amount', 0))
                    
                    order_code = txn.get('description', 'N/A')
                    
                    if not user_id or not amount:
                        continue

                    # Calculate coinz
                    base_coinz = (amount // 1000) * config.COINZ_PER_1000VND
                    
                    # Calculate Bonus
                    bonus_coinz = 0
                    if amount >= 500000:
                        bonus_coinz = 2000000
                    elif amount >= 200000:
                        bonus_coinz = 500000
                    elif amount >= 100000:
                        bonus_coinz = 200000
                    elif amount >= 50000:
                        bonus_coinz = 50000
                        
                    total_coinz = base_coinz + bonus_coinz
                    
                    # Add points using shared database
                    if hasattr(self.bot, 'db'):
                        await self.bot.db.add_points(user_id, 0, total_coinz)
                        
                        # Check for Donator Rod reward (>= 10k VND)
                        if amount >= 10000:
                            try:
                                # Safe import or string usage
                                rod_key = "Donator Rod"
                                data = await self.bot.db.get_fishing_data(user_id)
                                inv = data.get("inventory", {})
                                
                                # Ensure 'rods' list exists
                                if "rods" not in inv: 
                                    inv["rods"] = ["Plastic Rod"] # Default
                                    
                                if rod_key not in inv["rods"]:
                                    inv["rods"].append(rod_key)
                                    await self.bot.db.update_fishing_data(user_id, inventory=inv)
                                    
                                    # Notify
                                    try:
                                        u = await self.bot.fetch_user(user_id)
                                        await u.send(f"🎣 **QUÀ TẶNG:** Bạn đã nhận được **Cần Nhà Tài Trợ** (Donator Rod) nhờ donate > 10k!")
                                    except:
                                        pass
                            except Exception as e:
                                print(f"Error giving Donator Rod: {e}")
                    
                    # Notify User
                    try:
                        user = await self.bot.fetch_user(user_id)
                        
                        desc = (
                            f"Cảm ơn bạn đã ủng hộ!\n"
                            f"Đơn hàng: `{txn_id}`\n"
                            f"Nội dung: `{order_code}`\n"
                            f"Số nhận: **{total_coinz:,} Coinz** {emojis.ANIMATED_EMOJI_COINZ}"
                        )
                        
                        if bonus_coinz > 0:
                            desc += f"\n*(Gốc: {base_coinz:,} + Bonus: {bonus_coinz:,})*"
                            
                        embed = discord.Embed(
                            title="✅ THANH TOÁN THÀNH CÔNG",
                            description=desc,
                            color=config.COLOR_SUCCESS
                        )
                        await user.send(embed=embed)
                    except Exception:
                        pass 
                    
                    # Mark as rewarded
                    self.supabase.table('transactions').update({'rewarded': True, 'rewarded_at': 'now()'}).eq('id', txn_id).execute()

            # Query 'late_payment' transactions
            response_late = self.supabase.table('transactions').select("*").eq('status', 'late_payment').eq('rewarded', False).execute()
            
            if response_late.data:
                for txn in response_late.data:
                    txn_id = txn.get('id')
                    user_id = int(txn.get('user_id', 0))
                    amount = int(txn.get('amount', 0))
                    
                    if not user_id: continue

                    # Notify User
                    try:
                        user = await self.bot.fetch_user(user_id)
                        embed = discord.Embed(
                            title="⚠️ GIAO DỊCH QUÁ HẠN",
                            description=(
                                f"Hệ thống ghi nhận khoản chuyển **{amount:,} VND**.\n"
                                f"Tuy nhiên, giao dịch này thực hiện **sau 10 phút** kể từ khi tạo lệnh.\n"
                                f"Vậy nên chúng tôi không có trách nhiệm nếu giao dịch này không được tính."
                            ),
                            color=discord.Color.red()
                        )
                        await user.send(embed=embed)
                    except Exception:
                        pass
                    
                    # Mark as rewarded/handled
                    self.supabase.table('transactions').update({'rewarded': True, 'rewarded_at': 'now()'}).eq('id', txn_id).execute()

        except Exception as e:
            print(f"Error in donation loop: {e}")
            
        # Cleanup expired pending transactions (> 10 minutes)
        try:
            from datetime import datetime, timedelta, timezone
            
            # Calculate threshold (10 minutes ago)
            # Assuming timestamps are stored in UTC
            threshold = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
            
            # Delete pending transactions older than 15 minutes
            # We delete them to keep the DB clean. 
            # If a late payment comes in, the Webhook handles it by creating a new success record.
            self.supabase.table('transactions').delete().eq('status', 'pending').lt('created_at', threshold).execute()
            
            # Also cleanup any 'expired' status rows if they exist
            self.supabase.table('transactions').delete().eq('status', 'expired').execute()
            
        except Exception as e:
            print(f"Error cleaning up expired transactions: {e}")

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
            title=f"💎 NẠP COINZ | ỦNG HỘ SERVER",
            description=(
                f"Chào mừng bạn đến với hệ thống nạp Coinz tự động 24/7!\n\n"
                f"**🎁 QUYỀN LỢI KHI NẠP COINZ**\n"
                "✨ Tham gia các minigame giải trí\n"
                "✨ Đua Top Tỷ Phú Server\n"
                "✨ Mua các vật phẩm/quyền lợi (sắp ra mắt)\n"
                "❤️ Góp phần duy trì Bot hoạt động ổn định\n\n"
                "**💰 TỶ GIÁ QUY ĐỔI:**\n"
                f"💵 `1,000 VND` = `{config.COINZ_PER_1000VND:,} Coinz` {emojis.ANIMATED_EMOJI_COINZ}\n"
                f"🔥 **Khuyến mãi:** Tặng thêm 10% khi nạp trên 50k!\n"
                f"🎣 **Đặc biệt:** Nạp tối thiểu **10,000 VND** nhận ngay **Cần Nhà Tài Trợ** (Donator Rod)!\n\n"
                "**💳 PHƯƠNG THỨC THANH TOÁN:**\n"
                "1. **MOMO** - Ví điện tử thông dụng\n"
                "2. **VNPAY** - Quét mã tiện lợi\n"
                "3. **VIETQR** - Chuyển khoản mọi ngân hàng (MB, VCB, OCB...)\n\n"
                "👇 **Chọn phương thức thanh toán bên dưới để bắt đầu:**"
            ),
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmZpbHRmaXZ4b3J5YWR4aGZ4eXF4aGZ4eXF4aGZ4eXF4aGZ4eXF4aGZ4eSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/LdOyjZ7io5Msw/giphy.gif")
        embed.set_footer(text="Hệ thống xử lý tự động trong vài giây • Cảm ơn bạn đã ủng hộ!")
        embed.set_image(url="https://cdn.discordapp.com/attachments/1305556786304127097/1327687391267389632/thenoicez.gif?ex=6940eafd&is=693f997d&hm=332f39b7a027ecfebdead2cd326f57c1502020fff8922b78c8fdb623fa49a43b&") # Decorative line if desired, or remove if specific aesthetic wasn't provided earlier, but "hấp dẫn" implies visual appeal.
        
        await interaction.response.send_message(embed=embed, view=DonationView())

async def setup(bot):
    await bot.add_cog(Donation(bot))
