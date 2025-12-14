import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import config
from utils import emojis
from database.db_manager import DatabaseManager

class BetModal(discord.ui.Modal):
    def __init__(self, side_name, side_emoji, current_balance, callback_func):
        super().__init__(title=f"Đặt Cược: {side_name}")
        self.current_balance = current_balance
        self.callback_func = callback_func
        self.side_name = side_name
        self.side_emoji = side_emoji

        self.amount = discord.ui.TextInput(
            label=f"Số tiền cược (Có: {current_balance:,})",
            placeholder="Nhập số tiền hoặc 'all' để tất tay...",
            min_length=1,
            max_length=20, # Increase length just in case
            required=True
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            raw_value = self.amount.value.lower().strip()
            
            if raw_value in ["all", "all in", "tat ca", "hết"]:
                 amount = self.current_balance
            else:
                 amount = int(self.amount.value.replace(',', '').replace('.', ''))
            
            if amount <= 0:
                await interaction.response.send_message("❌ Số tiền cược phải lớn hơn 0!", ephemeral=True)
                return
            
            # Check logic, but don't deduct yet.
            # However, we need to track "potential spend" to prevent over-betting across multiple clicks
            # callback_func handles the validation of "locked" funds.
            await self.callback_func(interaction, amount, self.side_name, self.side_emoji)

        except ValueError:
            await interaction.response.send_message("❌ Vui lòng nhập số hợp lệ!", ephemeral=True)

class PlayAgainView(discord.ui.View):
    def __init__(self, host_id, timeout=60):
        super().__init__(timeout=timeout)
        self.host_id = host_id
        self.choice = None
        self.next_interaction = None

    @discord.ui.button(label="Chơi Tiếp", style=discord.ButtonStyle.success)
    async def continue_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_id:
             await interaction.response.send_message("❌ Chỉ chủ phòng mới được chọn!", ephemeral=True)
             return
        self.choice = "continue"
        self.next_interaction = interaction
        self.stop()

    @discord.ui.button(label="Dừng Lại", style=discord.ButtonStyle.danger)
    async def stop_game(self, interaction: discord.Interaction, button: discord.ui.Button):
         if interaction.user.id != self.host_id:
             await interaction.response.send_message("❌ Chỉ chủ phòng mới được chọn!", ephemeral=True)
             return
         self.choice = "stop"
         self.next_interaction = interaction
         self.stop()

class BauCuaView(discord.ui.View):
    def __init__(self, bot, db, host_id, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.db = db
        self.host_id = host_id
        self.bets = {} # {user_id: {side: amount}}
        self.user_total_bet = {} # {user_id: total_amount}
        self.locked_balance = {} # {user_id: locked_amount}
        self.message = None
        self.stop_event = asyncio.Event()
        
        # Define sides with names and emojis
        self.sides = [
            {"id": "side_1", "name": "Nai", "emoji": emojis.SIDE_1},
            {"id": "side_2", "name": "Bầu", "emoji": emojis.SIDE_2},
            {"id": "side_3", "name": "Mèo", "emoji": emojis.SIDE_3},
            {"id": "side_4", "name": "Cá", "emoji": emojis.SIDE_4},
            {"id": "side_5", "name": "Cua", "emoji": emojis.SIDE_5},
            {"id": "side_6", "name": "Tôm", "emoji": emojis.SIDE_6},
        ]

        # Add betting buttons
        for i, side in enumerate(self.sides):
            btn = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                emoji=side['emoji'],
                label=f" {side['name']} ", # Add spaces for width
                custom_id=side['id'],
                row=0 if self.sides.index(side) < 3 else 1
            )
            btn.callback = self.create_callback(side)
            self.add_item(btn)

        # Control buttons
        self.spin_btn = discord.ui.Button(
            label="QUAY NGAY!", 
            style=discord.ButtonStyle.success,
            emoji="🎲",
            row=2,
            custom_id="spin_now"
        )
        self.spin_btn.callback = self.spin_callback
        self.add_item(self.spin_btn)

    def create_callback(self, side):
        async def callback(interaction: discord.Interaction):
            # Check current balance
            points = await self.db.get_player_points(interaction.user.id, interaction.guild_id)
            locked = self.locked_balance.get(interaction.user.id, 0)
            available = points - locked
            
            modal = BetModal(
                side_name=side['name'], 
                side_emoji=side['emoji'],
                current_balance=available, # Pass available balance for UI hint
                callback_func=self.process_bet
            )
            await interaction.response.send_modal(modal)
        return callback

    async def process_bet(self, interaction: discord.Interaction, amount, side_name, side_emoji):
        user_id = interaction.user.id
        
        # Re-verify funds with lock
        points = await self.db.get_player_points(interaction.user.id, interaction.guild_id)
        locked = self.locked_balance.get(user_id, 0)
        
        if (locked + amount) > points:
            await interaction.response.send_message(f"❌ Bạn không đủ tiền! (Đã cược: {locked:,}, muốn cược thêm: {amount:,})", ephemeral=True)
            return

        # Lock funds (don't deduct from DB yet)
        self.locked_balance[user_id] = locked + amount
        new_locked = self.locked_balance[user_id]
        
        if user_id not in self.bets:
            self.bets[user_id] = {}
            self.user_total_bet[user_id] = 0
            
        current_side_bet = self.bets[user_id].get(side_name, 0)
        self.bets[user_id][side_name] = current_side_bet + amount
        self.user_total_bet[user_id] += amount
        
        remaining = points - new_locked
        
        await interaction.response.send_message(
            f"✅ Đã cược **{amount:,}** coinz {emojis.ANIMATED_EMOJI_COINZ} vào {side_emoji} {side_name}!\n"
            f"Số dư khả dụng: **{remaining:,}** coinz {emojis.ANIMATED_EMOJI_COINZ}", 
            ephemeral=True
        )
        # Note: We do NOT call update_embed here anymore to avoid rate-limit clashes with the animation loop.
        # The animation loop (running every 1s) will pick up the new bet state automatically.

    async def spin_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("❌ Chỉ người tạo phòng mới được bấm quay!", ephemeral=True)
            return
        
        self.stop_event.set() # Stop animation
        await interaction.response.defer()
        self.stop() # Stop interactions

    async def update_embed(self):
        if not self.message: return
        try:
            embed = self.message.embeds[0]
            
            # Update TOTAL BETS field (Index 0)
            total_pot = sum(self.user_total_bet.values())
            total_players = len(self.bets)
            embed.set_field_at(0, name="💰 Tổng Cược", value=f"**{total_pot:,}** coinz {emojis.ANIMATED_EMOJI_COINZ} ({total_players} người chơi)", inline=False)
            
            # Update BET LIST field (Index 1)
            bet_details = []
            for uid, user_bets in self.bets.items():
                b_str = []
                for s_name, amt in user_bets.items():
                    s_emoji = next((s['emoji'] for s in self.sides if s['name'] == s_name), "")
                    b_str.append(f"{s_emoji} {amt:,}")
                bet_details.append(f"<@{uid}>: " + " | ".join(b_str))
            
            val = "\n".join(bet_details) if bet_details else "Chưa có cược"
            if len(val) > 1024: val = val[:1000] + "..."
            
            if len(embed.fields) > 1:
                embed.set_field_at(1, name="📝 Danh sách cược", value=val, inline=False)
            else:
                embed.add_field(name="📝 Danh sách cược", value=val, inline=False)

            await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"Error updating embed: {e}")

class BauCuaCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.sides_map = {
            "Nai": emojis.SIDE_1,
            "Bầu": emojis.SIDE_2,
            "Mèo": emojis.SIDE_3,
            "Cá": emojis.SIDE_4,
            "Cua": emojis.SIDE_5,
            "Tôm": emojis.SIDE_6
        }
        self.sides_list = list(self.sides_map.keys())
        self.emoji_list = [emojis.SIDE_1, emojis.SIDE_2, emojis.SIDE_3, emojis.SIDE_4, emojis.SIDE_5, emojis.SIDE_6]

    async def animate_waiting(self, view: BauCuaView):
        """Keeps the embed updated while waiting"""
        while not view.stop_event.is_set():
            if view.message:
                try:
                    # Only update betting info, no animation needed
                    await view.update_embed()

                except Exception as e:
                    print(f"Update error: {e}")
            
            # Wait 1.0s to refresh betting info
            await asyncio.sleep(1.0)

    async def start_game(self, interaction: discord.Interaction):
        host_id = interaction.user.id
        current_interaction = interaction
        
        while True:
            # Run the round
            await self.run_round(current_interaction)
            
            # Ask to continue
            play_again_view = PlayAgainView(host_id)
            try:
                msg = await current_interaction.channel.send(
                    f"**{interaction.user.display_name}**, bạn có muốn tiếp tục chơi Bầu Cua không?", 
                    view=play_again_view
                )
            except Exception:
                # Channel might be gone or no perms
                break
            
            await play_again_view.wait()
            
            if play_again_view.choice == "continue":
                current_interaction = play_again_view.next_interaction
                # Delete the prompt message to clean up? Optional.
                try:
                    await msg.delete()
                except:
                    pass
                continue
            else:
                if play_again_view.next_interaction:
                    await play_again_view.next_interaction.response.send_message("👋 Cảm ơn đã chơi! Hẹn gặp lại.", ephemeral=True)
                else:
                    # Timeout
                    pass 
                    # await current_interaction.channel.send("👋 Game đã kết thúc do hết thời gian chờ!")
                
                # Try to disable buttons on the prompt
                try:
                    await msg.edit(view=None)
                except:
                    pass
                break

    async def run_round(self, interaction: discord.Interaction):
        # Initial Embed
        embed = discord.Embed(
            title="🎲 BẦU CUA TÔM CÁ (Space Edition) 🎲",
            description=(
                f"Hãy đặt cược vào các cửa bên dưới!\n"
                f"Tối đa cược: **500,000** coinz/lần\n"
                f"Người tạo phòng: {interaction.user.mention}\n"
                f"⚠️ Tiền sẽ được trừ và cộng sau khi quay xong!"
            ),
            color=config.COLOR_INFO
        )
        
        # Pre-add "Total Bet" field at index 0
        embed.add_field(name="💰 Tổng Cược", value="**0** coinz {emojis.ANIMATED_EMOJI_COINZ} (0 người chơi)", inline=False)
        
        # Set static image
        embed.set_image(url="https://media.discordapp.net/attachments/1449574237734965311/1449574316361519175/bau-cua.jpg?ex=693f64c8&is=693e1348&hm=55e841a05991f0f8d26114203ffb8b28def31e942729034aaa7cd0245f46ef58&=&format=webp&width=1240&height=829")
        
        # Add "Bet List" field placeholder at index 1
        embed.add_field(name="� Danh sách cược", value="Chưa có cược", inline=False)

        view = BauCuaView(self.bot, self.db, interaction.user.id, timeout=120)
        
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        
        # Start animation task
        anim_task = asyncio.create_task(self.animate_waiting(view))
        
        # Wait for timeout or manual stop
        await view.wait()
        
        # Ensure animation stops
        view.stop_event.set()
        await asyncio.sleep(0.5) # Allow task to finish logic
        anim_task.cancel()

        # Deduct Money First (Validation Phase)
        # We need to check if they STILL have money (since we didn't lock it in DB)
        # If they don't, we invalidate the bet.
        
        valid_bets = {} # {uid: {side: valid_amount}}
        
        current_balances = {} # cache to avoid spamming DB
        
        for uid, user_bets in view.bets.items():
            total_bet_req = sum(user_bets.values())
            
            # Get fresh balance
            if uid not in current_balances:
                current_balances[uid] = await self.db.get_player_points(uid, interaction.guild_id)
            
            balance = current_balances[uid]
            
            if balance >= total_bet_req:
                # Valid
                valid_bets[uid] = user_bets
                # Deduct now
                await self.db.add_points(uid, interaction.guild_id, -total_bet_req)
                current_balances[uid] -= total_bet_req
            else:
                # Not enough funds anymore!
                user = self.bot.get_user(uid)
                name = user.name if user else uid
                try:
                     await interaction.channel.send(f"⚠️ <@{uid}> không đủ tiền để thực hiện cược (Cần: {total_bet_req}, Có: {balance}). Hủy cược!")
                except: pass
        
        # Determine Results
        
        # Animation: 3 Loading -> Reveal
        load_embed = discord.Embed(
            title="🎲 ĐANG QUAY...",
            description="",
            color=config.COLOR_WARNING
        )
        
        # Helper to format reveal
        def format_reveal(revealed_indices, results):
            # 3 slots.
            slots = []
            for i in range(3):
                if i in revealed_indices:
                    slots.append(self.sides_map[results[i]])
                else:
                    slots.append(emojis.LOADING)
            return " | ".join(slots)

        result_names = [random.choice(self.sides_list) for _ in range(3)]
        
        # Step 0: All Loading
        load_embed.description = f"# {emojis.LOADING} | {emojis.LOADING} | {emojis.LOADING}"
        await view.message.edit(embed=load_embed, view=None)
        await asyncio.sleep(1.5)
        
        # Step 1: Reveal 1
        load_embed.description = f"# {format_reveal([0], result_names)}"
        await view.message.edit(embed=load_embed)
        await asyncio.sleep(1.5)
        
        # Step 2: Reveal 2
        load_embed.description = f"# {format_reveal([0, 1], result_names)}"
        await view.message.edit(embed=load_embed)
        await asyncio.sleep(1.5)
         
        # Step 3: Reveal 3 (Final)
        final_desc = f"# {format_reveal([0, 1, 2], result_names)}"
        load_embed.description = final_desc
        await view.message.edit(embed=load_embed)
        await asyncio.sleep(1)

        
        # Calculate Winnings & Summary
        summary_lines = []
        
        for user_id, user_bets in valid_bets.items():
            total_bet = sum(user_bets.values())
            total_payout = 0
            win_details = []
            
            for side_name, amount in user_bets.items():
                count = result_names.count(side_name)
                if count > 0:
                    profit = amount * count
                    # Payout = Bet + Profit
                    payout_for_side = amount + profit
                    total_payout += payout_for_side
                    
                    side_emoji = self.sides_map[side_name]
                    # Format: 🐟 x2 (+Bonus)
                    win_details.append(f"{side_emoji} x{count} (+{profit:,})")

            # Update DB if payout > 0
            if total_payout > 0:
                await self.db.add_points(user_id, interaction.guild_id, total_payout)

            net_outcome = total_payout - total_bet
            user_mention = f"<@{user_id}>"
            
            if net_outcome > 0:
                # Winner
                detail_str = ", ".join(win_details)
                line = f"🎉 {user_mention}: **+{net_outcome:,}** {emojis.ANIMATED_EMOJI_COINZ}\n   ╚ {detail_str}"
                summary_lines.append(line)
            elif net_outcome == 0:
                # Break even
                line = f"😐 {user_mention}: **Hòa vốn** {emojis.ANIMATED_EMOJI_COINZ}"
                summary_lines.append(line)
            else:
                # Loser
                # Show negative amount
                line = f"💸 {user_mention}: **{net_outcome:,}** {emojis.ANIMATED_EMOJI_COINZ}"
                summary_lines.append(line)

        # Final Result Embed
        result_emojis = [self.sides_map[name] for name in result_names]
        result_str = " ".join(result_emojis)
        end_embed = discord.Embed(
            title=f"🎲 KẾT QUẢ: {result_str}",
            color=config.COLOR_SUCCESS
        )
        end_embed.description = final_desc + "\n\n"
        
        if summary_lines:
            end_embed.add_field(name="📊 Tổng Kết", value="\n".join(summary_lines), inline=False)
        else:
            end_embed.add_field(name="😅 Kết Quả", value="Không có người chơi nào đặt cược!", inline=False)
            
        await view.message.edit(embed=end_embed)

    async def stop_game(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ Game Bầu Cua tự động kết thúc sau khi quay. Hãy bấm nút 'QUAY NGAY'!", ephemeral=True)

async def setup(bot: commands.Bot):
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(BauCuaCog(bot, db))
