import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import json
from typing import Optional, Dict
import config
from utils import emojis
from database.db_manager import DatabaseManager

# --- CONSTANTS ---

FISH_TYPES = [
    "Fish", "Salmon", "Cod", "Tropical Fish", "Pufferfish", 
    "Fiery Pufferfish", "Volcanic Fish", "Turtle", "Squid", "Dolphin"
]

FISH_DATA = {
    "Fish":             {"value": 1,    "xp": 0.25, "min_quality": 1},
    "Salmon":           {"value": 3,    "xp": 1,    "min_quality": 2},
    "Cod":              {"value": 10,   "xp": 2,    "min_quality": 3},
    "Tropical Fish":    {"value": 30,   "xp": 5,    "min_quality": 4},
    "Pufferfish":       {"value": 80,   "xp": 10,   "min_quality": 5},
    "Fiery Pufferfish": {"value": 200,  "xp": 20,   "min_quality": 6},
    "Volcanic Fish":    {"value": 480,  "xp": 40,   "min_quality": 7},
    "Turtle":           {"value": 1000, "xp": 75,   "min_quality": 8},
    "Squid":            {"value": 2500, "xp": 120,  "min_quality": 9},
    "Dolphin":          {"value": 6000, "xp": 150,  "min_quality": 10}
}

RODS = {
    "Plastic Rod":    {"price": 0,       "mul_qty": 1.1,  "add_qual": 0.3},
    "Improved Rod":   {"price": 500,     "mul_qty": 1.15, "add_qual": 0.6},
    "Greater Rod":    {"price": 1500,    "mul_qty": 1.25, "add_qual": 1.0},
    "Fiberglass Rod": {"price": 3500,    "mul_qty": 1.35, "add_qual": 1.4},
    "Lava Rod":       {"price": 7500,    "mul_qty": 1.5,  "add_qual": 1.7},
    "Magma Rod":      {"price": 15000,   "mul_qty": 1.75, "add_qual": 2.0},
    "Oceanic Rod":    {"price": 30000,   "mul_qty": 2.0,  "add_qual": 2.3},
    "Aquatic Rod":    {"price": 75000,   "mul_qty": 2.5,  "add_qual": 2.6},
    "Golden Rod":     {"price": 150000,  "mul_qty": 3.0,  "add_qual": 3.0},
    "Treasure Rod":   {"price": 500000,  "mul_qty": 1.0,  "add_qual": 0.0, "treasure_mul": 2.0} # Special
}

# Ordered list for shop logic
ROD_LIST = list(RODS.keys())

# Upgrade costs (Simple list for "More Fish" for now, scalable later)
UPGRADE_COSTS = {
    "More Fish": [200, 500, 1500, 5000, 12500, 30000, 75000, 200000, 500000, 1500000]
}

class ShopView(discord.ui.View):
    def __init__(self, cog, user_id, current_rod, money):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.current_rod = current_rod
        self.money = money
        self.message = None

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        # Determine next rod
        try:
            curr_idx = ROD_LIST.index(self.current_rod)
        except ValueError:
            curr_idx = 0
            
        if curr_idx < len(ROD_LIST) - 1:
            next_rod = ROD_LIST[curr_idx + 1]
            price = RODS[next_rod]["price"]
            can_afford = self.money >= price
            
            btn = discord.ui.Button(
                label=f"Mua {next_rod} ({price:,} Coinz 🪙)",
                style=discord.ButtonStyle.success if can_afford else discord.ButtonStyle.secondary,
                disabled=not can_afford,
                custom_id="buy_rod",
                emoji="🎣"
            )
            btn.callback = self.buy_rod_callback
            self.add_item(btn)
        else:
            self.add_item(discord.ui.Button(label="Đã sở hữu cần câu tốt nhất!", disabled=True))

    async def buy_rod_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return

        try:
            curr_idx = ROD_LIST.index(self.current_rod)
            next_rod = ROD_LIST[curr_idx + 1]
            price = RODS[next_rod]["price"]

            await self.cog.db.add_points(interaction.user.id, interaction.guild_id, -price)
            await self.cog.db.update_fishing_data(interaction.user.id, rod_type=next_rod)
            
            self.current_rod = next_rod
            self.money -= price
            self.update_buttons()
            
            await interaction.response.edit_message(
                content=f"✅ Bạn đã mua **{next_rod}** thành công!",
                view=self
            )
        except Exception as e:
            await interaction.response.send_message(f"Có lỗi xảy ra: {e}", ephemeral=True)


class CauCaCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db

    async def get_current_channel_game(self, channel_id):
        return await self.db.get_channel_config(channel_id)

    @app_commands.command(name="kenh-cau-ca", description="Set kênh hiện tại làm kênh câu cá")
    @app_commands.checks.has_permissions(administrator=True)
    async def kenh_cau_ca(self, interaction: discord.Interaction):
        """Đặt kênh hiện tại làm kênh chuyên câu cá"""
        await self.db.set_channel_config(interaction.channel_id, interaction.guild_id, "fishing")
        await interaction.response.send_message(
            f"✅ Đã đặt kênh {interaction.channel.mention} làm kênh **Câu Cá**! 🎣",
            ephemeral=False
        )

    @app_commands.command(name="fish", description="Câu cá (yêu cầu đặt kênh câu cá)")
    async def fish(self, interaction: discord.Interaction):
        # 1. Check channel
        game_type = await self.get_current_channel_game(interaction.channel_id)
        if game_type != "fishing":
            await interaction.response.send_message(
                "❌ Kênh này chưa được thiết lập để câu cá! Admin hãy dùng `/kenh-cau-ca` để cài đặt.",
                ephemeral=True
            )
            return

        # 2. Get User Data
        user_id = interaction.user.id
        data = await self.db.get_fishing_data(user_id)
        
        rod_name = data.get("rod_type", "Plastic Rod")
        rod_stats = RODS.get(rod_name, RODS["Plastic Rod"])
        
        # Base stats
        base_quantity = 1.0
        base_quality = 1.1
        
        # Apply Rod Multipliers
        quantity_mul = rod_stats.get("mul_qty", 1.0)
        quality_add = rod_stats.get("add_qual", 0.0)
        
        final_quantity_val = base_quantity * quantity_mul
        final_quality = base_quality + quality_add
        
        # Calculate rolls
        min_rolls = int(final_quantity_val * 5)
        max_rolls = int(final_quantity_val * 10)
        rolls = random.randint(min_rolls, max_rolls)
        
        # Fishing Logic
        caught_fish = {} # {FishName: Count}
        total_xp_gain = 0
        new_items = [] # For treasures/crates if implemented later
        
        for _ in range(rolls):
            # Roll quality for this fish
            # Chance to upgrade quality tier by 1 based on decimal part
            # e.g. quality 1.4 -> base 1, 40% chance to be 2
            current_quality_roll = int(final_quality)
            if random.random() < (final_quality % 1):
                current_quality_roll += 1
            
            # Map quality directly to fish index (1-based from original script logic roughly)
            # Original: 1=Fish, 2=Salmon, ...
            # Let's clamp it
            if current_quality_roll < 1: current_quality_roll = 1
            if current_quality_roll > 10: current_quality_roll = 10
            
            fish_name = FISH_TYPES[current_quality_roll - 1]
            
            caught_fish[fish_name] = caught_fish.get(fish_name, 0) + 1
            total_xp_gain += FISH_DATA[fish_name]["xp"]

        # Update Inventory
        inventory = data.get("inventory", {})
        for fname, fcount in caught_fish.items():
            inventory[fname] = inventory.get(fname, 0) + fcount
            
        # Update Stats (XP)
        stats = data.get("stats", {})
        stats["xp"] = stats.get("xp", 0) + total_xp_gain
        
        # Save to DB
        await self.db.update_fishing_data(user_id, inventory=inventory, stats=stats)
        
        # Embed Result
        embed = discord.Embed(
            title="🎣 KẾT QUẢ CÂU CÁ",
            color=discord.Color.blue()
        )
        
        details = []
        for fname, fcount in caught_fish.items():
            details.append(f"**{fcount}** {fname}")
        
        if not details:
           desc = "Bạn không câu được gì cả... (Xui xẻo thật!)"
        else:
           desc = ", ".join(details)
           
        embed.description = f"Bạn đã câu được:\n{desc}\n\n✨ **+{int(total_xp_gain)} XP**"
        embed.set_footer(text=f"Cần câu: {rod_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="Xem túi cá của bạn")
    async def inventory(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        data = await self.db.get_fishing_data(user_id)
        inventory = data.get("inventory", {})
        
        if not inventory or sum(inventory.values()) == 0:
            await interaction.response.send_message("🎒 Túi của bạn đang trống! Hãy đi câu cá ngay (`/fish`).", ephemeral=True)
            return
            
        embed = discord.Embed(title=f"🎒 Túi Cá Của {interaction.user.display_name}", color=discord.Color.green())
        
        # Sort by value
        sorted_items = sorted(inventory.items(), key=lambda x: FISH_DATA.get(x[0], {}).get("value", 0), reverse=True)
        
        desc_lines = []
        total_value = 0
        
        for fname, count in sorted_items:
            if count > 0:
                val_per = FISH_DATA.get(fname, {}).get("value", 0)
                total_val = val_per * count
                total_value += total_val
                desc_lines.append(f"• **{fname}**: {count} (Trị giá: {total_val:,} Coinz {emojis.ANIMATED_EMOJI_COINZ})")
                
        embed.description = "\n".join(desc_lines)
        embed.add_field(name="💰 Tổng Giá Trị", value=f"**{total_value:,}** Coinz {emojis.ANIMATED_EMOJI_COINZ}", inline=False)
        embed.set_footer(text="Dùng /sell để bán tất cả cá.")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="Bán tất cả cá trong túi")
    async def sell(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        data = await self.db.get_fishing_data(user_id)
        inventory = data.get("inventory", {})
        
        if not inventory or sum(inventory.values()) == 0:
            await interaction.response.send_message("🎒 Bạn không có cá để bán!", ephemeral=True)
            return
            
        total_payout = 0
        sold_details = []
        
        for fname, count in inventory.items():
            if count > 0:
                val = FISH_DATA.get(fname, {}).get("value", 0)
                total_payout += val * count
                sold_details.append(f"{count} {fname}")
                inventory[fname] = 0 # Clear item
        
        # Update DB
        if total_payout > 0:
            await self.db.add_points(user_id, interaction.guild_id, total_payout)
            await self.db.update_fishing_data(user_id, inventory=inventory)
            
            embed = discord.Embed(title="💰 BÁN CÁ", color=discord.Color.gold())
            embed.description = f"Bạn đã bán tất cả cá và nhận được **{total_payout:,}** Coinz {emojis.ANIMATED_EMOJI_COINZ}!"
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Lỗi tính toán giá trị bán.", ephemeral=True)

    @app_commands.command(name="shop", description="Cửa hàng cần câu")
    async def shop(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        points = await self.db.get_player_points(user_id, interaction.guild_id)
        data = await self.db.get_fishing_data(user_id)
        current_rod = data.get("rod_type", "Plastic Rod")
        
        embed = discord.Embed(title="🏪 Cửa Hàng Đồ Câu", color=discord.Color.purple())
        embed.description = f"Số dư của bạn: **{points:,}** Coinz {emojis.ANIMATED_EMOJI_COINZ}\nCần câu hiện tại: **{current_rod}**"
        
        # Show rod list
        rod_desc = ""
        for name, stats in RODS.items():
            price = stats["price"]
            rod_desc += f"• **{name}**: {price:,} Coinz {emojis.ANIMATED_EMOJI_COINZ}\n"
        
        embed.add_field(name="📜 Danh Sách Cần Câu", value=rod_desc, inline=False)
        
        view = ShopView(self, user_id, current_rod, points)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    # Retrieve the existing DatabaseManager instance if possible, 
    # but since setup needs to pass it, we create or retrieve.
    # Typically bot has it stored or we init new one.
    # Provided files show setup instantiates new DatabaseManager(config.DATABASE_PATH)
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(CauCaCog(bot, db))
