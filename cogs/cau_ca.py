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

# --- CONSTANTS & CONFIGURATION ---

RARITIES = {
    "Common":    {"color": 0x95A5A6, "chance": 58, "mul": 1.0, "emoji": "⚪"},
    "Uncommon":  {"color": 0x2ECC71, "chance": 23, "mul": 1.5, "emoji": "🟢"},
    "Rare":      {"color": 0x3498DB, "chance": 12, "mul": 3.0, "emoji": "🔵"},
    "Epic":      {"color": 0x9B59B6, "chance": 5,  "mul": 8.0, "emoji": "🟣"},
    "Legendary": {"color": 0xF1C40F, "chance": 1.8, "mul": 20.0, "emoji": "🟡"},
    "Mythical":  {"color": 0xE74C3C, "chance": 0.2, "mul": 100.0, "emoji": "🔴"}
}

BIOMES = {
    "River": {
        "name": "Dòng Sông",
        "desc": "Nơi bắt đầu của mọi cần thủ.",
        "req_level": 1,
        "req_money": 0,
        "emoji": emojis.BIOME_RIVER,
        "fish": [
            {"name": "Cá Chép", "base_value": 5, "min_size": 10, "max_size": 30, "emoji": emojis.FISH_RAW},
            {"name": "Cá Vàng", "base_value": 15, "min_size": 5, "max_size": 15, "emoji": emojis.FISH_GOLDFISH},
            {"name": "Cá Hồi", "base_value": 25, "min_size": 30, "max_size": 60, "emoji": emojis.FISH_SALMON},
            {"name": "Cá Tuyết", "base_value": 30, "min_size": 40, "max_size": 80, "emoji": emojis.FISH_COD},
            {"name": "Cua", "base_value": 20, "min_size": 5, "max_size": 15, "emoji": emojis.FISH_CRAB},
        ]
    },
    "Ocean": {
        "name": "Đại Dương",
        "desc": "Biển cả mênh mông với những loài cá lớn.",
        "req_level": 5,
        "req_money": 50000,
        "emoji": emojis.BIOME_OCEAN,
        "fish": [
            {"name": "Cá Nhiệt Đới", "base_value": 50, "min_size": 10, "max_size": 30, "emoji": emojis.FISH_TROPICAL},
            {"name": "Cá Ngừ", "base_value": 100, "min_size": 50, "max_size": 150, "emoji": emojis.FISH_TUNA},
            {"name": "Cá Mập", "base_value": 300, "min_size": 200, "max_size": 500, "emoji": emojis.FISH_SHARK},
            {"name": "Cá Heo", "base_value": 500, "min_size": 150, "max_size": 300, "emoji": emojis.FISH_DOLPHIN},
            {"name": "Rùa Biển", "base_value": 200, "min_size": 50, "max_size": 100, "emoji": emojis.FISH_TURTLE},
            {"name": "Mực Ống", "base_value": 80, "min_size": 20, "max_size": 60, "emoji": emojis.FISH_SQUID},
        ]
    },
    "Sky": {
        "name": "Vùng Trời",
        "desc": "Câu cá trên những đám mây.",
        "req_level": 10,
        "req_money": 100000,
        "emoji": emojis.BIOME_SKY,
        "fish": [
            {"name": "Cá Cầu Vồng", "base_value": 800, "min_size": 30, "max_size": 100, "emoji": emojis.FISH_RAINBOW},
            {"name": "Cá Azure", "base_value": 1000, "min_size": 40, "max_size": 120, "emoji": emojis.FISH_AZURE},
            {"name": "Cá Kim Cương", "base_value": 2000, "min_size": 20, "max_size": 50, "emoji": emojis.FISH_DIAMOND},
        ]
    },
    "Volcano": {
        "name": "Núi Lửa",
        "desc": "Nóng bỏng tay, cá nướng tại chỗ.",
        "req_level": 20,
        "req_money": 500000,
        "emoji": emojis.BIOME_VOLCANIC,
        "fish": [
            {"name": "Cá Nóng", "base_value": 1500, "min_size": 30, "max_size": 80, "emoji": emojis.FISH_HOTCOD},
            {"name": "Cá Dung Nham", "base_value": 3000, "min_size": 50, "max_size": 150, "emoji": emojis.FISH_LAVAFISH},
            {"name": "Cá Nóc Lửa", "base_value": 4000, "min_size": 40, "max_size": 90, "emoji": emojis.FISH_FIREPUFFER},
        ]
    },
    "Space": {
        "name": "Vũ Trụ",
        "desc": "Không trọng lực, cá siêu hiếm.",
        "req_level": 40,
        "req_money": 10000000,
        "emoji": emojis.BIOME_SPACE,
        "fish": [
            {"name": "Cá Vũ Trụ", "base_value": 8000, "min_size": 100, "max_size": 300, "emoji": emojis.FISH_SPACE},
            {"name": "Cua Không Gian", "base_value": 10000, "min_size": 50, "max_size": 120, "emoji": emojis.FISH_SPACE_CRAB},
            {"name": "Cá Lục Bảo", "base_value": 15000, "min_size": 80, "max_size": 200, "emoji": emojis.FISH_EMERALD},
        ]
    },
    "Alien": {
        "name": "Hành Tinh Lạ",
        "desc": "Những sinh vật bí ẩn từ thế giới khác.",
        "req_level": 60,
        "req_money": 50000000,
        "emoji": emojis.BIOME_ALIEN,
        "fish": [
            {"name": "Cá Ngoài Hành Tinh", "base_value": 25000, "min_size": 100, "max_size": 400, "emoji": emojis.FISH_ALIEN},
            {"name": "Vệ Binh Biển", "base_value": 40000, "min_size": 200, "max_size": 600, "emoji": emojis.FISH_GUARDIAN},
            {"name": "Axolotl Thần", "base_value": 50000, "min_size": 50, "max_size": 150, "emoji": emojis.FISH_AXOLOTL},
            {"name": "Mực Lục Bảo", "base_value": 60000, "min_size": 300, "max_size": 800, "emoji": emojis.FISH_EMERALD_SQUID},
            {"name": "Cá Ngựa Vằn", "base_value": 80000, "min_size": 100, "max_size": 200, "emoji": emojis.FISH_ZEBRA},
        ]
    }
}

RODS = {
    "Plastic Rod":    {"name": "Cần Nhựa",       "price": 0,          "power": 0,    "luck": 0,   "emoji": emojis.ROD_PLASTIC, "durability": None},
    "Steel Rod":      {"name": "Cần Thép",       "price": 5000,       "power": 10,   "luck": 5,   "emoji": emojis.ROD_STEEL, "durability": 50},
    "Alloy Rod":      {"name": "Cần Hợp Kim",    "price": 12000,      "power": 18,   "luck": 10,  "emoji": emojis.ROD_ALLOY, "durability": 80},
    "Fiberglass Rod": {"name": "Cần Sợi Thủy Tinh", "price": 18000,   "power": 22,   "luck": 12,  "emoji": emojis.ROD_FIBERGLASS, "durability": 100},
    "Golden Rod":     {"name": "Cần Vàng",       "price": 25000,      "power": 30,   "luck": 20,  "emoji": emojis.ROD_GOLDEN, "durability": 150},
    "Floating Rod":   {"name": "Cần Nổi",        "price": 40000,      "power": 40,   "luck": 25,  "emoji": emojis.ROD_FLOATING, "durability": 180},
    "Heavy Rod":      {"name": "Cần Hạng Nặng",  "price": 60000,      "power": 55,   "luck": 15,  "emoji": emojis.ROD_HEAVY, "durability": 200},
    "Heavier Rod":    {"name": "Cần Siêu Nặng",  "price": 80000,      "power": 70,   "luck": 20,  "emoji": emojis.ROD_HEAVIER, "durability": 220},
    "Lava Rod":       {"name": "Cần Dung Nham",  "price": 100000,     "power": 85,   "luck": 30,  "emoji": emojis.ROD_LAVA, "durability": 250},
    "Magma Rod":      {"name": "Cần Magma",      "price": 150000,     "power": 100,  "luck": 35,  "emoji": emojis.ROD_MAGMA, "durability": 300},
    "Oceanium Rod":   {"name": "Cần Đại Dương",  "price": 250000,     "power": 120,  "luck": 50,  "emoji": emojis.ROD_OCEANIUM, "durability": 400},
    "Sky Rod":        {"name": "Cần Bầu Trời",   "price": 500000,     "power": 150,  "luck": 60,  "emoji": emojis.ROD_SKY, "durability": 500},
    "Meteor Rod":     {"name": "Cần Thiên Thạch","price": 800000,     "power": 180,  "luck": 70,  "emoji": emojis.ROD_METEOR, "durability": 600},
    "Space Rod":      {"name": "Cần Vũ Trụ",     "price": 2000000,    "power": 250,  "luck": 100, "emoji": emojis.ROD_SPACE, "durability": 800},
    "Superium Rod":   {"name": "Cần Siêu Cấp",   "price": 5000000,    "power": 350,  "luck": 150, "emoji": emojis.ROD_SUPERIUM, "durability": 1000},
    "Diamond Rod":    {"name": "Cần Kim Cương",  "price": 8000000,    "power": 450,  "luck": 200, "emoji": emojis.ROD_DIAMOND, "durability": 1200},
    "Alien Rod":      {"name": "Cần Alien",      "price": 12000000,   "power": 600,  "luck": 250, "emoji": emojis.ROD_ALIEN, "durability": 1500},
    "Saltspreader":   {"name": "Cần Rắc Muối",   "price": 20000000,   "power": 750,  "luck": 300, "emoji": emojis.ROD_SALTSPREADER, "durability": 2000},
    "Infinity Rod":   {"name": "Cần Vô Cực",     "price": 50000000,   "power": 1000, "luck": 500, "emoji": emojis.ROD_INFINITY, "durability": 5000},
    "Donator Rod":    {"name": "Cần Nhà Tài Trợ","price": 0,          "power": 1500, "luck": 800, "emoji": emojis.ROD_DONATOR, "description": "Cần câu dành riêng cho Nhà Tài Trợ (Không thể mua)", "durability": None},
}
# Map old keys to new if necessary, but here we assume clean slate or migration
ROD_LIST = list(RODS.keys())

BADGES = {
    "Bronze":    {"name": "Huy hiệu Đồng", "desc": "Câu được tổng cộng 100 con cá", "emoji": emojis.BADGE_BRONZE, "req_type": "total_fish", "req_val": 100},
    "Silver":    {"name": "Huy hiệu Bạc",  "desc": "Câu được tổng cộng 500 con cá", "emoji": emojis.BADGE_SILVER, "req_type": "total_fish", "req_val": 500},
    "Gold":      {"name": "Huy hiệu Vàng", "desc": "Câu được tổng cộng 1000 con cá", "emoji": emojis.BADGE_GOLD, "req_type": "total_fish", "req_val": 1000},
    "Platinum":  {"name": "Huy hiệu Bạch Kim", "desc": "Câu được tổng cộng 5000 con cá", "emoji": emojis.BADGE_PLATINUM, "req_type": "total_fish", "req_val": 5000},
    "Amethyst":  {"name": "Huy hiệu Thạch Anh", "desc": "Kiếm được 1 triệu Coiz từ câu cá", "emoji": emojis.BADGE_AMETHYST, "req_type": "total_earn", "req_val": 1000000},
    "Emerald":   {"name": "Huy hiệu Lục Bảo", "desc": "Kiếm được 10 triệu Coiz từ câu cá", "emoji": emojis.BADGE_EMERALD, "req_type": "total_earn", "req_val": 10000000},
    "Ruby":      {"name": "Huy hiệu Hồng Ngọc", "desc": "Kiếm được 100 triệu Coiz từ câu cá", "emoji": emojis.BADGE_RUBY, "req_type": "total_earn", "req_val": 100000000},
    "Sapphire":  {"name": "Huy hiệu Sapphire", "desc": "Sở hữu 10 loại Cần câu khác nhau", "emoji": emojis.BADGE_SAPPHIRE, "req_type": "rod_count", "req_val": 10},
    "50Shades":  {"name": "50 Sắc Thái", "desc": "Sở hữu 20 loại Cần câu khác nhau", "emoji": emojis.BADGE_50_SHADES, "req_type": "rod_count", "req_val": 20},
    "Admin":     {"name": "Admin", "desc": "Dành cho Admin", "emoji": emojis.BADGE_ADMIN, "req_type": "admin", "req_val": 0},
    "Supporter": {"name": "Người Ủng Hộ", "desc": "Dành cho Donator", "emoji": emojis.BADGE_SUPPORTER, "req_type": "manual", "req_val": 0},
}

BAITS = {
    "Worms":           {"name": "Mồi Giun",    "price": 50,     "power": 0,  "luck": 0,  "desc": "Mồi câu cơ bản.", "emoji": emojis.BAIT_WORM},
    "Cricket":         {"name": "Dế Mèn",      "price": 200,    "power": 5,  "luck": 2,  "desc": "Thu hút cá nhỏ.", "emoji": emojis.BAIT_CRICKET},
    "Leeches":         {"name": "Đỉa",         "price": 500,    "power": 8,  "luck": 4,  "desc": "Bám dính tốt.", "emoji": emojis.BAIT_LEECH},
    "Minnows":         {"name": "Cá Con",      "price": 1500,   "power": 12, "luck": 8,  "desc": "Dụ cá săn mồi.", "emoji": emojis.BAIT_MINNOW},
    "Support Bait":    {"name": "Mồi Hỗ Trợ",  "price": 15000,  "power": 30, "luck": 25, "desc": "Tăng khả năng câu.", "emoji": emojis.BAIT_SUPPORT},
    "Magic Bait":      {"name": "Mồi Ma Thuật","price": 50000,  "power": 50, "luck": 40, "desc": "Có ma thuật huyền bí.", "emoji": emojis.BAIT_MAGIC},
    "Wise Bait":       {"name": "Mồi Thông Thái","price": 100000,"power": 80, "luck": 60, "desc": "Dụ cá hiếm cực tốt.", "emoji": emojis.BAIT_WISE},
    "Magnet":          {"name": "Nam Châm",    "price": 200000, "power": 30, "luck": 20, "desc": "Hút 2-4 con cá một lúc!", "emoji": emojis.BAIT_MAGNET, "is_special": True},
}

TREASURES = [
    {"name": "Rương Gỗ",        "value": 2000,   "emoji": emojis.CHEST_UNCOMMON},
    {"name": "Rương Sắt",       "value": 5000,   "emoji": emojis.CHEST_RARE},
    {"name": "Rương Vàng",      "value": 20000,  "emoji": emojis.CHEST_EPIC},
    {"name": "Rương Kim Cương", "value": 100000, "emoji": emojis.CHEST_LEGENDARY},
    {"name": "Rương Kho Báu",   "value": 500000, "emoji": emojis.CHEST_SUPER},
    {"name": "Cổ Vật",          "value": 1000000,"emoji": emojis.CHEST_ARTIFACT},
]

CHARMS = {
    "Lucky Charm": {"name": "Bùa May Mắn", "price": 5000, "power": 0, "luck": 50, "duration_min": 10, "duration_max": 30, "emoji": emojis.CHARM_GREEN},
    "Power Charm": {"name": "Bùa Sức Mạnh", "price": 8000, "power": 50, "luck": 0, "duration_min": 10, "duration_max": 20, "emoji": emojis.CHARM_RED},
    "Golden Charm": {"name": "Bùa Vàng", "price": 20000, "power": 30, "luck": 30, "duration_min": 5, "duration_max": 15, "emoji": emojis.CHARM_YELLOW},
}

class ChangeBaitView(discord.ui.View):
    def __init__(self, cog, user_id, baits_inv, parent_view):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.baits_inv = baits_inv
        self.parent_view = parent_view
        
        # Populate buttons
        for key, count in baits_inv.items():
            if count > 0:
                info = BAITS.get(key, {"name": key, "emoji": "🪱"})
                btn = discord.ui.Button(label=f"{info['name']} (x{count})", emoji=info['emoji'], style=discord.ButtonStyle.secondary)
                
                async def callback(inter, k=key, n=info['name']):
                    await self.equip_bait(inter, k, n)
                    
                btn.callback = callback
                self.add_item(btn)

    async def equip_bait(self, interaction: discord.Interaction, key, name):
        if key == "Magnet":
            # Prompt for sub-bait
            other_baits = {k: v for k, v in self.baits_inv.items() if k != "Magnet" and v > 0}
            
            if not other_baits:
                 await self._do_equip(interaction, key, None)
                 return
                 
            view = discord.ui.View()
            options = [discord.SelectOption(label="Không dùng kèm", value="none", emoji="❌")]
            
            for k, count in other_baits.items():
                 b_info = BAITS.get(k, {"name": k, "emoji": "🪱"})
                 options.append(discord.SelectOption(label=f"{b_info['name']} (x{count})", value=k, emoji=b_info['emoji']))
            
            select = discord.ui.Select(placeholder="Chọn mồi dùng kèm Nam Châm...", options=options[:25])
            
            async def sub_callback(inter):
                 val = select.values[0]
                 sub_bait = val if val != "none" else None
                 await self._do_equip(inter, "Magnet", sub_bait)
            
            select.callback = sub_callback
            view.add_item(select)
            
            await interaction.response.send_message("🧲 Bạn có muốn dùng kèm mồi khác để tăng hiệu quả không?", view=view, ephemeral=True)
            return

        await self._do_equip(interaction, key, None)

    async def _do_equip(self, interaction, key, sub_bait):
        data = await self.cog.db.get_fishing_data(self.user_id)
        stats = data.get("stats", {})
        stats["current_bait"] = key
        stats["magnet_sub_bait"] = sub_bait
        await self.cog.db.update_fishing_data(self.user_id, stats=stats)
        
        msg = f"✅ Đã trang bị mồi **{BAITS.get(key,{}).get('name', key)}**!"
        if sub_bait:
             msg += f" (Kèm: **{BAITS.get(sub_bait,{}).get('name', sub_bait)}**)"
        
        if interaction.response.is_done():
             await interaction.edit_original_response(content=msg, view=None)
        else:
             await interaction.response.send_message(msg, ephemeral=True) 

class ChangeRodView(discord.ui.View):
    def __init__(self, cog, user_id, owned_rods, current_rod, parent_view, durability_map=None):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.owned_rods = owned_rods
        self.current_rod = current_rod
        self.parent_view = parent_view
        if durability_map is None: durability_map = {}
        
        for rod_key in owned_rods:
            info = RODS.get(rod_key, {"name": rod_key, "emoji": "🎣"})
            style = discord.ButtonStyle.primary if rod_key == current_rod else discord.ButtonStyle.secondary
            disabled = (rod_key == current_rod)
            
            dura = durability_map.get(rod_key)
            max_dura = info.get("durability")
            label_s = info['name']
            if dura is not None and max_dura:
                label_s += f" [{dura}/{max_dura}]"
            
            btn = discord.ui.Button(label=label_s, emoji=info['emoji'], style=style, disabled=disabled)
            
            async def callback(inter, k=rod_key, n=info['name']):
                await self.equip_rod(inter, k, n)
            
            btn.callback = callback
            self.add_item(btn)

    async def equip_rod(self, interaction: discord.Interaction, key, name):
        await self.cog.db.update_fishing_data(self.user_id, rod_type=key)
        await interaction.response.send_message(f"✅ Đã trang bị **{name}**!", ephemeral=True)

class ShopSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.select(
        placeholder="🏪 Chọn cửa hàng muốn ghé thăm...",
        min_values=1, 
        max_values=1,
        options=[
            discord.SelectOption(label="Cửa Hàng Mồi", emoji="🪱", description="Mua mồi câu (Giun, Dế, Nam Châm...)", value="bait"),
            discord.SelectOption(label="Cửa Hàng Cần", emoji="🎣", description="Nâng cấp cần câu mới", value="rod"),
            discord.SelectOption(label="Cửa Hàng Bùa", emoji="🧿", description="Mua bùa buff chỉ số", value="charm"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        if choice == "bait":
             # Call the command callback manually
             await self.cog.bait_shop.callback(self.cog, interaction)
        elif choice == "rod":
             await self.cog.rod_shop.callback(self.cog, interaction)
        elif choice == "charm":
             # Charm shop is a regular method, not a command anymore
             await self.cog.charm_shop(interaction)


class ConfirmUnlockView(discord.ui.View):
    def __init__(self, cog, user_id, biome_key, cost):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.biome_key = biome_key
        self.cost = cost

    @discord.ui.button(label="Xác Nhận Mở Khóa", style=discord.ButtonStyle.success, emoji="🔓")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        
        # Re-check money
        bal = await self.cog.db.get_player_points(self.user_id, interaction.guild_id)
        if bal < self.cost:
             await interaction.response.send_message(f"❌ Bạn không đủ tiền! Cần {self.cost:,} Coiz.", ephemeral=True)
             return

        await self.cog.db.add_points(self.user_id, interaction.guild_id, -self.cost)
        
        # Update unlock data
        data = await self.cog.db.get_fishing_data(self.user_id)
        stats = data.get("stats", {})
        unlocked = stats.get("unlocked_biomes", ["River"])
        
        if self.biome_key not in unlocked:
            unlocked.append(self.biome_key)
            stats["unlocked_biomes"] = unlocked
        
        # Move to new biome
        stats["current_biome"] = self.biome_key
        await self.cog.db.update_fishing_data(self.user_id, stats=stats)

        b_info = BIOMES[self.biome_key]
        await interaction.response.edit_message(content=f"🎉 Đã mở khóa và chuyển đến **{b_info['emoji']} {b_info['name']}**!", view=None, embed=None)

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
         if interaction.user.id != self.user_id: return
         await interaction.response.edit_message(content="❌ Đã hủy mở khóa.", view=None, embed=None)

class BiomeSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="🗺️ Xem thông tin vùng...", min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.selected_biome = self.values[0]
        self.view.update_components()
        embed = self.view.get_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)

class BiomeSelectView(discord.ui.View):
    def __init__(self, cog, user_id, current_biome, stats):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        if current_biome not in BIOMES:
            current_biome = "River"
        self.current_biome = current_biome
        self.selected_biome = current_biome
        self.stats = stats
        self.unlocked = stats.get("unlocked_biomes", ["River"])
        if "River" not in self.unlocked:
            self.unlocked.insert(0, "River")
        self.update_components()

    def update_components(self):
        self.clear_items()
        
        options = []
        for k, v in BIOMES.items():
            is_unlocked = k in self.unlocked
            label = v["name"]
            emoji = v["emoji"]
            desc = "Đã mở khóa" if is_unlocked else "🔒 Locked"
            options.append(discord.SelectOption(label=label, emoji=emoji, value=k, description=desc, default=(k==self.selected_biome)))
        self.add_item(BiomeSelect(options))
        
        if self.selected_biome in self.unlocked:
             style = discord.ButtonStyle.secondary if self.selected_biome == self.current_biome else discord.ButtonStyle.success
             label = "Đang Ở Đây" if self.selected_biome == self.current_biome else "Đi Đến Đây"
             disabled = (self.selected_biome == self.current_biome)
             
             btn = discord.ui.Button(label=label, style=style, disabled=disabled, emoji="✅")
             btn.callback = self.move_callback
             self.add_item(btn)
        else:
             cost = BIOMES[self.selected_biome].get("req_money", 0)
             btn = discord.ui.Button(label=f"Mở Khóa ({cost:,} Coiz)", style=discord.ButtonStyle.primary, emoji="🔓")
             btn.callback = self.unlock_callback
             self.add_item(btn)

    def get_embed(self):
        b_data = BIOMES[self.selected_biome]
        embed = discord.Embed(title=f"{b_data['emoji']} {b_data['name']}", description=b_data['desc'], color=discord.Color.blue())
        
        req_level = b_data.get("req_level", 1)
        req_money = b_data.get("req_money", 0)
        status = "✅ Đã mở khóa" if self.selected_biome in self.unlocked else f"🔒 Yêu cầu: Level {req_level} | {req_money:,} Coiz"
        embed.add_field(name="📍 Trạng Thái", value=status, inline=False)
        
        fish_list = b_data.get("fish", [])
        fish_desc = "\n".join([f"- {f['emoji']} {f['name']}" for f in fish_list])
        embed.add_field(name="🐟 Các loài cá:", value=fish_desc or "Chưa có thông tin", inline=False)
        return embed

    async def move_callback(self, interaction: discord.Interaction):
         if interaction.user.id != self.user_id: return
         self.stats["current_biome"] = self.selected_biome
         await self.cog.db.update_fishing_data(self.user_id, stats=self.stats)
         await interaction.response.edit_message(content=f"✅ Đã chuyển đến **{BIOMES[self.selected_biome]['name']}**!", view=None, embed=None)

    async def unlock_callback(self, interaction: discord.Interaction):
         if interaction.user.id != self.user_id: return
         b_key = self.selected_biome
         b_data = BIOMES[b_key]
         cost = b_data.get("req_money", 0)
         req_level = b_data.get("req_level", 1)
         user_level = self.stats.get("level", 1)
         
         if user_level < req_level:
              await interaction.response.send_message(f"❌ Bạn cấp thấp! Cần Level {req_level}.", ephemeral=True)
              return
              
         user_point = await self.cog.db.get_player_points(self.user_id, interaction.guild_id)
         if user_point < cost:
              await interaction.response.send_message(f"❌ Bạn không đủ tiền! Cần {cost:,} Coiz.", ephemeral=True)
              return
              
         await self.cog.db.add_points(self.user_id, interaction.guild_id, -cost)
         self.unlocked.append(b_key)
         self.stats["unlocked_biomes"] = self.unlocked
         self.stats["current_biome"] = b_key
         await self.cog.db.update_fishing_data(self.user_id, stats=self.stats)
         
         await interaction.response.edit_message(content=f"🎉 Đã mở khóa và chuyển đến **{b_data['name']}**!", view=None, embed=None)

class FishingView(discord.ui.View):
    def __init__(self, cog, user_id, current_biome, last_catch=None):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        if current_biome not in BIOMES:
            current_biome = "River"
        self.current_biome = current_biome
        self.last_catch = last_catch
        self.message = None

    @discord.ui.button(label="Câu Tiếp", style=discord.ButtonStyle.success, emoji="🎣")
    async def fish_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        self.timeout = 60
        await interaction.response.defer()
        await self.cog.process_fishing(interaction, self.current_biome, view=self)

    @discord.ui.button(label="Bán Nhanh", style=discord.ButtonStyle.secondary, emoji="💰")
    async def sell_fast(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        if not self.last_catch:
            await interaction.response.send_message("❌ Không có cá để bán hoặc đã bán rồi!", ephemeral=True)
            return

        catches = self.last_catch if isinstance(self.last_catch, list) else [self.last_catch]
        total_val = 0
        names_sold = []
        
        data = await self.cog.db.get_fishing_data(self.user_id)
        inv = data.get("inventory", {})
        fish_inv = inv.get("fish", {})

        for fish in catches:
            f_name = fish['name']
            f_val = fish['value']
            if f_name in fish_inv and fish_inv[f_name]["count"] > 0:
                fish_inv[f_name]["count"] -= 1
                fish_inv[f_name]["total_value"] -= f_val
                if fish_inv[f_name]["count"] <= 0: del fish_inv[f_name]
                total_val += f_val
                names_sold.append(f_name)

        if total_val > 0:
            stats = data.get("stats", {})
            stats["lifetime_money"] = stats.get("lifetime_money", 0) + total_val
            
            await self.cog.db.update_fishing_data(self.user_id, inventory=inv, stats=stats)
            await self.cog.db.add_points(self.user_id, interaction.guild_id, total_val)
            
            await self.cog.check_badges(self.user_id, interaction.channel)
            
            button.disabled = True
            button.label = "Đã Bán"
            self.last_catch = None
            await interaction.response.edit_message(view=self)
            names_summary = ", ".join(set(names_sold))
            cnt = len(names_sold)
            await interaction.followup.send(f"✅ Đã bán **{cnt}x cá** ({names_summary}) với giá **{total_val:,}** Coiz {emojis.ANIMATED_EMOJI_COIZ}", ephemeral=True)
        else:
             await interaction.response.send_message("❌ Cá này không còn trong túi đồ (có thể đã bán?)", ephemeral=True)

    @discord.ui.button(label="Chuyển Vùng", style=discord.ButtonStyle.secondary, emoji="🗺️", row=1)
    async def change_biome(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        # Call the existing command logic function to ensure consistency (same interface as /khu-vuc)
        await self.cog.show_biomes_ui(interaction)

    @discord.ui.button(label="Đổi Mồi", style=discord.ButtonStyle.secondary, emoji="🪱", row=1)
    async def change_bait(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        data = await self.cog.db.get_fishing_data(self.user_id)
        inv = data.get("inventory", {})
        baits_inv = inv.get("baits", {})
        if not baits_inv:
            await interaction.response.send_message("❌ Túi mồi trống không! Hãy vào Shop mua thêm.", ephemeral=True)
            return
        view = ChangeBaitView(self.cog, self.user_id, baits_inv, self)
        await interaction.response.send_message("👇 **Chọn mồi câu muốn dùng:**", view=view, ephemeral=True)

    @discord.ui.button(label="Đổi Cần", style=discord.ButtonStyle.secondary, emoji="🥢", row=1)
    async def change_rod(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        data = await self.cog.db.get_fishing_data(self.user_id)
        current_rod = data.get("rod_type", "Plastic Rod")
        
        inv = data.get("inventory", {})
        owned = inv.get("rods", [])
        durability_map = inv.get("rod_durability", {})

        # Ensure default
        if not owned: owned = ["Plastic Rod"]
        
        # Sync current rod if missing (migration fix)
        if current_rod not in owned:
            owned.append(current_rod)
            inv["rods"] = owned
            await self.cog.db.update_fishing_data(self.user_id, inventory=inv)

        view = ChangeRodView(self.cog, self.user_id, owned, current_rod, self, durability_map)
        await interaction.response.send_message(f"👇 **Chọn cần câu ({len(owned)} sở hữu):**", view=view, ephemeral=True)


class UseCharmSelect(discord.ui.Select):
    def __init__(self, cog, user_id, charm_list):
        self.cog = cog
        self.user_id = user_id
        options = []
        for i, c in enumerate(charm_list[:25]):
             c_info = CHARMS.get(c['key'], {"emoji": "🧿"})
             minutes = c['duration'] // 60
             options.append(discord.SelectOption(
                label=f"{c.get('name', 'Bùa')} ({minutes}p)",
                value=str(i),
                description=f"Kích hoạt {minutes}p",
                emoji=c_info.get('emoji', '🧿')
             ))
        super().__init__(placeholder="Chọn bùa để sử dụng...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        d = await self.cog.db.get_fishing_data(self.user_id)
        i_v = d.get("inventory", {})
        c_list = i_v.get("charms", [])
        
        if idx >= len(c_list):
            await interaction.response.send_message("❌ Bùa không tồn tại hoặc lỗi dữ liệu!", ephemeral=True)
            return
        
        try:
            used_charm = c_list.pop(idx)
        except IndexError:
             await interaction.response.send_message("❌ Bùa không tồn tại!", ephemeral=True)
             return
        
        # Activate
        st = d.get("stats", {})
        ac = st.get("active_charms", {})
        
        import time
        now = int(time.time())
        current_end = ac.get(used_charm['key'], now)
        if current_end < now: current_end = now
        
        ac[used_charm['key']] = current_end + used_charm['duration']
        st["active_charms"] = ac
        
        await self.cog.db.update_fishing_data(self.user_id, inventory=i_v, stats=st)
        await interaction.response.send_message(f"✨ Đã kích hoạt **{used_charm['name']}**! Hiệu lực thêm {used_charm['duration']//60} phút.", ephemeral=True)

class InventoryView(discord.ui.View):
    def __init__(self, cog, user_id, user_data):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.user_data = user_data
        
        self.add_item(InventorySelect(cog, user_id, user_data))

    @discord.ui.button(label="Dùng Bùa", style=discord.ButtonStyle.success, emoji="🔮", row=1)
    async def use_charm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        
        # Refresh data to be safe
        d = await self.cog.db.get_fishing_data(self.user_id)
        charms = d.get("inventory", {}).get("charms", [])
        
        if not charms:
             await interaction.response.send_message("❌ Bạn không có bùa nào để dùng!", ephemeral=True)
             return

        view = discord.ui.View()
        view.add_item(UseCharmSelect(self.cog, self.user_id, charms))
        await interaction.response.send_message("👇 **Chọn bùa muốn kích hoạt:**", view=view, ephemeral=True)

class InventorySelect(discord.ui.Select):
    def __init__(self, cog, user_id, user_data):
        self.cog = cog
        self.user_id = user_id
        self.user_data = user_data
        
        options = [
            discord.SelectOption(label="Cần Câu", emoji="🎣", value="rod", description="Xem danh sách cần câu"),
            discord.SelectOption(label="Cá", emoji="🐟", value="fish", description="Xem kho cá câu được"),
            discord.SelectOption(label="Mồi Câu", emoji="🪱", value="bait", description="Xem số lượng mồi"),
            discord.SelectOption(label="Bùa Chú", emoji="🧿", value="charm", description="Xem bùa buff")
        ]
        super().__init__(placeholder="Chọn túi đồ để xem...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id: 
            return # Silent fail or ephemeral msg
        
        val = self.values[0]
        inv = self.user_data.get("inventory", {})
        embed = discord.Embed(title=f"🎒 TÚI ĐỒ", color=discord.Color.gold())
        
        if val == "rod":
            rods_inv = inv.get("rods", [])
            dura_map = inv.get("rod_durability", {})
            current_rod = self.user_data.get("rod_type", "Plastic Rod")
            
            if rods_inv:
                rod_lines = []
                for r in rods_inv:
                    r_info = RODS.get(r, {"name": r, "emoji": "🎣", "durability": None})
                    dura = dura_map.get(r)
                    max_d = r_info.get("durability")
                    dura_str = "Vĩnh viễn"
                    if max_d:
                        cur = dura if dura is not None else max_d
                        dura_str = f"{cur}/{max_d}"
                    status = "✅ (Đang dùng)" if r == current_rod else ""
                    rod_lines.append(f"{r_info['emoji']} **{r_info['name']}** {status} [Độ bền: {dura_str}]")
                embed.description = "\n".join(rod_lines)
            else:
                embed.description = "Chưa sở hữu cần nào."

        elif val == "fish":
            fish_inv = inv.get("fish", {})
            if fish_inv:
                fish_list = []
                total_val = 0
                for name, info in fish_inv.items():
                    count = info.get("count", 0)
                    val_fish = info.get("total_value", 0)
                    
                    # Look up fish emoji from Biomes data by name
                    emoji_icon = "🐟"
                    for b_key, b_val in BIOMES.items():
                         for f in b_val["fish"]:
                             if f["name"] == name:
                                 emoji_icon = f["emoji"]
                                 break
                         if emoji_icon != "🐟": break
                    
                    if count > 0:
                        fish_list.append(f"• {emoji_icon} **{name}**: x{count} (Tổng: {val_fish:,} Coiz {emojis.ANIMATED_EMOJI_COIZ})")
                        total_val += val_fish
                embed.add_field(name=f"🐟 Cá ({total_val:,} Coiz {emojis.ANIMATED_EMOJI_COIZ})", value="\n".join(fish_list) if fish_list else "Trống", inline=False)
            else:
                embed.description = "Thùng cá trống rỗng."

        elif val == "bait":
            bait_inv = inv.get("baits", {})
            bait_list = []
            if bait_inv:
                for k, v in bait_inv.items():
                    b_info = BAITS.get(k, {"name": k, "emoji": "🪱"})
                    if v > 0:
                        bait_list.append(f"{b_info['emoji']} **{b_info['name']}**: {v}")
            embed.description = "\n".join(bait_list) if bait_list else "Hết mồi câu rồi!"

        elif val == "charm":
            charm_inv = inv.get("charms", [])
            if charm_inv:
                charm_list = []
                for i, c in enumerate(charm_inv):
                    minutes = c['duration'] // 60
                    c_info = CHARMS.get(c['key'], {"emoji": "🧿"})
                    charm_list.append(f"**{i+1}.** {c_info.get('emoji', '🧿')} {c.get('name', 'Bùa')} ({minutes}p)")
                embed.description = "\n".join(charm_list)
            else:
                embed.description = "Không có bùa nào."
                
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Shop", style=discord.ButtonStyle.primary, emoji="🛒", row=1)
    async def open_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        view = ShopSelectView(self.cog)
        await interaction.response.send_message("🏪 **Bạn muốn vào cửa hàng nào?**", view=view, ephemeral=True)

class CauCaCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db

    # ... (Command implementations inside class)

    async def get_stats_multiplier(self, user_id):
        """Calculate total Power and Luck from Rod + Bait + Active Charms"""
        data = await self.db.get_fishing_data(user_id)
        stats = data.get("stats", {})
        
        # Rod Stats
        rod_key = data.get("rod_type", "Plastic Rod")
        rod = RODS.get(rod_key, RODS["Plastic Rod"])
        
        # Bait Stats
        bait_key = stats.get("current_bait")
        bait = BAITS.get(bait_key, {"power": 0, "luck": 0})
        
        active_charms = stats.get("active_charms", {})
        import time
        current_time = int(time.time())
        
        charm_power = 0
        charm_luck = 0
        expired_charms = []
        
        for c_key, expire_at in active_charms.items():
            if current_time < expire_at:
                c_info = CHARMS.get(c_key)
                if c_info:
                    charm_power += c_info["power"]
                    charm_luck += c_info["luck"]
            else:
                expired_charms.append(c_key)
        
        # Clean up expired
        if expired_charms:
            for k in expired_charms:
                del active_charms[k]
            stats["active_charms"] = active_charms
            # We don't save DB here to avoid async write race conditions in tight loops, 
            # relying on next update. Or we can just let it update next time something is saved.
        
        total_power = rod["power"] + bait["power"] + charm_power
        total_luck = rod["luck"] + bait["luck"] + charm_luck
        
        return total_power, total_luck, data, bait_key

    async def charm_shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🧿 CỬA HÀNG BÙA CHÚ", description="Mua bùa để tăng chỉ số trong thời gian ngắn! (Ngẫu nhiên 3-30p)", color=discord.Color.purple())
        
        for key, info in CHARMS.items():
            embed.add_field(
                name=f"{info['emoji']} {info['name']}",
                value=f"💰 Giá: **{info['price']:,}** Coiz {emojis.ANIMATED_EMOJI_COIZ}\n💪 Power: +{info['power']} | 🍀 Luck: +{info['luck']}\n⏱️ Thời gian: {info['duration_min']}-{info['duration_max']} phút",
                inline=False
            )
            
        view = discord.ui.View()
        
        for key, info in CHARMS.items():
            btn = discord.ui.Button(label=info['name'], emoji=info['emoji'], style=discord.ButtonStyle.secondary)
            
            async def callback(inter, k=key, i=info):
                # Buy logic
                cost = i["price"]
                user_point = await self.db.get_player_points(inter.user.id, inter.guild_id)
                
                if user_point < cost:
                    await inter.response.send_message("❌ Không đủ tiền!", ephemeral=True)
                    return
                
                # Randomized duration on purchase
                duration_min = i["duration_min"]
                duration_max = i["duration_max"]
                duration_sec = random.randint(duration_min * 60, duration_max * 60)
                
                await self.db.add_points(inter.user.id, inter.guild_id, -cost)
                
                data = await self.db.get_fishing_data(inter.user.id)
                inv = data.get("inventory", {})
                if "charms" not in inv: inv["charms"] = [] 
                
                # New charm item
                new_charm = {"key": k, "duration": duration_sec, "name": i["name"]}
                inv["charms"].append(new_charm)
                
                await self.db.update_fishing_data(inter.user.id, inventory=inv)
                
                minutes = duration_sec // 60
                seconds = duration_sec % 60
                await inter.response.send_message(f"✅ Đã mua **{i['emoji']} {i['name']}**!\n⏱️ Thời gian hiệu lực: **{minutes} phút {seconds} giây**.\n(Vào `/inventory` chọn dùng ngay)", ephemeral=True)


            btn.callback = callback
            view.add_item(btn)

        back_btn = discord.ui.Button(label="Trang Chủ", style=discord.ButtonStyle.secondary, emoji="🏠", row=1)
        async def back_callback(inter):
            if inter.user.id != interaction.user.id: return
            view = ShopSelectView(self)
            await inter.response.edit_message(content="🏪 **CHÀO MỪNG ĐẾN CỬA HÀNG!**\nBạn muốn xem loại hàng nào?", embed=None, view=view)
        back_btn.callback = back_callback
        view.add_item(back_btn)
            
        await interaction.response.send_message(embed=embed, view=view)
    async def check_badges(self, user_id, channel):
        data = await self.db.get_fishing_data(user_id)
        stats = data.get("stats", {})
        owned_badges = stats.get("badges", [])
        
        # Metrics
        total_fish = 0
        inv = data.get("inventory", {})
        fish_inv = inv.get("fish", {})
        # Recalculate total caught from current inventory + unsold? 
        # Ideally we track a lifetime stats. 
        # For now, approximate with inventory count + sold count if we tracked it (we don't fully).
        # Improving: "total_caught" in stats.
        total_caught = stats.get("total_caught", 0)
        
        total_money = stats.get("lifetime_money", 0)
        
        owned_rods_count = 0
        rods_list = inv.get("rods", [])
        if rods_list:
            owned_rods_count = len(rods_list)
        elif data.get("rod_type"): 
             owned_rods_count = 1
        
        new_badges = []
        for key, info in BADGES.items():
            if key in owned_badges: continue
            
            req_type = info["req_type"]
            val = info["req_val"]
            awarded = False
            
            if req_type == "total_fish" and total_caught >= val: awarded = True
            elif req_type == "total_earn" and total_money >= val: awarded = True
            elif req_type == "rod_count" and owned_rods_count >= val: awarded = True
            
            if awarded:
                owned_badges.append(key)
                new_badges.append(info)
        
        if new_badges:
            stats["badges"] = owned_badges
            await self.db.update_fishing_data(user_id, stats=stats)
            if channel:
                desc = "\n".join([f"{b['emoji']} **{b['name']}**\n*{b['desc']}*" for b in new_badges])
                em = discord.Embed(title="🏅 HUY HIỆU MỚI!", description=f"Chúc mừng bạn đã đạt được:\n{desc}", color=discord.Color.orange())
                try:
                    await channel.send(f"<@{user_id}>", embed=em)
                except: pass

    async def process_fishing(self, interaction: discord.Interaction, biome_name, view=None):
        user_id = interaction.user.id
        channel_id = interaction.channel_id
        
        # Check channel config
        config_channel = await self.db.get_channel_config(channel_id)
        if config_channel != "fishing":
            # Allow admin to fish anywhere or just ignore? Best to warn if command used directly.
            # But process_fishing is internal.
            pass

        data = await self.db.get_fishing_data(user_id)
        inventory = data.get("inventory", {})
        stats = data.get("stats", {})

        # === REQUIREMENTS CHECK ===
        user_balance = await self.db.get_player_points(user_id, interaction.guild_id)
        owned_rods = inventory.get("rods", [])
        
        # 1. New User: First Rod (Steel Rod - 5000 Coinz)
        if not owned_rods:
            if user_balance < 5000:
                 msg = f"❌ Bạn là người mới? Bạn cần **5,000 Coiz** {emojis.ANIMATED_EMOJI_COIZ} để mua Cần Câu đầu tiên (Cần Thép)!"
                 try: await interaction.response.send_message(msg, ephemeral=True)
                 except: await interaction.followup.send(msg, ephemeral=True)
                 return
            
            # Deduct & Unlock
            await self.db.add_points(user_id, interaction.guild_id, -5000)
            
            # Update Inventory
            if "rods" not in inventory: inventory["rods"] = []
            inventory["rods"].append("Steel Rod")
            # Initialize durability
            if "rod_durability" not in inventory: inventory["rod_durability"] = {}
            inventory["rod_durability"]["Steel Rod"] = RODS["Steel Rod"]["durability"]
            
            # Also ensure Steel Rod is active
            await self.db.update_fishing_data(user_id, rod_type="Steel Rod", inventory=inventory)
            
            try: await interaction.channel.send(f"🎉 **Chào mừng Newbie!** Hệ thống đã tự động mua **Cần Thép** (-5,000 Coiz {emojis.ANIMATED_EMOJI_COIZ}) cho bạn!")
            except: pass
            
            # Refresh data
            data = await self.db.get_fishing_data(user_id)
            stats = data.get("stats", {})
            inventory = data.get("inventory", {})

        # 2. Fishing Cost (10 Coiz)
        if user_balance < 10:
             msg = f"❌ Bạn cần **10 Coiz** {emojis.ANIMATED_EMOJI_COIZ} chi phí cho mỗi lần câu!"
             try: await interaction.response.send_message(msg, ephemeral=True)
             except: await interaction.followup.send(msg, ephemeral=True)
             return
             
        await self.db.add_points(user_id, interaction.guild_id, -10)
        
        # 3. Bait Check
        if not stats.get("current_bait"):
             msg = f"❌ Bạn chưa trang bị mồi câu! Hãy vào `/shop` để mua Mồi Giun và dùng `/inventory` để trang bị."
             try: await interaction.response.send_message(msg, ephemeral=True)
             except: await interaction.followup.send(msg, ephemeral=True)
             return
        
        # Get Stats (Power/Luck)
        power, luck, data, current_bait_key = await self.get_stats_multiplier(user_id)
        rod_key = data.get("rod_type", "Plastic Rod")
        
        # === DURABILITY CHECK ===
        durability_map = inventory.get("rod_durability", {})
        if rod_key not in durability_map:
             # Auto-fix missing durability
             max_d = RODS.get(rod_key, {}).get("durability")
             if max_d:
                 durability_map[rod_key] = max_d
             else:
                 # Infinite durability for Plastic/Donator
                 pass
        
        current_durability = durability_map.get(rod_key)
        
        # If rod has durability and it's 0 (should not happen if we check after use, but safety first)
        if current_durability is not None and current_durability <= 0:
             # Remove rod
             if rod_key in inventory.get("rods", []):
                 inventory["rods"].remove(rod_key)
                 if rod_key in durability_map: del durability_map[rod_key]
             
             await self.db.update_fishing_data(user_id, inventory=inventory, rod_type="Plastic Rod")
             msg = f"💥 **CẦN CÂU CỦA BẠN ĐÃ BỊ GÃY!**\nCần **{RODS[rod_key]['name']}** đã hỏng hoàn toàn. Hãy mua cần mới!"
             try: await interaction.response.send_message(msg, ephemeral=True)
             except: await interaction.followup.send(msg, ephemeral=True)
             return

        # Bait Consumption Logic
        baits_inv = inventory.get("baits", {})
        sub_bait_key = stats.get("magnet_sub_bait")
        bait_consumed = False
        is_magnet = (current_bait_key == "Magnet")
        loops = 1
        
        if current_durability is not None:
             # Logic change: Durability consumes per CAST (not per fish)
             # But if loops > 1 (Magnet), does it consume more? 
             # Standard: 1 cast = 1 durability, regardless of 1 or 5 fish.
             
             durability_map[rod_key] -= 1
             inventory["rod_durability"] = durability_map
             
             if durability_map[rod_key] <= 0:
                 # ROD BREAKS AFTER THIS CAST
                 # We let the cast finish, then notify break at the end? or check at end?
                 # Let's handle break at the end of function to allow receiving the fish.
                 pass

        if current_bait_key:
             if baits_inv.get(current_bait_key, 0) > 0:
                 baits_inv[current_bait_key] -= 1
                 bait_consumed = True
                 
                 if baits_inv[current_bait_key] <= 0:
                     if current_bait_key in baits_inv: del baits_inv[current_bait_key]
                     stats["current_bait"] = None
                 
                 if is_magnet:
                     loops = random.randint(2, 5) # Magnet: 2-5 fish
             else:
                 stats["current_bait"] = None
                 is_magnet = False

        # Treasure Chance (2% + Luck/50)
        treasure_chance = 2 + (luck * 0.05)
        treasure_found = False
        
        result_list = []
        
        total_xp = 0
        total_val = 0
        
        current_biome_data = BIOMES.get(biome_name, BIOMES["River"])
        fish_pool = current_biome_data["fish"]
        
        embed_color = discord.Color.blue()
        
        # Initialize variables for scope safety
        new_rod_type = None
        rod_broken_msg = ""
        
        if not treasure_found and random.uniform(0, 100) < treasure_chance:
            # TREASURE EVENT
            chest_idx = min(len(TREASURES)-1, int(random.triangular(0, len(TREASURES)-1, 0 + luck/50)))
            chest = TREASURES[chest_idx]
            
            # Loot Type: Coinz (35%), Fish (35%), Bait (20%), Charm (10%)
            loot_type = random.choices(["coiz", "fish", "bait", "charm"], weights=[35, 35, 20, 10], k=1)[0]
            reward_msg = ""
            
            if loot_type == "coiz":
                amount = int(chest["value"] * random.uniform(0.8, 1.5))
                # Update lifetime money? No, this is direct money.
                current_lt = stats.get("lifetime_money", 0)
                stats["lifetime_money"] = current_lt + amount
                
                await self.db.add_points(user_id, interaction.guild_id, amount)
                reward_msg = f"Bạn nhận được **{amount:,}** Coinz {emojis.ANIMATED_EMOJI_COIZ} từ rương!"
                
            elif loot_type == "fish":
                selected_fish = random.choice(fish_pool)
                min_qty = 1 + chest_idx
                max_qty = 3 + (chest_idx * 2)
                quantity = random.randint(min_qty, max_qty)
                
                unit_value = int(selected_fish['base_value'] * 1.2)
                total_f_val = unit_value * quantity
                
                if 'fish' not in inventory: inventory['fish'] = {}
                f_name = selected_fish['name']
                if f_name not in inventory['fish']:
                    inventory['fish'][f_name] = {"count": 0, "total_value": 0}
                
                inventory['fish'][f_name]["count"] += quantity
                inventory['fish'][f_name]["total_value"] += total_f_val
                
                stats["total_caught"] = stats.get("total_caught", 0) + quantity
                reward_msg = f"Bạn nhận được **{quantity}x {selected_fish['emoji']} {selected_fish['name']}** từ rương!"
                
            elif loot_type == "bait":
                 bait_keys = list(BAITS.keys())
                 selected_bait_key = random.choice(bait_keys)
                 selected_bait = BAITS[selected_bait_key]
                 
                 min_qty = 5 + (chest_idx * 2)
                 max_qty = 10 + (chest_idx * 5)
                 quantity = random.randint(min_qty, max_qty)
                 
                 if 'baits' not in inventory: inventory['baits'] = {}
                 inventory['baits'][selected_bait_key] = inventory['baits'].get(selected_bait_key, 0) + quantity
                 
                 reward_msg = f"Bạn nhận được **{quantity}x {selected_bait['emoji']} {selected_bait['name']}** từ rương!"

            elif loot_type == "charm":
                charm_keys = list(CHARMS.keys())
                c_key = random.choice(charm_keys)
                c_info = CHARMS[c_key]
                
                duration_min = c_info["duration_min"]
                duration_max = c_info["duration_max"]
                duration_sec = random.randint(duration_min * 60, duration_max * 60)
                
                if "charms" not in inventory: inventory["charms"] = []
                new_charm = {"key": c_key, "duration": duration_sec, "name": c_info["name"]}
                inventory["charms"].append(new_charm)
                
                minutes = duration_sec // 60
                reward_msg = f"Bạn nhận được **{c_info['emoji']} {c_info['name']}** ({minutes}p) từ rương!"

            embed = discord.Embed(title="🎁 KHO BÁU!", color=discord.Color.gold())
            embed.description = f"Bạn tìm thấy **{chest['emoji']} {chest['name']}**!\n{reward_msg}"
            
        else:
            # FISHING LOOP
            desc_lines = []
            
            for _ in range(loops):
                # Calculate current catch stats (handles Magnet Sub-Bait)
                eff_luck = luck
                eff_power = power
                
                # Logic for Sub-Bait (Magnet Only)
                if is_magnet and sub_bait_key:
                    if baits_inv.get(sub_bait_key, 0) > 0:
                        baits_inv[sub_bait_key] -= 1
                        if baits_inv[sub_bait_key] <= 0:
                            if sub_bait_key in baits_inv: del baits_inv[sub_bait_key]
                            stats["magnet_sub_bait"] = None
                            
                        sb_info = BAITS.get(sub_bait_key, {})
                        eff_luck += sb_info.get("luck", 0)
                        eff_power += sb_info.get("power", 0)
                    else:
                        stats["magnet_sub_bait"] = None

                # Rarity selection
                # Luck/Power affects weights? 
                
                luck_bonus = eff_luck * 0.15
                roll = random.uniform(0, 100) + luck_bonus
                
                rarity = "Common"
                if roll > 120: rarity = "Exotic" # Alien/Secret?
                elif roll > 110: rarity = "Mythical"
                elif roll > 95: rarity = "Legendary"
                elif roll > 80: rarity = "Epic"
                elif roll > 60: rarity = "Rare"
                elif roll > 40: rarity = "Uncommon"
                
                # Pick fish
                # Note: Currently fish_pool is list of dicts. We don't have explicit rarity in fish dicts in BIOMES constant yet?
                # The BIOMES constant has "fish": [{name, base_value, min, max, emoji}...]
                # We need to assign rarity or pick based on value?
                # For now, pick random fish from pool, then apply size multiplier based on power/rarity.
                
                if not fish_pool: break
                
                selected_fish = random.choice(fish_pool)
                # Size calculation
                # Power affects size directly
                # Size = Random(min, max) + Power * 0.1
                
                min_s = selected_fish['min_size']
                max_s = selected_fish['max_size']
                size = round(random.uniform(min_s, max_s) + (eff_power * 0.05), 2)
                
                # Value calculation
                # Value = Base * (Size / AvgSize) * RarityMult?
                # Simplify: Value = Base + (Size * 2)
                base_v = selected_fish['base_value']
                rarity_mul = RARITIES.get(rarity, {}).get("mul", 1.0)
                val = int((base_v + (size * 5)) * rarity_mul)
                
                # Crit?
                if random.random() < 0.05:
                    val *= 2
                    size_bonus = "(CRIT!)"
                
                # Add to result
                result_list.append({
                    "name": selected_fish['name'], 
                    "value": val, 
                    "emoji": selected_fish['emoji'],
                    "size": size,
                    "rarity": rarity
                })
                
                # Update Inventory
                if 'fish' not in inventory: inventory['fish'] = {}
                f_name = selected_fish['name']
                if f_name not in inventory['fish']:
                    inventory['fish'][f_name] = {"count": 0, "total_value": 0}
                    
                inventory['fish'][f_name]["count"] += 1
                inventory['fish'][f_name]["total_value"] += val
                
                stats["total_caught"] = stats.get("total_caught", 0) + 1
                
                total_xp += int(val / 10) + 5
                total_val += val
                
                # Get rarity info
                r_info = RARITIES.get(rarity, {"emoji": "✨", "color": 0xFFFFFF})
                r_emoji = r_info.get("emoji", "✨")
                
                # Translate rarity
                rarity_vi = {
                    "Common": "Thường", "Uncommon": "Khá", "Rare": "Hiếm", 
                    "Epic": "Sử Thi", "Legendary": "Huyền Thoại", 
                    "Mythical": "Thần Thoại", "Exotic": "Cực Phẩm"
                }.get(rarity, rarity)

                desc_lines.append(f"{r_emoji} **{rarity_vi}** | {selected_fish['emoji']} **{selected_fish['name']}** ({size}cm)")

            # Check Rod Break Status before creating Embed
            rod_broken_msg = ""
            user_dura = inventory.get("rod_durability", {}).get(rod_key)
            new_rod_type = None # Default: No change
            
            if user_dura is not None and user_dura <= 0:
                 # Remove rod from inventory
                 if "rods" in inventory and rod_key in inventory["rods"]:
                     inventory["rods"].remove(rod_key)
                 if "rod_durability" in inventory and rod_key in inventory["rod_durability"]:
                     del inventory["rod_durability"][rod_key]
                 
                 # Prepare to reset rod to Plastic
                 new_rod_type = "Plastic Rod"
                 rod_broken_msg = f"\n\n💥 **CẦN CÂU ĐÃ GÃY!**\nCần **{RODS[rod_key]['name']}** của bạn đã hỏng hoàn toàn do hết độ bền. Hãy mua cần mới!"

            title = "🎣 CÂU ĐƯỢC CÁ!"
            if is_magnet: title = f"🧲 NAM CHÂM HÚT ĐƯỢC {len(result_list)} CÁ!"
            
            embed = discord.Embed(title=title, color=embed_color)
            embed.description = "\n".join(desc_lines)
            embed.add_field(name="Tổng kết", value=f"Exp: +{total_xp} | Giá trị: {total_val:,} Coinz {emojis.ANIMATED_EMOJI_COIZ}{rod_broken_msg}")
            
            dura_info = ""
            if user_dura is not None:
                max_dura = RODS[rod_key]['durability']
                dura_info = f" | Độ bền: {max(0, user_dura)}/{max_dura}"
            
            # Level Up Logic
            current_level = stats.get("level", 1)
            current_xp = stats.get("xp", 0) + total_xp
            
            # Recalculate level
            # Formula: Next Level XP = 1000 * (1.5 ^ (level - 1))
            # Loop incase of multi-level up
            leveled_up = False
            while True:
                req_xp = int(1000 * (1.5 ** (current_level - 1)))
                if current_xp >= req_xp:
                    current_xp -= req_xp
                    current_level += 1
                    leveled_up = True
                else:
                    break
            
            stats["xp"] = current_xp
            stats["level"] = current_level
            
            if leveled_up:
                try:
                    await interaction.channel.send(f"🎉 **LEVEL UP!** Chúc mừng <@{user_id}> đã đạt **Level {current_level}**! Mở khóa các khu vực mới!")
                except: pass

            dura_info = ""
            if user_dura is not None:
                max_dura = RODS[rod_key]['durability']
                dura_info = f" | Độ bền: {max(0, user_dura)}/{max_dura}"
                
            req_xp_next = int(1000 * (1.5 ** (current_level - 1)))
            embed.set_footer(text=f"Level: {current_level} | XP: {current_xp}/{req_xp_next}{dura_info}")

        # Save Data
        save_kwargs = {"inventory": inventory, "stats": stats}
        if new_rod_type:
            save_kwargs["rod_type"] = new_rod_type
            
        await self.db.update_fishing_data(user_id, **save_kwargs)

        
        # Check Badges
        await self.check_badges(user_id, interaction.channel)
        
        # UI
        last_catch_data = result_list if result_list else None
        new_view = FishingView(self, user_id, biome_name, last_catch=last_catch_data)
        
        if view:
             new_view.message = view.message
             await view.message.edit(embed=embed, view=new_view)
        else:
             msg = await interaction.followup.send(embed=embed, view=new_view)
             new_view.message = msg






    @app_commands.command(name="fish", description="Bắt đầu câu cá!")
    async def fish(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        data = await self.db.get_fishing_data(interaction.user.id)
        current_biome = data.get("stats", {}).get("current_biome", "River") # Default to River now
        
        # Trigger fishing
        await self.process_fishing(interaction, current_biome)

    @app_commands.command(name="khu-vuc", description="Xem và di chuyển đến các khu vực câu cá")
    async def biomes_cmd(self, interaction: discord.Interaction):
        await self.show_biomes_ui(interaction)

    async def show_biomes_ui(self, interaction: discord.Interaction):
        data = await self.db.get_fishing_data(interaction.user.id)
        stats = data.get("stats", {})
        current = stats.get("current_biome", "River")
        unlocked = stats.get("unlocked_biomes", ["River"])
        # Ensure default unlock
        if "River" not in unlocked: 
            unlocked.append("River")
            stats["unlocked_biomes"] = unlocked
            await self.db.update_fishing_data(interaction.user.id, stats=stats) # Sync fix if needed
            
        xp = stats.get("xp", 0)
        level = stats.get("level", 1)
        
        curr_info = BIOMES.get(current, BIOMES["River"])
        
        embed = discord.Embed(title="🗺️ BẢN ĐỒ CÂU CÁ", color=discord.Color.teal())
        embed.description = f"Hiện tại đang ở: **{curr_info['emoji']} {curr_info['name']}**\nLevel: **{level}** | XP: **{xp:,}**"
        
        view = discord.ui.View()
        
        async def unlock_or_travel(interaction: discord.Interaction, biome_key: str):
            # Refresh data
            d = await self.db.get_fishing_data(interaction.user.id)
            s = d.get("stats", {})
            u = s.get("unlocked_biomes", ["River"])
            
            if biome_key in u:
                s["current_biome"] = biome_key
                await self.db.update_fishing_data(interaction.user.id, stats=s)
                b_info = BIOMES[biome_key]
                msg = f"✈️ Đã chuyển đến **{b_info['emoji']} {b_info['name']}**!"
                if interaction.response.is_done():
                     await interaction.followup.send(msg, ephemeral=True)
                else:
                     await interaction.response.send_message(msg, ephemeral=True)
            else:
                # Try unlock
                target = BIOMES[biome_key]
                cost = target["req_money"]
                req_level = target["req_level"]
                
                u_bal = await self.db.get_player_points(interaction.user.id, interaction.guild_id)
                curr_level = s.get("level", 1)
                
                if curr_level < req_level:
                    await interaction.response.send_message(f"❌ Bạn chưa đủ Level {req_level} để mở khóa!", ephemeral=True)
                    return
                # Show confirmation regardless of money (or check money here too?)
                # User asked: "if level is enough, show confirm button to use money"
                # It's better to verify money first to avoid disappointment, but let's follow logic:
                # Check money inside View or before? 
                # Let's check money here to give immediate feedback if too poor, 
                # BUT request says "confirm to use money", implying the choice happens then.
                # I will show the view if Level is met. The view handles money check.
                
                view_confirm = ConfirmUnlockView(self, interaction.user.id, biome_key, cost)
                msg_txt = f"🔓 **MỞ KHÓA VÙNG MỚI**\nBạn có muốn dùng **{cost:,} Coiz** {emojis.ANIMATED_EMOJI_COIZ} để mở khóa **{target['emoji']} {target['name']}** không?"
                
                if interaction.response.is_done():
                    await interaction.followup.send(msg_txt, view=view_confirm, ephemeral=True)
                else:
                    await interaction.response.send_message(msg_txt, view=view_confirm, ephemeral=True)

        select = discord.ui.Select(placeholder="Chọn khu vực để đi...")
        
        for key, info in BIOMES.items():
            label = info['name']
            is_unlocked = key in unlocked
            desc_s = "Đã mở khóa (Nhấn để đi)" if is_unlocked else f"Yêu cầu: Level {info['req_level']} | {info['req_money']:,} Coiz"
            emoji = info['emoji']
            select.add_option(label=label, value=key, description=desc_s, emoji=emoji)
        
        async def select_callback(inter):
            val = select.values[0]
            await unlock_or_travel(inter, val)
        
        select.callback = select_callback
        view.add_item(select)
        
        if interaction.response.is_done():
             await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
             await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="shop", description="🏪 Mở cửa hàng vật phẩm (Mồi, Cần, Bùa)")
    async def shop(self, interaction: discord.Interaction):
        view = ShopSelectView(self)
        await interaction.response.send_message("🏪 **CHÀO MỪNG ĐẾN CỬA HÀNG!**\nBạn muốn xem loại hàng nào?", view=view, ephemeral=True)

    @app_commands.command(name="moi-cau", description="Cửa hàng mồi câu (Mua số lượng tùy ý)")
    async def bait_shop(self, interaction: discord.Interaction):
        # 1. Embed listing all baits
        embed = discord.Embed(title="🪱 CỬA HÀNG MỒI CÂU", description="Chọn loại mồi bạn muốn mua bên dưới.", color=discord.Color.dark_green())
        
        for key, info in BAITS.items():
            if info.get("is_special"): continue # Skip special items if not purchasable? Or keep magnet?
            # User mentioned price for 1 bait
            embed.add_field(
                name=f"{info['emoji']} {info['name']}",
                value=f"� Giá: **{info['price']:,}** Coinz {emojis.ANIMATED_EMOJI_COIZ}/cái\n�💪 Power: +{info['power']} | 🍀 Luck: +{info['luck']}\n*{info['desc']}*",
                inline=False
            )
            
        # 2. View with Buttons for each bait
        view = discord.ui.View()
        
        # Define Modal locally or as a class
        class BaitAmountModal(discord.ui.Modal):
            def __init__(self, bait_key, bait_info, db, parent_view):
                super().__init__(title=f"Mua {bait_info['name']}")
                self.bait_key = bait_key
                self.bait_info = bait_info
                self.db = db
                self.parent_view = parent_view
                
                self.amount = discord.ui.TextInput(
                    label="Số lượng cần mua",
                    placeholder="Ví dụ: 10, 50, 100...",
                    min_length=1,
                    max_length=5,
                    required=True
                )
                self.add_item(self.amount)

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    qty = int(self.amount.value)
                    if qty <= 0: raise ValueError
                except ValueError:
                    await interaction.response.send_message("❌ Số lượng không hợp lệ!", ephemeral=True)
                    return
                
                cost = self.bait_info["price"] * qty
                user_point = await self.db.get_player_points(interaction.user.id, interaction.guild_id)
                
                if user_point < cost:
                    await interaction.response.send_message(f"❌ Bạn không đủ **{cost:,}** Coinz {emojis.ANIMATED_EMOJI_COIZ} để mua {qty}x {self.bait_info['name']}!", ephemeral=True)
                    return
                
                # Proceed Transaction
                await self.db.add_points(interaction.user.id, interaction.guild_id, -cost)
                
                data = await self.db.get_fishing_data(interaction.user.id)
                inv = data.get("inventory", {})
                if "baits" not in inv: inv["baits"] = {}
                
                inv["baits"][self.bait_key] = inv["baits"].get(self.bait_key, 0) + qty
                
                # Auto equip if none
                stats = data.get("stats", {})
                if not stats.get("current_bait"):
                    stats["current_bait"] = self.bait_key
                
                await self.db.update_fishing_data(interaction.user.id, inventory=inv, stats=stats)
                
                await interaction.response.send_message(f"✅ Đã mua thành công **{qty}x {self.bait_info['emoji']} {self.bait_info['name']}** với giá **{cost:,}** Coinz {emojis.ANIMATED_EMOJI_COIZ}!", ephemeral=True)

        async def bait_button_callback(interaction: discord.Interaction):
            # Hacky way to get the button that was clicked
            # But we can bind specific callback
            pass

        # Dynamically create buttons
        for key, info in BAITS.items():
            # if info.get("is_special"): continue 
            # Allow Magnet buying? Yes, user asked for magnet earlier.
            
            btn = discord.ui.Button(label=info['name'], emoji=info['emoji'], style=discord.ButtonStyle.secondary)
            
            # Closure to capture key variable
            async def callback(inter, k=key, i=info):
                modal = BaitAmountModal(k, i, self.db, view)
                await inter.response.send_modal(modal)
            
            btn.callback = callback
            view.add_item(btn)

        back_btn = discord.ui.Button(label="Trang Chủ", style=discord.ButtonStyle.secondary, emoji="🏠", row=2)
        async def back_callback(inter):
            if inter.user.id != interaction.user.id: return
            view = ShopSelectView(self)
            await inter.response.edit_message(content="🏪 **CHÀO MỪNG ĐẾN CỬA HÀNG!**\nBạn muốn xem loại hàng nào?", embed=None, view=view)
        back_btn.callback = back_callback
        view.add_item(back_btn)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="can-cau", description="Cửa hàng Cần câu (Chọn mua theo ý thích)")
    async def rod_shop(self, interaction: discord.Interaction):
        # 1. Embed listing all rods
        user_id = interaction.user.id
        data = await self.db.get_fishing_data(user_id)
        current_rod_key = data.get("rod_type", "Plastic Rod")
        current_rod_info = RODS.get(current_rod_key, RODS["Plastic Rod"])

        embed = discord.Embed(title="🎣 CỬA HÀNG CẦN CÂU", description=f"Cần câu hiện tại: **{current_rod_info['emoji']} {current_rod_info['name']}**", color=discord.Color.blue())
        
        buyable_rods = []
        for key in ROD_LIST:
            info = RODS[key]
            if info["price"] > 0:
                buyable_rods.append((key, info))
                embed.add_field(
                    name=f"{info['emoji']} {info['name']}",
                    value=f"💰 Giá: **{info['price']:,}** Coinz {emojis.ANIMATED_EMOJI_COIZ}\n💪 Power: {info['power']} | 🍀 Luck: {info['luck']} | 🔧 Độ bền: {info['durability']}",
                    inline=False
                )
        
        # 2. View with Buttons
        view = discord.ui.View()
        
        class ConfirmBuyView(discord.ui.View):
            def __init__(self, rod_key, rod_info, db, parent_interaction):
                super().__init__(timeout=60)
                self.rod_key = rod_key
                self.rod_info = rod_info
                self.db = db
                self.value = None
                
            @discord.ui.button(label="Xác nhận mua", style=discord.ButtonStyle.success, emoji="✅")
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Check prerequisites
                data = await self.db.get_fishing_data(interaction.user.id)
                inv = data.get("inventory", {})
                owned_rods = inv.get("rods", ["Plastic Rod"])
                if not owned_rods: owned_rods = ["Plastic Rod"]

                if self.rod_key in owned_rods:
                     await interaction.response.edit_message(content="❌ Bạn đã sở hữu cần này rồi!", view=None)
                     return

                # Check strict progression
                try:
                    curr_idx = ROD_LIST.index(self.rod_key)
                    if curr_idx > 0:
                        prev_rod = ROD_LIST[curr_idx - 1]
                        if prev_rod not in owned_rods:
                             prev_rod_name = RODS.get(prev_rod, {}).get("name", prev_rod)
                             await interaction.response.edit_message(content=f"❌ Bạn cần sở hữu **{prev_rod_name}** trước khi mua cần này!", view=None)
                             return
                except ValueError:
                    pass # Rod key not in list? Should not happen if data is consistent

                user_point = await self.db.get_player_points(interaction.user.id, interaction.guild_id)
                cost = self.rod_info["price"]
                
                if user_point < cost:
                    await interaction.response.edit_message(content="❌ Bạn không đủ tiền!", view=None)
                    return

                await self.db.add_points(interaction.user.id, interaction.guild_id, -cost)
                
                # Update Inventory and Equip
                if "rods" not in inv: inv["rods"] = owned_rods
                if self.rod_key not in inv["rods"]:
                    inv["rods"].append(self.rod_key)
                    
                # Initialize Durability
                if "rod_durability" not in inv: inv["rod_durability"] = {}
                inv["rod_durability"][self.rod_key] = RODS[self.rod_key]["durability"]
                
                await self.db.update_fishing_data(interaction.user.id, rod_type=self.rod_key, inventory=inv)
                
                await interaction.response.edit_message(content=f"🎉 Chúc mừng! Bạn đã sở hữu **{self.rod_info['emoji']} {self.rod_info['name']}**!", view=None)
                self.value = True
                self.stop()

            @discord.ui.button(label="Hủy bỏ", style=discord.ButtonStyle.danger, emoji="❌")
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.edit_message(content="Đã hủy giao dịch.", view=None)
                self.value = False
                self.stop()

        for key, info in buyable_rods:
            # Button for each rod
            # Style update: highlight if current? discord buttons don't support custom css.
            style = discord.ButtonStyle.primary if key == current_rod_key else discord.ButtonStyle.secondary
            if key == current_rod_key:
                # Add durability info to label if possible
                dura = data.get("inventory", {}).get("rod_durability", {}).get(key)
                max_dura = info.get("durability")
                d_str = ""
                if dura is not None and max_dura:
                    d_str = f" [{dura}/{max_dura}]"
                label = f"{info['name']} (Đang dùng){d_str}"
                disabled = True
            else:
                label = info['name']
                disabled = False
                
            btn = discord.ui.Button(label=label, emoji=info['emoji'], style=style, disabled=disabled)
            
            async def callback(inter, k=key, i=info):
                # Trigger Confirmation
                confirm_view = ConfirmBuyView(k, i, self.db, inter)
                await inter.response.send_message(
                    f"Bạn có chắc muốn mua **{i['emoji']} {i['name']}** với giá **{i['price']:,}** Coinz {emojis.ANIMATED_EMOJI_COIZ} không?",
                    view=confirm_view,
                    ephemeral=True
                )
            
            btn.callback = callback
            view.add_item(btn)

        back_btn = discord.ui.Button(label="Trang Chủ", style=discord.ButtonStyle.secondary, emoji="🏠", row=4)
        async def back_callback(inter):
            if inter.user.id != interaction.user.id: return
            view = ShopSelectView(self)
            await inter.response.edit_message(content="🏪 **CHÀO MỪNG ĐẾN CỬA HÀNG!**\nBạn muốn xem loại hàng nào?", embed=None, view=view)
        back_btn.callback = back_callback
        view.add_item(back_btn)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="inventory", description="Xem túi cá và vật phẩm")
    async def inventory(self, interaction: discord.Interaction):
        data = await self.db.get_fishing_data(interaction.user.id)
        current_rod = data.get("rod_type", "Plastic Rod")
        
        # Default view shows current rod or summary?
        # Let's show Rods by default or just the menu with instruction
        
        embed = discord.Embed(title=f"🎒 TÚI ĐỒ CỦA {interaction.user.display_name.upper()}", description="Chọn danh mục bên dưới để xem chi tiết.", color=discord.Color.gold())
        
        view = InventoryView(self, interaction.user.id, data)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="fish-stats", description="Xem thông số câu cá, Level, Rank")
    async def fish_stats_cmd(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        power, luck, data, bait_key = await self.get_stats_multiplier(user_id)
        stats = data.get("stats", {})
        
        level = stats.get("level", 1)
        xp = stats.get("xp", 0)
        req_xp = int(1000 * (1.5 ** (level - 1)))
        
        # Calculate Rank
        rank = await self.db.get_fishing_rank(user_id)
        
        # Progress Bar
        pct = min(1.0, xp / max(1, req_xp))
        bar_len = 10
        filled = int(pct * bar_len)
        bar = "🟦" * filled + "⬜" * (bar_len - filled)
        
        embed = discord.Embed(title=f"📊 THÔNG SỐ CẦN THỦ: {interaction.user.display_name}", color=discord.Color.purple())
        
        embed.add_field(name="🏅 Xếp Hạng", value=f"TOP **#{rank}**", inline=True)
        embed.add_field(name="⭐ Cấp Độ", value=f"**Level {level}**\n{bar}\n({xp}/{req_xp} XP)", inline=True)
        
        # Buff Details
        rod_key = data.get("rod_type", "Plastic Rod")
        rod_info = RODS.get(rod_key, {})
        
        bait_info = BAITS.get(bait_key, {"power": 0, "luck": 0}) if bait_key else {"power": 0, "luck": 0}
        
        active_charms = stats.get("active_charms", {})
        charm_power = power - rod_info.get("power",0) - bait_info.get("power",0)
        charm_luck = luck - rod_info.get("luck",0) - bait_info.get("luck",0)

        buff_desc = (
            f"⚔️ **POWER: {power}** (Rod: {rod_info.get('power',0)} + Bait: {bait_info.get('power',0)} + Charm: {charm_power})\n"
            f"🍀 **LUCK: {luck}** (Rod: {rod_info.get('luck',0)} + Bait: {bait_info.get('luck',0)} + Charm: {charm_luck})"
        )
        embed.add_field(name="💪 Chỉ Số Sức Mạnh", value=buff_desc, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="Bán tất cả cá")
    async def sell(self, interaction: discord.Interaction):
        data = await self.db.get_fishing_data(interaction.user.id)
        inv = data.get("inventory", {})
        fish_inv = inv.get("fish", {})
        
        if not fish_inv:
             await interaction.response.send_message("🎒 Không có cá để bán!", ephemeral=True)
             return

        total_payout = 0
        for name, info in fish_inv.items():
            total_payout += info.get("total_value", 0)
            
        if total_payout == 0:
             await interaction.response.send_message("🎒 Không có cá có giá trị để bán!", ephemeral=True)
             return

        # Clear fish
        inv["fish"] = {}
        
        stats = data.get("stats", {})
        stats["lifetime_money"] = stats.get("lifetime_money", 0) + total_payout
        
        await self.db.update_fishing_data(interaction.user.id, inventory=inv, stats=stats)
        await self.db.add_points(interaction.user.id, interaction.guild_id, total_payout)
        
        await self.check_badges(interaction.user.id, interaction.channel)
        
        await interaction.response.send_message(f"💰 Đã bán sạch cá và nhận được **{total_payout:,}** Coinz {emojis.ANIMATED_EMOJI_COIZ}!")

async def setup(bot: commands.Bot):
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(CauCaCog(bot, db))
