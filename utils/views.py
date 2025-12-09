"""
Registration View - Discord Buttons for player registration
"""
import discord
from discord import ui
import asyncio
from typing import Set


class RegistrationView(ui.View):
    """
    View with buttons for game registration
    - 📝 Đăng Ký button: Anyone can click to join
    - 🎮 Bắt Đầu button: Host only, starts the game
    """
    
    def __init__(self, host_id: int, timeout: int = None):
        super().__init__(timeout=timeout)
        self.host_id = host_id
        self.registered_players: Set[int] = set()
        self.game_started = False
        
    @ui.button(label="Đăng Ký", emoji="📝", style=discord.ButtonStyle.primary, custom_id="register")
    async def register_button(self, interaction: discord.Interaction, button: ui.Button):
        """Register player for the game"""
        user_id = interaction.user.id
        
        if user_id in self.registered_players:
            await interaction.response.send_message(
                "✅ Bạn đã đăng ký rồi!",
                ephemeral=True
            )
            return
        
        # Add player to registered list
        self.registered_players.add(user_id)
        
        # Update the message
        embed = interaction.message.embeds[0]
        # Update player count in embed
        for idx, field in enumerate(embed.fields):
            if field.name.startswith("👥"):
                player_list = "\n".join([f"• <@{pid}>" for pid in self.registered_players]) if self.registered_players else "Chưa có ai"
                embed.set_field_at(
                    idx,
                    name=f"👥 Đã Đăng Ký ({len(self.registered_players)} người)",
                    value=player_list,
                    inline=False
                )
                break
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Send confirmation
        await interaction.followup.send(
            f"✅ {interaction.user.mention} đã đăng ký thành công!",
            ephemeral=False
        )
    
    @ui.button(label="Bắt Đầu", emoji="🎮", style=discord.ButtonStyle.success, custom_id="start")
    async def start_button(self, interaction: discord.Interaction, button: ui.Button):
        """Start the game (host only)"""
        # Check if user is host
        if interaction.user.id != self.host_id:
            await interaction.response.send_message(
                f"❌ Chỉ <@{self.host_id}> (người tạo game) mới có thể bắt đầu!",
                ephemeral=True
            )
            return
        
        # Check if enough players
        if len(self.registered_players) < 1:
            await interaction.response.send_message(
                "❌ Cần ít nhất 1 người đăng ký để bắt đầu!",
                ephemeral=True
            )
            return
        
        # Mark game as started
        self.game_started = True
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        # Update message
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Game Đang Bắt Đầu..."
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Stop the view
        self.stop()
    
    @ui.button(label="Hủy", emoji="❌", style=discord.ButtonStyle.danger, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        """Cancel the game (host only)"""
        if interaction.user.id != self.host_id:
            await interaction.response.send_message(
                f"❌ Chỉ <@{self.host_id}> (người tạo game) mới có thể hủy!",
                ephemeral=True
            )
            return
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        # Update message
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Game Đã Bị Hủy"
        
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Stop the view
        self.stop()
