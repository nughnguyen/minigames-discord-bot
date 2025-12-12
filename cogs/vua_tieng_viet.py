import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import asyncio
import config
from database.db_manager import DatabaseManager

class VuaTiengVietCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.active_games = {} # channel_id -> {"answer": str, "scrambled": str, "state": str, "total_chars": int, "revealed_indices": set, "timer_task": Task}
        self.questions = []
        self.load_questions()

    async def cog_load(self):
        self.load_questions()

    def load_questions(self):
        try:
            with open(config.DATA_VUA_TIENG_VIET_PATH, 'r', encoding='utf-8') as f:
                self.questions = json.load(f)
            print(f"✅ Loaded {len(self.questions)} Vua Tieng Viet questions")
        except Exception as e:
            print(f"❌ Error loading Vua Tieng Viet questions: {e}")
            self.questions = ["Lỗi tải câu hỏi"]

    def shuffle_word(self, text):
        # Remove spaces and special characters for scrambling
        clean_text = "".join(filter(str.isalnum, text)).lower()
        chars = list(clean_text)
        random.shuffle(chars)
        return "/".join(chars)

    def generate_hint_text(self, question, revealed_indices):
        words = question.split()
        hint_parts = []
        global_idx = 0
        for word in words:
            word_parts = []
            for char in word:
                if char.isalnum():
                    if global_idx in revealed_indices:
                        word_parts.append(char.upper())
                    else:
                        word_parts.append("⬜")
                    global_idx += 1
            if word_parts:
                hint_parts.append("\u00A0".join(word_parts))
        return " - ".join(hint_parts)

    def cancel_timer(self, channel_id):
        if channel_id in self.active_games:
            task = self.active_games[channel_id].get("timer_task")
            if task and not task.done():
                task.cancel()

    async def hint_timer(self, channel, correct_answer):
        try:
            while True:
                await asyncio.sleep(45)
                if channel.id not in self.active_games: return
                
                game_data = self.active_games[channel.id]
                if game_data["answer"] != correct_answer or game_data["state"] != "playing": return
                
                revealed = game_data["revealed_indices"]
                total_chars = game_data["total_chars"]
                
                available = [i for i in range(total_chars) if i not in revealed]
                if available:
                    pick = random.choice(available)
                    revealed.add(pick)
                    
                    new_hint = self.generate_hint_text(correct_answer, revealed)
                    scrambled = game_data["scrambled"]
                    
                    embed = discord.Embed(
                        title="👑 Vua Tiếng Việt - Gợi Ý", 
                        description="⏳ Đã qua 45s! Bot mở giúp bạn 1 ô chữ:", 
                        color=0xFFA500
                    )
                    embed.add_field(name="Câu hỏi", value=f"**```\n{scrambled.upper()}\n```**", inline=False)
                    embed.add_field(name="Gợi ý đang mở", value=f"**{new_hint}**", inline=False)
                    embed.set_footer(text="⚠️ Điểm thưởng sẽ bị trừ tương ứng với số ô được mở sẵn.")
                    
                    await channel.send(embed=embed)
                else:
                    # No more chars to reveal
                    break
        except asyncio.CancelledError:
            pass

    async def start_new_round(self, channel):
        # Cancel any existing timer for this channel
        self.cancel_timer(channel.id)

        if not self.questions:
            await channel.send("❌ Không có dữ liệu câu hỏi!")
            return

        question = random.choice(self.questions)
        scrambled = self.shuffle_word(question)
        
        # Retry shuffle if it happens to match original
        attempts = 0
        clean_question = "".join(filter(str.isalnum, question)).lower()
        while scrambled.replace('/', '') == clean_question and len(clean_question) > 1 and attempts < 5:
             scrambled = self.shuffle_word(question)
             attempts += 1
        
        # Setup game data
        total_chars = len(clean_question)
        revealed_indices = set()
        
        # Calculate hint (visual blocks) using helper
        hint_text = self.generate_hint_text(question, revealed_indices)

        embed = discord.Embed(
            title="👑 Vua Tiếng Việt", 
            description="Sắp xếp các chữ cái sau thành từ/câu có nghĩa:", 
            color=0xFFD700
        )
        embed.add_field(name="Câu hỏi", value=f"**```\n{scrambled.upper()}\n```**", inline=False)
        embed.add_field(name="Gợi ý số chữ", value=f"**{hint_text}**", inline=False)
        embed.set_footer(text=f"Gõ câu trả lời chính xác vào kênh chat! Phần thưởng: {config.POINTS_VUA_TIENG_VIET} coinz!")

        await channel.send(embed=embed)
        
        # Create timer task
        task = self.bot.loop.create_task(self.hint_timer(channel, question))

        self.active_games[channel.id] = {
            "answer": question,
            "scrambled": scrambled,
            "state": "playing",
            "total_chars": total_chars,
            "revealed_indices": revealed_indices,
            "timer_task": task
        }

    async def start_game(self, interaction: discord.Interaction):
        """Bắt đầu game Vua Tiếng Việt"""
        if interaction.channel_id in self.active_games:
             await interaction.response.send_message("❌ Đang có game diễn ra ở kênh này! Hãy hoàn thành hoặc dùng lệnh stop.", ephemeral=True)
             return

        # Acknowledge the command
        await interaction.response.send_message("🎮 Bắt đầu chuỗi game Vua Tiếng Việt!", ephemeral=True)
        # Start the first round
        await self.start_new_round(interaction.channel)

    async def stop_game(self, interaction: discord.Interaction):
        """Dừng game Vua Tiếng Việt"""
        if interaction.channel_id in self.active_games:
            self.cancel_timer(interaction.channel_id)
            game_data = self.active_games.pop(interaction.channel_id)
            # If state was waiting, there is no current answer to show, or we can just say stopped.
            msg = "🛑 Game đã kết thúc!"
            if game_data.get("state") == "playing":
                msg += f" Đáp án là: **{game_data['answer']}**"
            
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("❌ Không có game Vua Tiếng Việt nào đang diễn ra ở đây.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot: return
        if message.channel.id not in self.active_games: return

        game_data = self.active_games[message.channel.id]
        
        # If in waiting state (between rounds), ignore messages
        if game_data.get("state") != "playing":
            return

        correct_answer = game_data["answer"]
        
        user_clean = " ".join(message.content.lower().split())
        target_clean = " ".join(correct_answer.lower().split())

        if user_clean == target_clean:
            # Winner!
            self.cancel_timer(message.channel.id)
            
            # Set state to waiting to prevent double triggers
            self.active_games[message.channel.id]["state"] = "waiting"
            
            base_points = config.POINTS_VUA_TIENG_VIET
            revealed_count = len(game_data.get("revealed_indices", []))
            total_chars = game_data.get("total_chars", 1)
            
            # Determine Base Points based on length
            if len(correct_answer) > 25:
                current_base_points = config.POINTS_VUA_TIENG_VIET * 10 # 50,000
            elif len(correct_answer) > 15:
                current_base_points = 10000
            else:
                current_base_points = config.POINTS_VUA_TIENG_VIET
            
            # Formula: Points * (Total - Revealed) / Total
            points = int(current_base_points * (total_chars - revealed_count) / total_chars)
            
            await self.db.add_points(message.author.id, message.guild.id, points)
            
            embed = discord.Embed(title="🎉 CHÚC MỪNG CHIẾN THẮNG!", color=0x00FF00)
            embed.description = f"👑 {message.author.mention} đã trả lời chính xác!\n\nĐáp án: **{correct_answer}**"
            embed.add_field(name="Phần thưởng", value=f"💰 +{points:,} coinz\n(Trừ gợi ý: -{current_base_points - points:,})", inline=False)
            
            if len(correct_answer) > 25:
               embed.set_footer(text="🔥 CÂU HỎI *SIÊU KHÓ* > 25 KÝ TỰ: x10 QUỸ THƯỞNG (50,000)! 🔥")
            elif len(correct_answer) > 15:
               embed.set_footer(text="🔥 CÂU HỎI *KHÓ* > 15 KÝ TỰ: QUỸ THƯỞNG 10,000! 🔥")
            else:
               embed.set_footer(text="Chuẩn bị câu tiếp theo trong 5 giây...")
            
            await message.channel.send(embed=embed)
            
            # Wait a bit before next round
            await asyncio.sleep(5)
            
            # Check if game was stopped during sleep
            if message.channel.id in self.active_games:
                await self.start_new_round(message.channel)

async def setup(bot: commands.Bot):
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(VuaTiengVietCog(bot, db))
