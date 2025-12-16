import discord
import asyncio
from discord import ui
import config
from utils import emojis
import urllib.parse
import datetime
import random
import time
SUPABASE_IMPORT_ERROR = None
try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import supabase in views.py: {e}")
    SUPABASE_IMPORT_ERROR = str(e)
    create_client = None


class DonationModal(ui.Modal):
    def __init__(self, method: str):
        super().__init__(title=f"Nạp qua {method}")
        self.method = method
        self.amount = ui.TextInput(
            label="Số tiền (VND)",
            placeholder="VD: 10000",
            min_length=4,
            max_length=10,
            required=True
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount_val = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Số tiền không hợp lệ. Vui lòng nhập số.", ephemeral=True)
            return

        if amount_val < config.MIN_DONATION_COIZ:
            await interaction.response.send_message(f"❌ Số tiền tối thiểu là {config.MIN_DONATION_COIZ} VND.", ephemeral=True)
            return

        # Generate Unique Order Code
        rand_code = random.randint(100000, 999999)
        order_content = f"GUMZ{rand_code}"
        
        # Calculate Rewards and Expiry
        coiz_reward = (amount_val // 1000) * config.COIZ_PER_1000VND
        expiry_seconds = 600 # 10 minutes
        expiry_time = discord.utils.utcnow() + datetime.timedelta(seconds=expiry_seconds)
        expiry_timestamp = int(expiry_time.timestamp())
        
        # Insert Pending Transaction to Supabase
        if not (config.SUPABASE_URL and config.SUPABASE_KEY and create_client):
             print(f"DEBUG: Supabase Config Error. URL={bool(config.SUPABASE_URL)}, Key={bool(config.SUPABASE_KEY)}, Lib={bool(create_client)}")
             error_msg = f"❌ Lỗi hệ thống: Bot chưa tải được thư viện Supabase.\nLỗi chi tiết: `{SUPABASE_IMPORT_ERROR}`"
             if not config.SUPABASE_KEY: error_msg += "\n(Thiếu KEY)"
             await interaction.response.send_message(error_msg, ephemeral=True)
             return

        try:
            sb = create_client(config.SUPABASE_URL.strip(), config.SUPABASE_KEY.strip())
            sb.table('transactions').insert({
                'user_id': interaction.user.id,
                'amount': amount_val,
                'description': order_content,
                'status': 'pending',
                'created_at': datetime.datetime.now().isoformat(),
                'metadata': {'method': self.method}
            }).execute()
        except Exception as e:
            print(f"Error creating pending txn: {e}")
            await interaction.response.send_message(f"❌ Không thể tạo đơn hàng: {e}", ephemeral=True)
            return
        
        params = {
            'amount': amount_val,
            'content': order_content,
            'method': self.method,
            'userId': interaction.user.id,
            'userName': interaction.user.name,
            'expiry': expiry_timestamp
        }
        query_string = urllib.parse.urlencode(params)
        payment_url = f"{config.DONATION_WEB_URL}/payment?{query_string}"
        
        embed = discord.Embed(
            title="💳 Thanh Toán",
            description=(
                f"Bạn đã chọn nạp **{amount_val:,} VND** qua **{self.method}**.\n"
                f"Sẽ nhận được: **{coiz_reward:,} Coiz** {emojis.ANIMATED_EMOJI_COIZ}\n\n"
                f"**⚠️ LƯU Ý QUAN TRỌNG:**\n"
                f"1. Nội dung chuyển khoản: `{order_content}`\n"
                f"2. Thời gian còn lại: <t:{expiry_timestamp}:R> (Hết hạn lúc <t:{expiry_timestamp}:T>)\n"
                f"3. Nếu chuyển khoản khi hết hạn: **KHÔNG ĐƯỢC TÍNH** & **KHÔNG CHỊU TRÁCH NHIỆM**."
            ),
            color=config.COLOR_INFO,
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.set_footer(text="Vui lòng quét mã QR trên web để đảm bảo chính xác nhất.")
        
        # Create a view with a link button
        view = ui.View()
        view.add_item(ui.Button(label="THANH TOÁN NGAY", url=payment_url, style=discord.ButtonStyle.link, emoji="💸"))
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        # Start background task to monitor transaction status
        asyncio.create_task(monitor_transaction(interaction, order_content, expiry_seconds))

async def monitor_transaction(interaction: discord.Interaction, order_code: str, duration: int):
    # Initialize Supabase client for this task
    sb = None
    if config.SUPABASE_URL and config.SUPABASE_KEY and create_client:
        try:
            sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        except Exception as e:
            print(f"Error initializing Supabase in monitor: {e}")

    end_time = time.time() + duration
    
    while time.time() < end_time:
        if sb:
            try:
                # Check status
                response = sb.table('transactions').select("status, amount").eq('description', order_code).execute()
                if response.data:
                    data = response.data[0]
                    status = data.get('status')
                    
                    if status == 'success':
                        amount = data.get('amount', 0)
                        coiz = (amount // 1000) * config.COIZ_PER_1000VND
                        
                        embed = discord.Embed(
                            title=f"{emojis.TADA_LEFT} THANH TOÁN THÀNH CÔNG {emojis.TADA_RIGHT}",
                            description=(
                                f"Cảm ơn bạn đã ủng hộ!\n"
                                f"Đơn hàng: `{order_code}`\n"
                                f"Đã nạp: **{amount:,} VND**\n"
                                f"Nhận được: **{coiz:,} Coiz** {emojis.ANIMATED_EMOJI_COIZ}"
                            ),
                            color=config.COLOR_SUCCESS,
                            timestamp=discord.utils.utcnow()
                        )
                        embed.set_footer(text="Giao dịch hoàn tất.")
                        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1110839734893363271/1175511198036000899/line_rainbow.gif") # Re-using a celebratory gif if appropriate or just keeping it clean
                        
                        # Remove buttons
                        await interaction.edit_original_response(embed=embed, view=None)
                        return
            except Exception as e:
                print(f"Error checking transaction status: {e}")
        
        await asyncio.sleep(5) # Check every 5 seconds

    # If loop finishes without success -> Expire
    try:
        embed = discord.Embed(
            title="⚠️ GIAO DỊCH HẾT HẠN",
            description=(
                f"Mã đơn: `{order_code}`\n"
                f"Đã quá thời gian thanh toán (10 phút).\n"
                f"Giao dịch này không còn hiệu lực. Vui lòng tạo lệnh mới."
            ),
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Giao dịch đã bị hủy tự động.")
        
        await interaction.edit_original_response(embed=embed, view=None)
    except Exception as e:
        print(f"Error expiring transaction embed: {e}")

class DonationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="MOMO", style=discord.ButtonStyle.primary, emoji=emojis.EMOJI_MOMO_PAY if hasattr(emojis, 'EMOJI_MOMO_PAY') else "💸", row=0)
    async def momo_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DonationModal(method="MOMO"))

    @ui.button(label="VNPAY", style=discord.ButtonStyle.primary, emoji="💳", row=0)
    async def vnpay_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DonationModal(method="VNPAY"))

    @ui.button(label="VIETQR", style=discord.ButtonStyle.success, emoji="🏦", row=1)
    async def vietqr_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DonationModal(method="VIETQR"))

class RegistrationView(ui.View):
    def __init__(self, host_id: int, timeout: float):
        super().__init__(timeout=timeout)
        self.host_id = host_id
        self.registered_players = {host_id} # Host auto-registered
        self.game_started = False

    @ui.button(label="📝 Đăng Ký", style=discord.ButtonStyle.success, emoji="✅")
    async def join_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id in self.registered_players:
            await interaction.response.send_message("Bạn đã đăng ký rồi!", ephemeral=True)
            return
        
        self.registered_players.add(interaction.user.id)
        await self.update_embed(interaction)
        await interaction.response.send_message("Đăng ký thành công!", ephemeral=True)

    @ui.button(label="❌ Hủy", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def leave_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id not in self.registered_players:
            await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)
            return
        
        if interaction.user.id == self.host_id:
             await interaction.response.send_message("Chủ phòng không thể hủy đăng ký! Hãy đợi hết giờ hoặc bắt đầu solo.", ephemeral=True)
             return

        self.registered_players.remove(interaction.user.id)
        await self.update_embed(interaction)
        await interaction.response.send_message("Đã hủy đăng ký!", ephemeral=True)

    @ui.button(label="🎮 Bắt Đầu", style=discord.ButtonStyle.primary, emoji="🚀")
    async def start_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("Chỉ chủ phòng mới được bắt đầu game!", ephemeral=True)
            return
        
        self.game_started = True
        self.stop()
        await interaction.response.defer()

    async def update_embed(self, interaction: discord.Interaction):
        try:
            embed = interaction.message.embeds[0]
            # Format player list nicely
            players = []
            for uid in self.registered_players:
                players.append(f"<@{uid}>")
                
            player_list_str = "\n".join(players)
            
            # Field 0 is assumed to be the player list based on game.py
            embed.set_field_at(0, name=f"👥 Đã Đăng Ký ({len(self.registered_players)} người)", value=player_list_str, inline=False)
            
            await interaction.message.edit(embed=embed)
        except Exception as e:
            print(f"Error updating registration embed: {e}")


