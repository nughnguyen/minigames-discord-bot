import discord
from discord import ui
import config
from utils import emojis
import urllib.parse
import datetime

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

        if amount_val < config.MIN_DONATION_COINZ:
            await interaction.response.send_message(f"❌ Số tiền tối thiểu là {config.MIN_DONATION_COINZ} VND.", ephemeral=True)
            return

        coinz_reward = (amount_val // 1000) * config.COINZ_PER_1000VND
        order_content = f"GUMZ {interaction.user.id}" 
        
        params = {
            'amount': amount_val,
            'content': order_content,
            'method': self.method,
            'userId': interaction.user.id,
            'userName': interaction.user.name
        }
        query_string = urllib.parse.urlencode(params)
        payment_url = f"{config.DONATION_WEB_URL}/payment?{query_string}"
        
        embed = discord.Embed(
            title="💳 Thanh Toán",
            description=(
                f"Bạn đã chọn nạp **{amount_val:,} VND** qua **{self.method}**.\n"
                f"Sẽ nhận được: **{coinz_reward:,} Coinz**\n\n"
                f"**Lưu ý:**\n"
                f"1. Nội dung chuyển khoản phải chính xác: `{order_content}`\n"
                f"2. Sau khi thanh toán thành công, vui lòng chờ 1-3 phút để hệ thống xử lý."
            ),
            color=config.COLOR_INFO,
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        # Create a view with a link button
        view = ui.View()
        view.add_item(ui.Button(label="Thanh Toán Ngay", url=payment_url, style=discord.ButtonStyle.link, emoji="💸"))
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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

    @ui.button(label="ZYPAGE", style=discord.ButtonStyle.secondary, emoji="🌐", row=1)
    async def zypage_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(DonationModal(method="ZYPAGE"))
