import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import copy
import config
from database.db_manager import DatabaseManager
from utils import emojis

# Game Constants
NUM_ROWS = 18
NUM_COLS = 10
EMPTY_SQUARE = ':black_large_square:'
BLUE_SQUARE = ':blue_square:'
BROWN_SQUARE = ':brown_square:'
ORANGE_SQUARE = ':orange_square:'
YELLOW_SQUARE = ':yellow_square:'
GREEN_SQUARE = ':green_square:'
PURPLE_SQUARE = ':purple_square:'
RED_SQUARE = ':red_square:'
EMBED_COLOUR = 0x077ff7

class Tetronimo:
    def __init__(self, starting_pos, colour, rotation_points):
        self.starting_pos = starting_pos # list of [row, col]
        self.colour = colour
        self.rotation_points = rotation_points # list

# Tetronimo definitions
SHAPE_I = Tetronimo([[0, 3], [0, 4], [0, 5], [0, 6]], BLUE_SQUARE, [1, 1, 1, 1])
SHAPE_J = Tetronimo([[0, 3], [0, 4], [0, 5], [-1, 3]], BROWN_SQUARE, [1, 1, 2, 2])
SHAPE_L = Tetronimo([[0, 3], [0, 4], [0, 5], [-1, 5]], ORANGE_SQUARE, [1, 2, 2, 1])
SHAPE_O = Tetronimo([[0, 4], [0, 5], [-1, 4], [-1, 5]], YELLOW_SQUARE, [1, 1, 1, 1])
SHAPE_S = Tetronimo([[0, 3], [0, 4], [-1, 4], [-1, 5]], GREEN_SQUARE, [2, 2, 2, 2])
SHAPE_T = Tetronimo([[0, 3], [0, 4], [0, 5], [-1, 4]], PURPLE_SQUARE, [1, 1, 3, 0])
SHAPE_Z = Tetronimo([[0, 4], [0, 5], [-1, 3], [-1, 4]], RED_SQUARE, [0, 1, 0, 2])

ALL_SHAPES = [SHAPE_I, SHAPE_J, SHAPE_L, SHAPE_O, SHAPE_S, SHAPE_T, SHAPE_Z]

# Wall Kicks
MAIN_WALL_KICKS = [
    [[0, 0], [0, -1], [-1, -1], [2, 0], [2, -1]],
    [[0, 0], [0, 1], [1, 1], [-2, 0], [-2, 1]],
    [[0, 0], [0, 1], [-1, 1], [2, 0], [2, 1]],
    [[0, 0], [0, -1], [1, -1], [-2, 0], [-2, -1]]
]

I_WALL_KICKS = [
    [[0, 0], [0, -2], [0, 1], [1, -2], [-2, 1]],
    [[0, 0], [0, -1], [0, 2], [-2, -1], [1, 2]],
    [[0, 0], [0, 2], [0, -1], [-1, 2], [2, -1]],
    [[0, 0], [0, 1], [0, -2], [2, 1], [-1, -2]]
]

ROT_ADJUSTMENTS = {
    BLUE_SQUARE: [[0, 1], [-1, -1], [0, 0], [-1, 0]],
    BROWN_SQUARE: [[0, 0], [0, 1], [0, 0], [0, -1]],
    ORANGE_SQUARE: [[0, -1], [0, 0], [-1, 1], [0, 0]],
    YELLOW_SQUARE: [[0, 0], [0, 0], [0, 0], [0, 0]],
    GREEN_SQUARE: [[0, 0], [0, 0], [0, 0], [0, 0]],
    PURPLE_SQUARE: [[0, 0], [1, 1], [0, -1], [0, 1]],
    RED_SQUARE: [[1, -1], [-1, -1], [0, 2], [-1, -1]]
}

class XepHinhView(discord.ui.View):
    def __init__(self, cog, channel_id, player_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.channel_id = channel_id
        self.player_id = player_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("Không phải lượt chơi của bạn!", ephemeral=True)
            return False
        return True

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.primary, custom_id="left")
    async def left_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.handle_input(self.channel_id, 'left')
        await interaction.response.defer()

    @discord.ui.button(emoji="⬇️", style=discord.ButtonStyle.primary, custom_id="down")
    async def down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.handle_input(self.channel_id, 'down')
        await interaction.response.defer()

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.primary, custom_id="right")
    async def right_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.handle_input(self.channel_id, 'right')
        await interaction.response.defer()

    @discord.ui.button(emoji="🔃", style=discord.ButtonStyle.success, custom_id="rotate")
    async def rotate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cog.handle_input(self.channel_id, 'rotate')
        await interaction.response.defer()

    @discord.ui.button(emoji="🛑", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.stop_game(interaction)

class XepHinhCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.active_games = {} 

    def make_empty_board(self):
        return [[EMPTY_SQUARE for _ in range(NUM_COLS)] for _ in range(NUM_ROWS)]

    def get_random_shape(self, start_higher=False):
        template = random.choice(ALL_SHAPES)
        start_pos = copy.deepcopy(template.starting_pos)
        if start_higher:
            for s in start_pos:
                s[0] -= 1
        return [start_pos, template.colour, template.rotation_points]

    def format_board_as_str(self, board):
        return "\n".join(["".join(row) for row in board])
    
    def handle_input(self, channel_id, action):
        if channel_id in self.active_games:
            game_data = self.active_games[channel_id]
            game_data['input_queue'].append(action)
            # Wake up the loop immediately
            if 'input_event' in game_data:
                game_data['input_event'].set()

    async def start_game(self, interaction: discord.Interaction):
        if interaction.channel_id in self.active_games:
            await interaction.response.send_message("❌ Đang có game xếp hình diễn ra ở đây!", ephemeral=True)
            return

        # Initialize game state
        game_data = {
            'player_id': interaction.user.id,
            'board': self.make_empty_board(),
            'score': 0,
            'lines': 0,
            'cur_shape': self.get_random_shape(),
            'rotation_pos': 0,
            'input_queue': [],
            'start_higher': False,
            'game_over': False,
            'input_event': asyncio.Event(),
            'last_render': None
        }
        
        embed = discord.Embed(
            title="Xếp Hình (Tetris)", 
            description=self.format_board_as_str(game_data['board']), 
            color=EMBED_COLOUR
        )
        embed.set_footer(text=f"Người chơi: {interaction.user.display_name} | Điểm: 0 | Hàng: 0")
        
        view = XepHinhView(self, interaction.channel_id, interaction.user.id)
        msg = await interaction.response.send_message(embed=embed, view=view)
        # Fetch the message object from the interaction response or callback
        # interaction.response.send_message does not return the message. 
        # We need to fetch it or use original response.
        game_data['message'] = await interaction.original_response()
        
        # Initial render state
        game_data['last_render'] = embed.description + str(embed.footer.text)
        
        self.active_games[interaction.channel_id] = game_data
        
        # Start game loop
        task = asyncio.create_task(self.game_loop(interaction.channel_id))
        self.active_games[interaction.channel_id]['game_task'] = task

    async def stop_game(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        if channel_id in self.active_games:
            game_data = self.active_games[channel_id]
            game_data['game_over'] = True
            game_data['input_event'].set() # Wake up loop to finish
            
            if not interaction.response.is_done():
                 await interaction.response.defer()
        else:
            await interaction.response.send_message("❌ Không có game nào đang chạy.", ephemeral=True)

    def check_collision(self, board, shape_pos):
        for r, c in shape_pos:
            if not (0 <= c < NUM_COLS and r < NUM_ROWS): # Out of bounds (left/right/bottom)
                return True
            if r >= 0 and board[r][c] != EMPTY_SQUARE: # Occupied
                 return True
        return False

    def rotate_shape(self, game_data):
        cur_shape = game_data['cur_shape']
        shape_pos = cur_shape[0]
        shape_colour = cur_shape[1]
        rot_points = cur_shape[2]
        rotation_pos = game_data['rotation_pos']
        
        if shape_colour == YELLOW_SQUARE: return shape_pos 

        rotation_point = shape_pos[rot_points[rotation_pos]]
        new_shape_pos = []
        
        adj = ROT_ADJUSTMENTS[shape_colour][rotation_pos-1]
        
        for r, c in shape_pos:
            nr = (c - rotation_point[1]) + rotation_point[0] + adj[0]
            nc = -(r - rotation_point[0]) + rotation_point[1] + adj[1]
            new_shape_pos.append([nr, nc])

        kick_set = MAIN_WALL_KICKS[rotation_pos] if shape_colour != BLUE_SQUARE else I_WALL_KICKS[rotation_pos]
        
        final_shape = []
        for kick in kick_set:
            valid = True
            temp_shape = []
            for r, c in new_shape_pos:
                nr, nc = r + kick[0], c + kick[1]
                if not (0 <= nc < NUM_COLS and 0 <= nr < NUM_ROWS):
                    valid = False; break
                if nr >= 0 and game_data['board'][nr][nc] != EMPTY_SQUARE:
                    valid = False; break
                temp_shape.append([nr, nc])
            
            if valid:
                final_shape = temp_shape
                break
        
        if final_shape:
            final_shape.sort(key=lambda x: x[0], reverse=True)
            return final_shape
        
        return shape_pos 

    async def render_board(self, gd):
        # Construct board display
        display_board = [row[:] for row in gd['board']]
        for r, c in gd['cur_shape'][0]:
            if 0 <= r < NUM_ROWS and 0 <= c < NUM_COLS:
                display_board[r][c] = gd['cur_shape'][1]
        
        description = self.format_board_as_str(display_board)
        footer_text = f"Người chơi: <@{gd['player_id']}> | Điểm: {gd['score']} | Hàng: {gd['lines']}"
        
        # Check if changed
        current_render = description + footer_text
        if gd.get('last_render') == current_render:
            return # Skip update if identical
        
        embed = discord.Embed(
            title="Xếp Hình (Tetris)", 
            description=description, 
            color=EMBED_COLOUR
        )
        embed.set_footer(text=footer_text)
        
        try:
            await gd['message'].edit(embed=embed)
            gd['last_render'] = current_render
        except discord.NotFound:
            gd['game_over'] = True

    async def game_loop(self, channel_id):
        try:
            if channel_id not in self.active_games: return
            gd = self.active_games[channel_id]
            
            last_gravity_time = asyncio.get_running_loop().time()
            GRAVITY_DELAY = 1.0 # Seconds per drop

            while not gd['game_over']:
                # Calculate time until next gravity drop
                now = asyncio.get_running_loop().time()
                timeout = max(0.05, GRAVITY_DELAY - (now - last_gravity_time))
                
                # Wait for input OR gravity timeout
                try:
                    await asyncio.wait_for(gd['input_event'].wait(), timeout=timeout)
                    gd['input_event'].clear()
                except asyncio.TimeoutError:
                    pass # Gravity tick

                # Check game over again after wait
                if gd['game_over']: break

                # 1. Process Inputs (Movement)
                shape_pos = gd['cur_shape'][0]
                shape_col = gd['cur_shape'][1]
                board_changed = False
                
                while gd['input_queue']:
                    action = gd['input_queue'].pop(0)
                    moved = False
                    if action == 'left':
                        test_pos = [[r, c-1] for r, c in shape_pos]
                        if not self.check_collision(gd['board'], test_pos):
                            shape_pos = test_pos
                            gd['cur_shape'][0] = shape_pos
                            moved = True
                    elif action == 'right':
                        test_pos = [[r, c+1] for r, c in shape_pos]
                        if not self.check_collision(gd['board'], test_pos):
                            shape_pos = test_pos
                            gd['cur_shape'][0] = shape_pos
                            moved = True
                    elif action == 'rotate':
                        old_rot = gd['rotation_pos']
                        gd['rotation_pos'] = (gd['rotation_pos'] + 1) % 4
                        new_pos = self.rotate_shape(gd)
                        if new_pos != shape_pos:
                            shape_pos = new_pos
                            gd['cur_shape'][0] = shape_pos
                            moved = True
                        else:
                            gd['rotation_pos'] = old_rot
                    elif action == 'down':
                        test_pos = [[r+1, c] for r, c in shape_pos]
                        if not self.check_collision(gd['board'], test_pos):
                            shape_pos = test_pos
                            gd['cur_shape'][0] = shape_pos
                            moved = True
                    
                    if moved: board_changed = True

                # 2. Gravity Logic
                now = asyncio.get_running_loop().time()
                if now - last_gravity_time >= GRAVITY_DELAY:
                    last_gravity_time = now
                    
                    test_pos = [[r+1, c] for r, c in shape_pos]
                    if not self.check_collision(gd['board'], test_pos):
                        shape_pos = test_pos
                        gd['cur_shape'][0] = shape_pos
                        board_changed = True
                    else:
                        # Lock Piece
                        if any(r < 0 for r, c in shape_pos):
                            gd['game_over'] = True
                            break # Game Over

                        for r, c in shape_pos:
                            gd['board'][r][c] = shape_col
                        
                        # Clear Lines
                        lines_cleared = 0
                        new_board = []
                        for row in gd['board']:
                            if EMPTY_SQUARE not in row:
                                lines_cleared += 1
                            else:
                                new_board.append(row)
                        
                        for _ in range(lines_cleared):
                            new_board.insert(0, [EMPTY_SQUARE]*NUM_COLS)
                        
                        gd['board'] = new_board
                        gd['lines'] += lines_cleared
                        
                        if lines_cleared == 1: gd['score'] += 100
                        elif lines_cleared == 2: gd['score'] += 300
                        elif lines_cleared >= 3: gd['score'] += 500
                        
                        # New Shape
                        gd['cur_shape'] = self.get_random_shape(start_higher=False)
                        gd['rotation_pos'] = 0
                        
                        if self.check_collision(gd['board'], gd['cur_shape'][0]):
                             gd['cur_shape'] = self.get_random_shape(start_higher=True)
                             if self.check_collision(gd['board'], gd['cur_shape'][0]):
                                 gd['game_over'] = True
                                 break
                        
                        board_changed = True

                # 3. Render
                if board_changed:
                     await self.render_board(gd)

        except Exception as e:
            print(f"Error in Tetris loop: {e}")
        finally:
            if channel_id in self.active_games:
                gd = self.active_games[channel_id]
                final_score = gd['score']
                player_id = gd['player_id']
                
                # Conversion rate: 1 Point = 100 Coiz
                final_coiz = final_score * 100
                
                if final_coiz > 0:
                    await self.db.add_points(player_id, gd['message'].guild.id, final_coiz)
                
                embed = discord.Embed(
                    title="GAME OVER",
                    description=f"Kết thúc game!\nNgười chơi: <@{player_id}>\n**Điểm số: {final_score}**\n**Nhận được: {final_coiz:,} Coiz** {emojis.ANIMATED_EMOJI_COIZ}\nSố hàng: {gd['lines']}",
                    color=discord.Color.red()
                )
                try:
                     await gd['message'].edit(embed=embed, view=None)
                except:
                     pass
                
                del self.active_games[channel_id]

async def setup(bot: commands.Bot):
    db = DatabaseManager(config.DATABASE_PATH)
    await bot.add_cog(XepHinhCog(bot, db))
