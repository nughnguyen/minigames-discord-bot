"""
Game Cog - Chứa tất cả logic chính của trò chơi nối từ
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional
import random
import time
import json
import aiosqlite

import config
from utils import embeds, emojis
from utils.validator import WordValidator
from database.db_manager import DatabaseManager


class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.validators = {}  # Cache validators cho mỗi ngôn ngữ
        self.active_timeouts = {}  # Track timeout tasks
        
    async def cog_load(self):
        """Load word lists khi cog được load"""
        await self.load_word_lists()
    
    async def load_word_lists(self):
        """Load danh sách từ cho các ngôn ngữ"""
        # Tiếng Việt
        try:
            with open(config.WORDS_VI_PATH, 'r', encoding='utf-8') as f:
                words_vi = [line.strip() for line in f if line.strip()]
            self.validators['vi'] = WordValidator('vi', words_vi)
            print(f"✅ Loaded {len(words_vi)} Vietnamese words")
        except Exception as e:
            print(f"❌ Error loading Vietnamese words: {e}")
        
        # Tiếng Anh
        try:
            with open(config.WORDS_EN_PATH, 'r', encoding='utf-8') as f:
                words_en = [line.strip() for line in f if line.strip()]
            self.validators['en'] = WordValidator('en', words_en)
            print(f"✅ Loaded {len(words_en)} English words")
        except Exception as e:
            print(f"❌ Error loading English words: {e}")
    
    def get_random_word(self, language: str) -> str:
        """Lấy từ ngẫu nhiên để bắt đầu game"""
        validator = self.validators.get(language)
        if validator:
            return random.choice(list(validator.word_list))
        return "start" if language == "en" else "bat dau"
    
    async def start_wordchain(
        self, 
        interaction: discord.Interaction,
        language: str = None
    ):
        """Bắt đầu game với Button UI"""
        # Handle if language is passed as Choice object (legacy support or if re-added) or string
        if hasattr(language, 'value'):
            lang = language.value
        elif isinstance(language, str):
            lang = language
        else:
            lang = config.DEFAULT_LANGUAGE
        
        if await self.db.is_game_active(interaction.channel_id):
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Đã có game đang chơi!",
                ephemeral=True
            )
            return
        
        if lang not in self.validators:
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Ngôn ngữ '{lang}' chưa được hỗ trợ!",
                ephemeral=True
            )
            return
        
        # ===== BUTTON UI REGISTRATION =====
        from utils.views import RegistrationView
        
        lang_flag = "🇻🇳" if lang == "vi" else "🇬🇧"
        lang_name = "Tiếng Việt" if lang == "vi" else "English"
        reg_end_time = int(time.time() + config.REGISTRATION_TIMEOUT)
        
        reg_embed = discord.Embed(
            title=f"{emojis.START} Đăng Ký Tham Gia Game!",
            description=f"**Ngôn ngữ:** {lang_flag} {lang_name}\n⏳ Kết thúc đăng ký: <t:{reg_end_time}:R>",
            color=config.COLOR_INFO
        )
        
        reg_embed.add_field(
            name="👥 Đã Đăng Ký (0 người)",
            value="Chưa có ai",
            inline=False
        )
        
        reg_embed.add_field(
            name="📋 Hướng Dẫn",
            value=(
                f"• Nhấn **📝 Đăng Ký** để tham gia\n"
                f"• <@{interaction.user.id}> nhấn **🎮 Bắt Đầu**\n"
                f"• Mỗi lượt: **{config.TURN_TIMEOUT}s**\n"
                f"• English: Từ phải có tối thiểu **3 chữ cái**"
            ),
            inline=False
        )
        
        view = RegistrationView(host_id=interaction.user.id, timeout=config.REGISTRATION_TIMEOUT)
        await interaction.response.send_message(embed=reg_embed, view=view)
        
        # Wait for start button
        await view.wait()
        
        if not view.game_started:
            return
        
        registered_players = list(view.registered_players)
        channel = interaction.channel
        
        # ===== GAME START =====
        is_bot_challenge = len(registered_players) == 1
        
        if is_bot_challenge:
            first_player_id = registered_players[0]
            players_list = [first_player_id]
        else:
            random.shuffle(registered_players)
            players_list = registered_players
            first_player_id = players_list[0]
        
        first_word = self.get_random_word(lang)
        
        await self.db.create_game(
            channel_id=channel.id,
            guild_id=interaction.guild_id,
            language=lang,
            first_word=first_word,
            first_player_id=first_player_id,
            is_bot_challenge=is_bot_challenge
        )
        

        async with aiosqlite.connect(config.DATABASE_PATH) as db:
            await db.execute(
                "UPDATE game_states SET players = ?, turn_start_time = ? WHERE channel_id = ?",
                (json.dumps(players_list), time.time(), channel.id)
            )
            await db.commit()
        
        start_embed = discord.Embed(
            title=f"{emojis.START} Game Bắt Đầu! {emojis.CELEBRATION}",
            description=f"**Ngôn ngữ:** {lang_flag} {lang_name}",
            color=config.COLOR_SUCCESS
        )
        
        start_embed.add_field(
            name=f"{emojis.SCROLL} Từ Đầu Tiên",
            value=f"```{first_word.upper()}```",
            inline=False
        )
        
        if is_bot_challenge:
            start_embed.add_field(
                name=f"🎮 Chế Độ",
                value=f"{emojis.ROBOT} **Bot Đưa Từ - Bạn Nối**",
                inline=False
            )
            turn_end = int(time.time() + config.TURN_TIMEOUT)
            start_embed.add_field(
                name=f"{emojis.TIMEOUT} Lượt Của Bạn",
                value=f"<@{first_player_id}> - Nối từ: **{first_word.upper()}**\nKết thúc: <t:{turn_end}:R>",
                inline=False
            )
        else:
            order_text = ""
            for idx, pid in enumerate(players_list, 1):
                player = interaction.guild.get_member(pid)
                marker = f"{emojis.FIRE} **→**" if pid == first_player_id else "  "
                order_text += f"{marker} **{idx}.** {player.mention}\n"
            
            start_embed.add_field(
                name=f"👥 Thứ Tự ({len(players_list)} người)",
                value=order_text,
                inline=False
            )
            turn_end = int(time.time() + config.TURN_TIMEOUT)
            start_embed.add_field(
                name=f"{emojis.TIMEOUT} Lượt Hiện Tại",
                value=f"<@{first_player_id}> - Kết thúc: <t:{turn_end}:R>",
                inline=False
            )
        
        await channel.send(embed=start_embed)
        await self.start_turn_timeout(channel.id, first_player_id)

    
    async def stop_wordchain(self, interaction: discord.Interaction):
        """Kết thúc game"""
        # Kiểm tra có game không
        game_state = await self.db.get_game_state(interaction.channel_id)
        if not game_state:
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Không có game nào đang chơi!",
                ephemeral=True
            )
            return
        
        # Cancel timeout nếu có
        if interaction.channel_id in self.active_timeouts:
            self.active_timeouts[interaction.channel_id].cancel()
            del self.active_timeouts[interaction.channel_id]
        
        # Tìm người thắng (người có nhiều điểm nhất trong phiên)
        scores = game_state.get('scores', {})
        winner_id = None
        session_points = 0
        total_points = 0
        
        if scores:
            # scores keys are stored as strings in JSON
            best_uid_str = max(scores, key=scores.get)
            winner_id = int(best_uid_str)
            session_points = scores[best_uid_str]
            # Lấy tổng điểm
            total_points = await self.db.get_player_points(winner_id, interaction.guild_id)
        
        # Lưu lịch sử
        await self.db.save_game_history(
            channel_id=interaction.channel_id,
            guild_id=interaction.guild_id,
            language=game_state['language'],
            winner_id=winner_id,
            total_turns=game_state['turn_count'],
            total_words=len(game_state['used_words']),
            started_at=game_state['started_at']
        )
        
        # Xóa game
        await self.db.delete_game(interaction.channel_id)
        
        # Thông báo kết thúc
        winner_data = {
            'user_id': winner_id, 
            'session_points': session_points,
            'total_points': total_points
        } if winner_id else None
        
        embed = embeds.create_game_end_embed(
            winner_data=winner_data,
            total_turns=game_state['turn_count'],
            used_words_count=len(game_state['used_words'])
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="status", description="📊 Xem trạng thái game hiện tại")
    async def status(self, interaction: discord.Interaction):
        """Hiển thị trạng thái game"""
        game_state = await self.db.get_game_state(interaction.channel_id)
        
        if not game_state:
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Không có game nào đang chơi!",
                ephemeral=True
            )
            return
        
        # Tạo embed status
        status_data = {
            'current_word': game_state['current_word'],
            'current_player': game_state['current_player_id'],
            'words_used': len(game_state['used_words']),
            'turn_count': game_state['turn_count']
        }
        
        embed = embeds.create_status_embed(status_data)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="hint", description="💡 Nhận gợi ý (tốn 100 coiz)")
    async def hint(self, interaction: discord.Interaction):
        """Gợi ý chữ cái tiếp theo"""
        game_state = await self.db.get_game_state(interaction.channel_id)
        
        if not game_state:
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Không có game nào đang chơi!",
                ephemeral=True
            )
            return
        
        # Kiểm tra điểm
        points = await self.db.get_player_points(interaction.user.id, interaction.guild_id)
        if points < config.HINT_COST:
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Bạn không đủ Coiz! Cần {config.HINT_COST} Coiz, bạn chỉ có {points} Coiz {emojis.ANIMATED_EMOJI_COIZ}",
                ephemeral=True
            )
            return
        
        # Trừ điểm
        await self.db.add_points(interaction.user.id, interaction.guild_id, -config.HINT_COST)
        await self.db.update_game_score(interaction.channel_id, interaction.user.id, -config.HINT_COST)
        
        # Lấy gợi ý
        validator = self.validators[game_state['language']]
        hint_char = validator.suggest_next_char(game_state['current_word'])
        
        # Gửi gợi ý
        embed = embeds.create_hint_embed(hint_char, config.HINT_COST)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="pass", description="⏭️ Bỏ lượt (tốn 20 Coiz)")
    async def pass_turn(self, interaction: discord.Interaction):
        """Bỏ lượt không bị trừ coiz timeout"""
        game_state = await self.db.get_game_state(interaction.channel_id)
        
        if not game_state:
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Không có game nào đang chơi!",
                ephemeral=True
            )
            return
        
        # Kiểm tra có phải lượt của người này không
        if game_state['current_player_id'] != interaction.user.id:
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Không phải lượt của bạn!",
                ephemeral=True
            )
            return
        
        # Kiểm tra điểm
        points = await self.db.get_player_points(interaction.user.id, interaction.guild_id)
        if points < config.PASS_COST:
            await interaction.response.send_message(
                f"{emojis.ANIMATED_EMOJI_WRONG} Bạn không đủ Coiz! Cần {config.PASS_COST} Coiz, bạn chỉ có {points} Coiz {emojis.ANIMATED_EMOJI_COIZ}",
                ephemeral=True
            )
            return
        
        # Trừ điểm
        await self.db.add_points(interaction.user.id, interaction.guild_id, -config.PASS_COST)
        await self.db.update_game_score(interaction.channel_id, interaction.user.id, -config.PASS_COST)
        
        # Chuyển lượt (giữ nguyên từ hiện tại)
        # Tìm người chơi tiếp theo (không phải bot challenge)
        next_player = self.get_next_player(game_state, interaction.user.id)
        
        # Cancel timeout cũ
        if interaction.channel_id in self.active_timeouts:
            self.active_timeouts[interaction.channel_id].cancel()
        
        # Cập nhật database
        await self.db.update_game_turn(
            channel_id=interaction.channel_id,
            new_word=game_state['current_word'],  # Giữ nguyên từ
            next_player_id=next_player.id
        )
        
        # Thông báo
        await interaction.response.send_message(
            f"{emojis.PASS} {interaction.user.mention} đã bỏ lượt! (-{config.PASS_COST} Coiz {emojis.ANIMATED_EMOJI_COIZ})\n"
            f"Lượt tiếp theo: {next_player.mention}"
        )
        
        # Bắt đầu timeout mới
        await self.start_turn_timeout(interaction.channel_id, next_player.id)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Lắng nghe tin nhắn để check từ nối"""
        # Bỏ qua tin nhắn của bot
        if message.author.bot:
            return
        
        # Kiểm tra có game không
        game_state = await self.db.get_game_state(message.channel.id)
        if not game_state:
            return
        
        # Kiểm tra có phải lượt của người này không
        if game_state['current_player_id'] != message.author.id:
            return
        
        # Lấy từ người dùng gửi
        word = message.content.strip().lower()
        
        # Validate từ
        validator = self.validators[game_state['language']]
        
        # [V2] Min length validation (English)
        if game_state['language'] == 'en' and len(word) < config.MIN_WORD_LENGTH_EN:
            await self.handle_wrong_answer(message, game_state, word, f"Từ tiếng Anh phải có ít nhất **{config.MIN_WORD_LENGTH_EN} chữ cái**!")
            return

        # Kiểm tra từ đã dùng chưa
        if word in game_state['used_words']:
            await self.handle_wrong_answer(message, game_state, word, "Từ này đã được sử dụng rồi!")
            return
        
        # Kiểm tra nối từ đúng không
        can_chain, reason = await validator.can_chain(game_state['current_word'], word)
        
        if not can_chain:
            await self.handle_wrong_answer(message, game_state, word, reason)
            return
        
        # ĐÚNG!
        # Cancel timeout
        if message.channel.id in self.active_timeouts:
            self.active_timeouts[message.channel.id].cancel()
        
        # [V2] Calculate points with Time Bonus
        import time
        points = config.POINTS_CORRECT # 10 points base
        bonus_list = []
        
        # Time Bonus
        turn_start = game_state.get('turn_start_time', 0)
        if turn_start > 0:
            elapsed = time.time() - turn_start
            if elapsed < 5:
                # Siêu tốc (<5s) - 100% Base (100 points)
                points += 100 
                bonus_list.append(f"⚡ Siêu tốc! (+100 {emojis.ANIMATED_EMOJI_COIZ})")
            elif elapsed < 10:
                # Nhanh (<10s) - 50% Base (50 points)
                points += 50
                bonus_list.append(f"🏃 Nhanh! (+50 {emojis.ANIMATED_EMOJI_COIZ})")
            elif elapsed < 20:
                # Khá (<20s) - 20% Base (20 points)
                points += 20
                bonus_list.append(f"🙂 Khá! (+20 {emojis.ANIMATED_EMOJI_COIZ})")
        
        # Word Length/Advanced Bonus
        word_info = None
        meaning_vi = None
        is_advanced = False
        
        if game_state['language'] == 'en':
            # Get Vietnamese meaning for ALL English words
            if validator.cambridge_api:
                meaning_vi = await validator.cambridge_api.get_vietnamese_meaning(word)

            # Check length bonus
            # Check dictionary for advanced status or long status
            # Check dictionary for level or long status
            word_info = await validator.cambridge_api.get_word_info(word, 'en')
            
            level_points = 0
            if word_info and word_info.get('level'):
                level = word_info['level']
                level_points = config.LEVEL_BONUS.get(level, 0)
                
                if level_points > 0:
                    points += level_points
                    bonus_list.append(f"📚 Level {level.upper()}! (+{level_points} {emojis.ANIMATED_EMOJI_COIZ})")
            
            # Fallback to long word bonus if no level bonus was awarded
            if level_points == 0 and len(word) >= config.LONG_WORD_THRESHOLD:
                points += config.POINTS_LONG_WORD # 200 points
                bonus_list.append(f"📝 Từ dài! (+{config.POINTS_LONG_WORD} {emojis.ANIMATED_EMOJI_COIZ})")
                
        elif validator.is_long_word(word):
            points += config.POINTS_LONG_WORD # 20 points
            bonus_list.append(f"{emojis.FIRE} Từ dài! (+{config.POINTS_LONG_WORD} {emojis.ANIMATED_EMOJI_COIZ})")
            
        bonus_reason = "\n".join(bonus_list)
        
        # Cập nhật điểm và stats
        await self.db.add_points(message.author.id, message.guild.id, points)
        await self.db.update_game_score(message.channel.id, message.author.id, points)
        await self.db.update_player_stats(message.author.id, message.guild.id, word, True)
        
        # Tìm người chơi tiếp theo
        next_player = self.get_next_player(game_state, message.author.id)
        
        # Cập nhật game state (Reset wrong attempts here is handled by update_game_turn setting it to 0)
        await self.db.update_game_turn(
            channel_id=message.channel.id,
            new_word=word,
            next_player_id=next_player.id
        )
        
        # Gửi thông báo (Gộp Chính xác + Nghĩa)
        embeds_list = embeds.create_rich_correct_answer_embed(
            author=message.author,
            word=word,
            word_info=word_info,
            meaning_vi=meaning_vi,
            points=points,
            bonus_reason=bonus_reason
        )
        
        await message.channel.send(embeds=embeds_list)
        
        # Check if bot challenge (solo mode)
        if game_state['is_bot_challenge']:
            # Bot mode: Bot đưa từ mới ngay lập tức
            await asyncio.sleep(1.5)  # Small delay for realism
            
            # Bot picks next word
            validator = self.validators[game_state['language']]
            next_char = validator.get_last_char(word)
            bot_word = validator.get_bot_word(next_char, set(game_state['used_words']))
            
            if not bot_word:
                # Bot cannot find word - Player wins!
                win_embed = discord.Embed(
                    title=f"{emojis.EMOJI_GIVEAWAY} Bạn Thắng!",
                    description=f"{emojis.ROBOT} Bot không tìm được từ nào tiếp theo!\n\n🏆 Chúc mừng!",
                    color=config.COLOR_GOLD
                )
                await message.channel.send(embed=win_embed)
                await self.db.delete_game(message.channel.id)
                return
            
            # Update game với từ mới của bot
            await self.db.update_game_turn(
                channel_id=message.channel.id,
                new_word=bot_word,
                next_player_id=message.author.id  # Back to player
            )
            
            # Bot announces new word
            turn_end = int(time.time() + config.TURN_TIMEOUT)
            bot_embed = discord.Embed(
                title=f"{emojis.ROBOT} Bot Đưa Từ Mới",
                description=f"```{bot_word.upper()}```",
                color=config.COLOR_INFO
            )
            bot_embed.add_field(
                name=f"⏰ Lượt Của Bạn",
                value=f"{message.author.mention} - Hãy nối từ!\nKết thúc: <t:{turn_end}:R>",
                inline=False
            )
            await message.channel.send(embed=bot_embed)
            
            # Start timeout for player's next turn
            await self.start_turn_timeout(message.channel.id, message.author.id)
        else:
            # Multi-player mode: Normal turn rotation
            next_player = self.get_next_player(game_state, message.author.id)
            
            # Update game state
            await self.db.update_game_turn(
                channel_id=message.channel.id,
                new_word=word,
                next_player_id=next_player.id
            )
            
            # Start timeout cho người chơi tiếp
            await self.start_turn_timeout(message.channel.id, next_player.id)
    
    def get_next_player(self, game_state: dict, current_user_id: int) -> discord.User:
        """Lấy người chơi tiếp theo"""
        players = game_state['players']
        current_index = players.index(current_user_id)
        next_index = (current_index + 1) % len(players)
        next_player_id = players[next_index]
        
        # Nếu chỉ có 1 người chơi, trả về chính họ
        return self.bot.get_user(next_player_id) or self.bot.get_user(current_user_id)
    
    async def bot_play_turn(self, channel: discord.TextChannel, game_state: dict, previous_word: str):
        """Bot tự động chơi (cho bot challenge)"""
        await asyncio.sleep(2)  # Delay để realistic
        
        validator = self.validators[game_state['language']]
        next_char = validator.get_last_char(previous_word)
        
        # Bot chọn từ khó
        bot_word = validator.get_bot_word(next_char, set(game_state['used_words']))
        
        if not bot_word:
            # Bot không tìm được từ -> người chơi thắng
            await channel.send(
                f"{emojis.ROBOT} Bot không tìm được từ nào! {emojis.CELEBRATION} Bạn thắng!"
            )
            # Kết thúc game
            await self.db.delete_game(channel.id)
            return
        
        # Bot gửi từ
        await channel.send(f"{emojis.ROBOT} Bot: **{bot_word.upper()}**")
        
        # Cập nhật game
        human_player = game_state['players'][0]  # Người chơi là người đầu tiên
        await self.db.update_game_turn(
            channel_id=channel.id,
            new_word=bot_word,
            next_player_id=human_player
        )
        
        # Bắt đầu timeout cho người chơi
        await self.start_turn_timeout(channel.id, human_player)
    
    async def start_turn_timeout(self, channel_id: int, player_id: int):
        """Bắt đầu đếm ngược timeout"""
        # Cancel timeout cũ nếu có
        if channel_id in self.active_timeouts:
            self.active_timeouts[channel_id].cancel()
        
        # Tạo task mới
        task = asyncio.create_task(self.timeout_handler(channel_id, player_id))
        self.active_timeouts[channel_id] = task
    
    async def timeout_handler(self, channel_id: int, player_id: int):
        """Xử lý khi hết thời gian"""
        try:
            await asyncio.sleep(config.TURN_TIMEOUT)
            
            # Lấy game state
            game_state = await self.db.get_game_state(channel_id)
            if not game_state:
                return
            
            # Kiểm tra xem người chơi có đúng là người timeout không
            if game_state['current_player_id'] != player_id:
                return  # Đã chuyển lượt rồi
            
            # Trừ coiz timeout (-10)
            channel = self.bot.get_channel(channel_id)
            player = self.bot.get_user(player_id)
            
            await self.db.add_points(player_id, game_state['guild_id'], config.POINTS_TIMEOUT)
            await self.db.update_game_score(channel_id, player_id, config.POINTS_TIMEOUT)
            
            # Gửi thông báo timeout
            embed = embeds.create_timeout_embed(player.mention)
            # Override description to show correct penalty
            embed.description = f"{player.mention} {emojis.SNAIL} đã không trả lời kịp thời! (-{abs(config.POINTS_TIMEOUT)} Coiz {emojis.ANIMATED_EMOJI_COIZ})"
            await channel.send(embed=embed)
            
            # Chuyển lượt
            next_player = self.get_next_player(game_state, player_id)
            await self.db.update_game_turn(
                channel_id=channel_id,
                new_word=game_state['current_word'],  # Giữ nguyên từ
                next_player_id=next_player.id
            )
            
            await channel.send(f"Lượt tiếp theo: {next_player.mention}")
            
            # Bắt đầu timeout mới
            await self.start_turn_timeout(channel_id, next_player.id)
            
        except asyncio.CancelledError:
            # Task bị cancel (người chơi đã trả lời kịp)
            pass



    async def handle_wrong_answer(self, message, game_state, word, reason):
        """Xử lý trả lời sai"""
        current_wrong = game_state.get('wrong_attempts', 0) + 1
        
        # Tính coiz trừ tích lũy: 2, 4, 6... (Mỗi lần sai -2)
        # Hoặc đơn giản là mỗi lần sai trừ 2 coiz, user yêu cầu "trừ tối đa 10 coiz" cho 5 lần
        # -> Nghĩa là lần 1 trừ 2, lần 2 trừ 2... tổng 5 lần là 10.
        penalty = config.POINTS_WRONG # -2
        
        await self.db.add_points(message.author.id, message.guild.id, penalty)
        await self.db.update_game_score(message.channel.id, message.author.id, penalty)
        await self.db.update_player_stats(message.author.id, message.guild.id, word, False)
        
        # Update wrong attempts count
        await self.db.update_wrong_attempts(message.channel.id, current_wrong)
        
        # Check limit
        if current_wrong >= config.MAX_WRONG_ATTEMPTS:
            embed = discord.Embed(
                title=f"{emojis.SKULL} Mất Lượt!",
                description=f"{message.author.mention} đã trả lời sai quá {config.MAX_WRONG_ATTEMPTS} lần!\nTự động chuyển lượt.",
                color=config.COLOR_ERROR
            )
            await message.channel.send(embed=embed)
            
            # Chuyển lượt
            next_player = self.get_next_player(game_state, message.author.id)
            
            # Cancel timeout cũ
            if message.channel.id in self.active_timeouts:
                self.active_timeouts[message.channel.id].cancel()
                
            await self.db.update_game_turn(
                channel_id=message.channel.id,
                new_word=game_state['current_word'],
                next_player_id=next_player.id
            )
            
            await message.channel.send(f"Lượt tiếp theo: {next_player.mention}")
            await self.start_turn_timeout(message.channel.id, next_player.id)
        else:
            # Chỉ báo sai và số lần còn lại
            remaining = config.MAX_WRONG_ATTEMPTS - current_wrong
            embed = embeds.create_wrong_answer_embed(
                message.author.mention,
                word,
                f"{reason}\n⚠️ Bạn còn **{remaining}** lần thử. (Bị trừ {abs(penalty)} Coiz {emojis.ANIMATED_EMOJI_COIZ})"
            )
            await message.channel.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function cho cog"""
    db = DatabaseManager(config.DATABASE_PATH)
    await db.initialize()
    await bot.add_cog(GameCog(bot, db))
