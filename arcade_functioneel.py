import pygame, sys, random, math, os
import socket
import threading
import pickle
import time

pygame.init()
pygame.joystick.init()

# ---- Controllers ----
joysticks = []
for i in range(pygame.joystick.get_count()):
    js = pygame.joystick.Joystick(i)
    js.init()
    joysticks.append(js)
    print(f"Joystick {i}: {js.get_name()}")

# ---- Screen ----
original_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = original_screen.get_size()
screen = original_screen
clock = pygame.time.Clock()

# ---- Colors ----
BLACK = (0,0,0)
DARK  = (120,40,0)
GREEN = (50, 180, 50)
DARK_GREEN = (30, 120, 30)
LIGHT_GREEN = (100, 220, 100)
RED   = (220, 50, 50)
WHITE = (255,255,255)
GRAY  = (60,60,60)
ORANGE = (255, 120, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (173, 216, 230)
YELLOW = (255, 255, 0)
GRID_COLOR_1 = (40, 160, 40)
GRID_COLOR_2 = (25, 110, 25)
SNAKE_HEAD_COLOR = (0, 255, 0)
PURPLE = (180, 70, 220)
CYAN = (0, 200, 200)
PINK = (255, 100, 180)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
DARK_RED = (150, 0, 0)
DARK_GREEN_ALT = (0, 150, 0)

# Pong game constants
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 120
BALL_RADIUS = 15
COURT_COLOR = (10, 20, 40)
CENTER_LINE_COLOR = WHITE

# Multiplayer Pong constants
MP_PADDLE_SPEED = 12
MP_BALL_SPEED = 8
MP_MAX_BALL_SPEED = 18
MP_FPS = 60

# ---- Background ----
try:
    bg = pygame.image.load("background.png").convert()
    bg = pygame.transform.scale(bg, (W, H))
except:
    bg = pygame.Surface((W, H))
    for y in range(H):
        color = (int(10 + (y/H)*30), int(5 + (y/H)*15), int(20 + (y/H)*40))
        pygame.draw.line(bg, color, (0, y), (W, y))

# ---- Fonts ----
title_font = pygame.font.SysFont(None, 130)
score_font = pygame.font.SysFont(None, 48)
btn_font   = pygame.font.SysFont(None, 64)
small_font = pygame.font.SysFont(None, 36)

# ---------- MENU BUTTONS ----------
size = 150
gap = 70
y = H - 240
x0 = (W - (size * 3 + gap * 2)) // 2
menu_buttons = [
    ("1P", pygame.Rect(x0, y, size, size)),
    ("2P", pygame.Rect(x0 + size + gap, y, size, size)),
    ("MP", pygame.Rect(x0 + (size + gap) * 2, y, size, size)),
]
menu_selected = 0
choose_selected = 0
game_selected = 0
state = "menu"
is_two_player_mode = False

# ---------- CONTROLLER LOCK ----------
active_joystick = None

# ---------- ARCADE ANIMATION ----------
arcade_texts = []
num_texts = 3
arcade_spacing = 400
arcade_y = 120
arcade_speed = 5
arcade_width = title_font.size("ARCADE")[0]
for i in range(num_texts):
    arcade_texts.append(-i * arcade_spacing)

# ---------- PONG SCORE SELECTION ----------
pong_score_limit = 5

# ---------- SPACE INVADERS DIFFICULTY ----------
space_invaders_difficulty = 5

# ========== INPUT CONFIGURATION DICTIONARIES ==========
MENU_INPUT_CONFIG = {
    "buttons": {
        0: (0, 1),
        1: (-1, 0),
        2: (0, -1),
        3: (1, 0),
    },
    "axis": {
        "AXIS0_POSITIVE": (-1, 0),
        "AXIS0_NEGATIVE": (1, 0),
        "AXIS1_POSITIVE": (0, -1),
        "AXIS1_NEGATIVE": (0, 1),
    },
    "back_button": 4,
    "select_button": 5,
    "axis_deadzone": 0.2
}

SNAKE_INPUT_CONFIG = {
    "buttons": {
        0: (0, 1),
        1: (-1, 0),
        2: (0, -1),
        3: (1, 0),
    },
    "axis": {
        "AXIS0_POSITIVE": (-1, 0),
        "AXIS0_NEGATIVE": (1, 0),
        "AXIS1_POSITIVE": (0, -1),
        "AXIS1_NEGATIVE": (0, 1),
    },
    "pause_button": 4,
    "select_button": 5,
    "axis_deadzone": 0.2
}

PONG_INPUT_CONFIG = {
    "player1": {
        "buttons": {
            0: 1,
            2: -1,
        },
        "axis": {
            "AXIS1": True,
        }
    },
    "player2": {
        "buttons": {
            0: 1,
            2: -1,
        },
        "axis": {
            "AXIS1": True,
        }
    },
    "axis_deadzone": 0.2
}

SPACE_INVADERS_INPUT_CONFIG = {
    "buttons": {
        0: "shoot",
        1: "left",
        2: "shoot",
        3: "right",
    },
    "axis": {
        "AXIS0_POSITIVE": "left",
        "AXIS0_NEGATIVE": "right",
        "AXIS1_POSITIVE": None,
        "AXIS1_NEGATIVE": None,
    },
    "pause_button": 4,
    "select_button": 5,
    "axis_deadzone": 0.2
}

# ========== INPUT HANDLING SYSTEM ==========
class InputHandler:
    def __init__(self, config):
        self.config = config
        self.last_horiz = [0, 0]
        self.last_vert = [0, 0]
        self.select_last = [False, False]
        self.button_last = [[False, False, False, False, False, False] for _ in range(2)]
        self.back_last = [False, False]
        self.button_held = [[False, False, False, False, False, False] for _ in range(2)]
        
    def deadzone(self, x):
        return 0 if abs(x) < self.config.get("axis_deadzone", 0.2) else x
    
    def get_menu_input(self, players):
        horiz_edge = 0
        vert_edge = 0
        select_pressed = False
        back_pressed = False
        button_dir = (0, 0)
        
        for p in players:
            if p < len(joysticks):
                j = joysticks[p]
                
                h = self.deadzone(j.get_axis(0))
                v = self.deadzone(j.get_axis(1))
                
                if h > 0.5 and self.last_horiz[p] <= 0.5:
                    horiz_edge = self.config["axis"]["AXIS0_POSITIVE"][0]
                elif h < -0.5 and self.last_horiz[p] >= -0.5:
                    horiz_edge = self.config["axis"]["AXIS0_NEGATIVE"][0]
                
                if v > 0.5 and self.last_vert[p] <= 0.5:
                    vert_edge = self.config["axis"]["AXIS1_POSITIVE"][1]
                elif v < -0.5 and self.last_vert[p] >= -0.5:
                    vert_edge = self.config["axis"]["AXIS1_NEGATIVE"][1]
                
                self.last_horiz[p] = h
                self.last_vert[p] = v
                
                for btn, direction in self.config["buttons"].items():
                    if btn < j.get_numbuttons():
                        pressed = j.get_button(btn)
                        if pressed and not self.button_last[p][btn]:
                            button_dir = direction
                        self.button_last[p][btn] = pressed
                
                back_btn = self.config["back_button"]
                if back_btn < j.get_numbuttons():
                    back = j.get_button(back_btn)
                    if back and not self.back_last[p]:
                        back_pressed = True
                    self.back_last[p] = back
                
                select_btn = self.config["select_button"]
                if select_btn < j.get_numbuttons():
                    sel = j.get_button(select_btn)
                    if sel and not self.select_last[p]:
                        select_pressed = True
                    self.select_last[p] = sel
        
        dx, dy = button_dir
        if dx == 0 and dy == 0:
            dx = horiz_edge
            dy = vert_edge
            
        return (dx, dy), select_pressed, back_pressed
    
    def get_snake_input(self, player):
        if player >= len(joysticks):
            return (0, 0), False, False, False
        
        j = joysticks[player]
        
        axis0 = self.deadzone(j.get_axis(0))
        axis1 = self.deadzone(j.get_axis(1))
        
        num_buttons = min(6, j.get_numbuttons())
        for btn in range(num_buttons):
            self.button_held[player][btn] = j.get_button(btn)
        
        dx, dy = 0, 0
        if self.button_held[player][1]:
            dx = -1
        elif self.button_held[player][3]:
            dx = 1
        elif self.button_held[player][0]:
            dy = 1
        elif self.button_held[player][2]:
            dy = -1
        elif axis0 > 0.5:
            dx = self.config["axis"]["AXIS0_POSITIVE"][0]
        elif axis0 < -0.5:
            dx = self.config["axis"]["AXIS0_NEGATIVE"][0]
        elif axis1 > 0.5:
            dy = self.config["axis"]["AXIS1_POSITIVE"][1]
        elif axis1 < -0.5:
            dy = self.config["axis"]["AXIS1_NEGATIVE"][1]
        
        pause = False
        select = False
        back = False
        
        pause_btn = self.config["pause_button"]
        if pause_btn < j.get_numbuttons():
            pause = j.get_button(pause_btn)
        
        select_btn = self.config["select_button"]
        if select_btn < j.get_numbuttons():
            select = j.get_button(select_btn)
        
        back_btn = MENU_INPUT_CONFIG["back_button"]
        if back_btn < j.get_numbuttons():
            back = j.get_button(back_btn)
        
        return (dx, dy), pause, select, back
    
    def get_pong_input(self, controller_num):
        if controller_num >= len(joysticks):
            return 0
        
        j = joysticks[controller_num]
        
        if controller_num == 0:
            config = self.config["player1"]
        else:
            config = self.config["player2"]
        
        axis1 = self.deadzone(j.get_axis(1))
        move = 0
        
        if abs(axis1) > self.config["axis_deadzone"]:
            if axis1 > 0:
                move = -1
            else:
                move = 1
        
        for btn, value in config["buttons"].items():
            if btn < j.get_numbuttons() and j.get_button(btn):
                move = value
        
        return move
    
    def get_space_invaders_input(self, player):
        if player >= len(joysticks):
            return "none", False, False, False
        
        j = joysticks[player]
        
        axis0 = self.deadzone(j.get_axis(0))
        
        action = "none"
        for btn in range(min(4, j.get_numbuttons())):
            if j.get_button(btn):
                action = self.config["buttons"].get(btn, "none")
        
        if action == "none":
            if axis0 > 0.5:
                action = self.config["axis"]["AXIS0_POSITIVE"]
            elif axis0 < -0.5:
                action = self.config["axis"]["AXIS0_NEGATIVE"]
        
        shoot = False
        pause = False
        select_btn = self.config["select_button"]
        if select_btn < j.get_numbuttons():
            shoot = j.get_button(select_btn)
        
        pause_btn = self.config["pause_button"]
        if pause_btn < j.get_numbuttons():
            pause = j.get_button(pause_btn)
        
        return action, shoot, pause, False

menu_input = InputHandler(MENU_INPUT_CONFIG)
snake_input = InputHandler(SNAKE_INPUT_CONFIG)
pong_input = InputHandler(PONG_INPUT_CONFIG)
space_invaders_input = InputHandler(SPACE_INVADERS_INPUT_CONFIG)

# ---------- DRAW FUNCTIONS ----------
def draw_text(text, font, pos, color):
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=pos))

def draw_3d_text(text, font, pos):
    x, y = pos
    for i in range(14, 0, -1):
        layer = font.render(text, True, DARK)
        screen.blit(layer, (x - layer.get_width() // 2 + i,
                            y - layer.get_height() // 2 + i))
    top = font.render(text, True, ORANGE)
    screen.blit(top, top.get_rect(center=pos))

def draw_slider(surface, x, y, width, value, min_val, max_val, steps):
    pygame.draw.rect(surface, GRAY, (x, y-5, width, 10), border_radius=5)
    
    if isinstance(min_val, int) and isinstance(max_val, int):
        min_int = int(min_val)
        max_int = int(max_val)
        
        for i in range(min_int, max_int + 1):
            tick_x = x + (i - min_int) / (max_int - min_int) * width
            pygame.draw.line(surface, WHITE, (tick_x, y-10), (tick_x, y+10), 2)
            val_text = small_font.render(f"{i}", True, WHITE)
            surface.blit(val_text, (tick_x - val_text.get_width()//2, y+15))
    
    handle_x = x + (value - min_val) / (max_val - min_val) * width
    pygame.draw.circle(surface, YELLOW, (int(handle_x), y), 15)
    pygame.draw.circle(surface, ORANGE, (int(handle_x), y), 15, 3)
    
    if max_val > 10:
        val_text = btn_font.render(f"{int(value)} POINTS", True, YELLOW)
    else:
        val_text = btn_font.render(f"{value:.1f}x", True, YELLOW)
    surface.blit(val_text, (handle_x - val_text.get_width()//2, y-50))

def create_grid_pattern(width, height, cell_size, color1, color2):
    pattern = pygame.Surface((width, height))
    pattern.fill(color1)
    
    for y in range(0, height, cell_size):
        for x in range(0, width, cell_size):
            if (x // cell_size + y // cell_size) % 2 == 0:
                points = [
                    (x + cell_size//2, y),
                    (x + cell_size, y + cell_size//2),
                    (x + cell_size//2, y + cell_size),
                    (x, y + cell_size//2)
                ]
                pygame.draw.polygon(pattern, color2, points)
    
    return pattern

def draw_snake_preview(surface, rect):
    pygame.draw.rect(surface, LIGHT_BLUE, rect, border_radius=20)
    pygame.draw.rect(surface, (0, 0, 0, 100), rect, 3, border_radius=20)
    
    preview_cell = rect.width // 15
    preview_cols = rect.width // preview_cell
    preview_rows = rect.height // preview_cell
    
    for y in range(preview_rows):
        for x in range(preview_cols):
            cell_rect = pygame.Rect(
                rect.x + x * preview_cell,
                rect.y + y * preview_cell,
                preview_cell,
                preview_cell
            )
            if (x + y) % 2 == 0:
                pygame.draw.rect(surface, GRID_COLOR_1, cell_rect)
            else:
                pygame.draw.rect(surface, GRID_COLOR_2, cell_rect)
    
    snake_length = 5
    for i in range(snake_length):
        seg_x = rect.x + (preview_cols//2 + i) * preview_cell
        seg_y = rect.y + preview_rows//2 * preview_cell
        seg_rect = pygame.Rect(seg_x, seg_y, preview_cell, preview_cell)
        
        if i == 0:
            pygame.draw.rect(surface, SNAKE_HEAD_COLOR, seg_rect, border_radius=4)
            pygame.draw.circle(surface, BLACK, (seg_x + preview_cell - 3, seg_y + 5), 2)
            pygame.draw.circle(surface, BLACK, (seg_x + preview_cell - 3, seg_y + preview_cell - 5), 2)
        else:
            color_val = max(100, 255 - i * 30)
            pygame.draw.rect(surface, (50, color_val, 50), seg_rect, border_radius=3)
    
    apple_x = rect.x + (preview_cols//2 + snake_length + 2) * preview_cell
    apple_y = rect.y + preview_rows//2 * preview_cell
    pygame.draw.circle(surface, RED, (apple_x + preview_cell//2, apple_y + preview_cell//2), preview_cell//2)

def draw_pong_preview(surface, rect):
    pygame.draw.rect(surface, (10, 20, 40), rect, border_radius=20)
    pygame.draw.rect(surface, CYAN, rect, 3, border_radius=20)
    
    pygame.draw.line(surface, WHITE, (rect.centerx, rect.y + 10), 
                    (rect.centerx, rect.bottom - 10), 2)
    
    pygame.draw.circle(surface, WHITE, (rect.centerx, rect.centery), 30, 2)
    
    paddle_width = 10
    paddle_height = 60
    left_paddle = pygame.Rect(rect.x + 30, rect.centery - paddle_height//2, 
                            paddle_width, paddle_height)
    pygame.draw.rect(surface, BLUE, left_paddle, border_radius=3)
    
    right_paddle = pygame.Rect(rect.right - 30 - paddle_width, rect.centery - paddle_height//2,
                             paddle_width, paddle_height)
    pygame.draw.rect(surface, RED, right_paddle, border_radius=3)
    
    ball_radius = 8
    pygame.draw.circle(surface, YELLOW, (rect.centerx, rect.centery), ball_radius)

def draw_space_invaders_preview(surface, rect):
    pygame.draw.rect(surface, (20, 0, 30), rect, border_radius=20)
    pygame.draw.rect(surface, PURPLE, rect, 3, border_radius=20)
    
    ship_x = rect.centerx - 15
    ship_y = rect.bottom - 30
    points = [
        (ship_x + 15, ship_y),
        (ship_x + 30, ship_y + 15),
        (ship_x, ship_y + 15)
    ]
    pygame.draw.polygon(surface, CYAN, points)
    
    for i in range(3):
        enemy_x = rect.x + 30 + i * 40
        enemy_y = rect.y + 30
        pygame.draw.rect(surface, RED, (enemy_x, enemy_y, 25, 20), border_radius=3)
        pygame.draw.circle(surface, WHITE, (enemy_x + 7, enemy_y + 7), 3)
        pygame.draw.circle(surface, WHITE, (enemy_x + 18, enemy_y + 7), 3)
    
    pygame.draw.rect(surface, YELLOW, (rect.centerx - 2, rect.centery, 4, 10))
    pygame.draw.rect(surface, RED, (rect.centerx - 20, rect.centery - 20, 4, 10))

def draw_mp_pong_preview(surface, rect):
    pygame.draw.rect(surface, (20, 20, 50), rect, border_radius=20)
    pygame.draw.rect(surface, GOLD, rect, 3, border_radius=20)
    
    font = pygame.font.Font(None, 30)
    wifi_text = font.render("🌐", True, GOLD)
    surface.blit(wifi_text, (rect.centerx - 15, rect.y + 10))
    
    pygame.draw.line(surface, GOLD, (rect.x + 20, rect.centery - 10), (rect.right - 20, rect.centery - 10), 2)
    
    left_screen = pygame.Rect(rect.x + 30, rect.centery - 20, 60, 40)
    right_screen = pygame.Rect(rect.right - 90, rect.centery - 20, 60, 40)
    pygame.draw.rect(surface, BLUE, left_screen, 2)
    pygame.draw.rect(surface, RED, right_screen, 2)
    
    pygame.draw.rect(surface, WHITE, (rect.x + 35, rect.centery - 15, 5, 30))
    pygame.draw.rect(surface, WHITE, (rect.right - 40, rect.centery - 15, 5, 30))
    
    pygame.draw.circle(surface, YELLOW, (rect.centerx, rect.centery), 5)
    
    text = small_font.render("2 PLAYERS NEEDED", True, GOLD)
    surface.blit(text, (rect.centerx - text.get_width()//2, rect.bottom - 30))

# ---------- STARS ----------
class ShootingStar:
    def __init__(self):
        self.reset()
    def reset(self):
        self.x = random.randint(-300, W)
        self.y = random.randint(-300, H // 2)
        self.speed = random.uniform(18, 26)
        self.angle = math.radians(random.randint(35, 55))
        self.length = random.randint(140, 220)
        self.alpha = 255
    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.alpha -= 6
        if self.alpha <= 0:
            self.reset()
    def draw(self, surf):
        for i in range(12):
            t = i / 12
            a = int(self.alpha * (1 - t))
            lx = self.x - math.cos(self.angle) * self.length * t
            ly = self.y - math.sin(self.angle) * self.length * t
            pygame.draw.circle(surf, (255, 220, 160, a),
                               (int(lx), int(ly)), 2)

stars = [ShootingStar() for _ in range(5)]
star_surf = pygame.Surface((W, H), pygame.SRCALPHA)

# ---------- PLAYER BUTTONS ----------
blue_btn = pygame.Rect(0, H//2, W//2, H//2)
red_btn = pygame.Rect(W//2, H//2, W//2, H//2)

# ---------- GAME SELECT (1P) ----------
game_width = 350
game_height = 250
game_gap = 50
game_y = H // 2 - 50
game_x0 = (W - (game_width * 3 + game_gap * 2)) // 2

one_player_games = [
    {
        "name": "SNAKE",
        "rect": pygame.Rect(game_x0, game_y, game_width, game_height),
        "color": GREEN,
        "description": "Classic Snake Game",
        "highscore_label": "HIGH SCORE",
        "preview_func": draw_snake_preview
    },
    {
        "name": "SPACE INVADERS",
        "rect": pygame.Rect(game_x0 + game_width + game_gap, game_y, game_width, game_height),
        "color": PURPLE,
        "description": "Defend Earth from Aliens",
        "highscore_label": "HIGH SCORE",
        "preview_func": draw_space_invaders_preview
    }
]

# ---------- GAME SELECT (2P) ----------
two_player_games = [
    {
        "name": "PONG",
        "rect": pygame.Rect(game_x0, game_y, game_width, game_height),
        "color": CYAN,
        "description": "Classic Pong Duel",
        "highscore_label": "BEST SCORE",
        "preview_func": draw_pong_preview
    }
]

# ---------- GAME SELECT (MP) ----------
mp_games = [
    {
        "name": "MP PONG",
        "rect": pygame.Rect(game_x0, game_y, game_width, game_height),
        "color": GOLD,
        "description": "Online Pong - 2 Players Needed",
        "highscore_label": "ONLINE",
        "preview_func": draw_mp_pong_preview
    }
]

# ---- HIGHSCORE ----
HS_FILE = "highscore.txt"
try:
    highscore = int(open(HS_FILE).read()) if os.path.exists(HS_FILE) else 0
except:
    highscore = 0

game_highscores = {
    "SNAKE": highscore,
    "PONG": 0,
    "SPACE INVADERS": 0,
    "MP PONG": 0
}

# ---------- SNAKE GAME FUNCTIONS ----------
def init_snake_game():
    global screen, W, H
    
    base_cell = 25
    cell = base_cell * 2
    
    cols = (W // cell) - 2
    rows = (H // cell) - 2
    
    grid_width = cols * cell
    grid_height = rows * cell
    grid_x = (W - grid_width) // 2
    grid_y = (H - grid_height) // 2
    
    game_screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
    
    grid_pattern = create_grid_pattern(grid_width, grid_height, cell, GRID_COLOR_1, GRID_COLOR_2)
    
    class Snake:
        def __init__(self):
            self.body = [(cols//2, rows//2)]
            self.dx, self.dy = 1, 0
            self.grow = 0
            self.score = 0
        def set_dir(self, x, y):
            if (x, y) != (-self.dx, -self.dy):
                self.dx, self.dy = x, y
        def update(self):
            x, y = self.body[0]
            nx, ny = x + self.dx, y + self.dy
            if nx < 0 or nx >= cols or ny < 0 or ny >= rows: return False
            self.body.insert(0, (nx, ny))
            if self.grow>0: self.grow-=1
            else: self.body.pop()
            return True
        def draw(self, surface):
            for i, (x, y) in enumerate(self.body):
                seg_x = grid_x + x*cell
                seg_y = grid_y + y*cell
                
                segment_rect = pygame.Rect(seg_x, seg_y, cell, cell)
                
                pygame.draw.rect(surface, DARK_GREEN_ALT, 
                               (seg_x+3, seg_y+3, cell, cell), border_radius=8)
                
                if i == 0:
                    pygame.draw.rect(surface, SNAKE_HEAD_COLOR, segment_rect, border_radius=8)
                    
                    eye_size = cell // 5
                    if self.dx == 1:
                        pygame.draw.circle(surface, BLACK, (seg_x + cell - eye_size, seg_y + eye_size*2), eye_size//2)
                        pygame.draw.circle(surface, BLACK, (seg_x + cell - eye_size, seg_y + cell - eye_size*2), eye_size//2)
                    elif self.dx == -1:
                        pygame.draw.circle(surface, BLACK, (seg_x + eye_size, seg_y + eye_size*2), eye_size//2)
                        pygame.draw.circle(surface, BLACK, (seg_x + eye_size, seg_y + cell - eye_size*2), eye_size//2)
                    elif self.dy == 1:
                        pygame.draw.circle(surface, BLACK, (seg_x + eye_size*2, seg_y + cell - eye_size), eye_size//2)
                        pygame.draw.circle(surface, BLACK, (seg_x + cell - eye_size*2, seg_y + cell - eye_size), eye_size//2)
                    elif self.dy == -1:
                        pygame.draw.circle(surface, BLACK, (seg_x + eye_size*2, seg_y + eye_size), eye_size//2)
                        pygame.draw.circle(surface, BLACK, (seg_x + cell - eye_size*2, seg_y + eye_size), eye_size//2)
                        
                else:
                    intensity = max(100, 255 - i * 15)
                    segment_color = (50, intensity, 50)
                    pygame.draw.rect(surface, segment_color, segment_rect, border_radius=6)
                
                highlight = pygame.Rect(seg_x, seg_y, cell, cell//3)
                pygame.draw.rect(surface, (255, 255, 255, 100), highlight, border_radius=3)
    
    class Apple:
        def __init__(self,snake): self.spawn(snake)
        def spawn(self,snake):
            while True:
                self.pos = (random.randint(0,cols-1),random.randint(0,rows-1))
                if self.pos not in snake.body: break
        def draw(self, surface):
            x,y = self.pos
            apple_x = grid_x + x*cell
            apple_y = grid_y + y*cell
            
            apple_rect = pygame.Rect(apple_x, apple_y, cell, cell)
            
            pygame.draw.rect(surface, (150, 30, 30), 
                           (apple_x+3, apple_y+3, cell, cell), border_radius=cell//2)
            
            pygame.draw.rect(surface, RED, apple_rect, border_radius=cell//2)
            
            shine_rect = pygame.Rect(apple_x + cell//4, apple_y + cell//4, 
                                    cell//2, cell//4)
            pygame.draw.rect(surface, (255, 200, 200, 150), shine_rect, border_radius=cell//8)
            
            stem_points = [
                (apple_x + cell//2, apple_y - 2),
                (apple_x + cell//2 - 3, apple_y - 8),
                (apple_x + cell//2 + 3, apple_y - 8)
            ]
            pygame.draw.polygon(surface, DARK_GREEN_ALT, stem_points)
    
    def new_game():
        s = Snake()
        a = Apple(s)
        return s,a
    
    snake, apple = new_game()
    timer = 0
    base_speed = 6
    speed_multiplier = 1.0
    dead = False
    menu_index = 0
    dead_select_pressed = False
    paused = False
    pause_select_pressed = False
    
    pause_panel = pygame.Rect(W//2-350, H//2-250, 700, 500)
    speed_slider_rect = pygame.Rect(W//2-250, H//2, 500, 40)
    
    death_panel = pygame.Rect(W//2-250, H//2-220, 500, 440)
    restart_btn = pygame.Rect(W//2-150, H//2+60, 300, 60)
    quit_btn    = pygame.Rect(W//2-150, H//2+140, 300, 60)
    
    return {
        'snake': snake,
        'apple': apple,
        'timer': timer,
        'base_speed': base_speed,
        'speed_multiplier': speed_multiplier,
        'dead': dead,
        'menu_index': menu_index,
        'dead_select_pressed': dead_select_pressed,
        'paused': paused,
        'pause_select_pressed': pause_select_pressed,
        'cols': cols,
        'rows': rows,
        'cell': cell,
        'grid_x': grid_x,
        'grid_y': grid_y,
        'grid_width': grid_width,
        'grid_height': grid_height,
        'grid_pattern': grid_pattern,
        'base_cell': base_cell,
        'death_panel': death_panel,
        'restart_btn': restart_btn,
        'quit_btn': quit_btn,
        'pause_panel': pause_panel,
        'speed_slider_rect': speed_slider_rect,
        'Snake': Snake,
        'Apple': Apple,
        'new_game': new_game,
        'game_screen': game_screen
    }

# ---------- PONG GAME FUNCTIONS ----------
def init_pong_game(win_score=5):
    global screen, W, H
    
    game_screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
    
    court_margin = 40
    court_width = W - court_margin * 2
    court_height = H - court_margin * 2
    court_x = court_margin
    court_y = court_margin
    
    class Paddle:
        def __init__(self, x, y, width, height, color, player_num):
            self.rect = pygame.Rect(x, y, width, height)
            self.color = color
            self.player_num = player_num
            self.speed = 12
            self.score = 0
            
        def move(self, dy, court_top, court_bottom):
            new_y = self.rect.y + dy * self.speed
            if new_y < court_top:
                new_y = court_top
            elif new_y + self.rect.height > court_bottom:
                new_y = court_bottom - self.rect.height
            self.rect.y = new_y
            
        def draw(self, surface):
            pygame.draw.rect(surface, (self.color[0]//2, self.color[1]//2, self.color[2]//2), 
                           (self.rect.x + 3, self.rect.y + 3, self.rect.width, self.rect.height),
                           border_radius=10)
            pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
            highlight = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height//3)
            pygame.draw.rect(surface, (255, 255, 255, 100), highlight, border_radius=5)
            
    class Ball:
        def __init__(self, court_center_x, court_center_y):
            self.base_speed = 8
            self.max_speed = 18
            self.reset(court_center_x, court_center_y)
            
        def reset(self, court_center_x, court_center_y):
            self.x = court_center_x
            self.y = court_center_y
            angle = random.uniform(-45, 45) * (math.pi / 180)
            direction = 1 if random.random() < 0.5 else -1
            self.dx = direction * math.cos(angle) * self.base_speed
            self.dy = math.sin(angle) * self.base_speed
            
        def update(self, court_top, court_bottom, court_left, court_right, paddles):
            self.x += self.dx
            self.y += self.dy
            
            if self.y - BALL_RADIUS < court_top or self.y + BALL_RADIUS > court_bottom:
                self.dy = -self.dy
                self.dy += random.uniform(-0.5, 0.5)
                
            scored = False
            scoring_player = None
            
            if self.x - BALL_RADIUS < court_left:
                paddles[1].score += 1
                scored = True
                scoring_player = 2
            elif self.x + BALL_RADIUS > court_right:
                paddles[0].score += 1
                scored = True
                scoring_player = 1
                
            if scored:
                self.reset((court_left + court_right) // 2, (court_top + court_bottom) // 2)
                return True, scoring_player
                
            ball_rect = pygame.Rect(self.x - BALL_RADIUS, self.y - BALL_RADIUS, 
                                  BALL_RADIUS * 2, BALL_RADIUS * 2)
            
            for paddle in paddles:
                if ball_rect.colliderect(paddle.rect):
                    relative_y = (self.y - paddle.rect.centery) / (paddle.rect.height / 2)
                    bounce_angle = relative_y * (math.pi / 4)
                    
                    self.dx = -self.dx * 1.1
                    self.dy = math.sin(bounce_angle) * abs(self.dx)
                    
                    speed = math.sqrt(self.dx**2 + self.dy**2)
                    if speed < self.base_speed:
                        factor = self.base_speed / speed
                        self.dx *= factor
                        self.dy *= factor
                        
                    if speed > self.max_speed:
                        factor = self.max_speed / speed
                        self.dx *= factor
                        self.dy *= factor
                        
                    if self.dx > 0:
                        self.x = paddle.rect.right + BALL_RADIUS
                    else:
                        self.x = paddle.rect.left - BALL_RADIUS
                        
                    return False, None
                    
            return False, None
            
        def draw(self, surface):
            pygame.draw.circle(surface, (YELLOW[0]//2, YELLOW[1]//2, YELLOW[2]//2),
                             (int(self.x) + 3, int(self.y) + 3), BALL_RADIUS)
            pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), BALL_RADIUS)
            pygame.draw.circle(surface, (255, 255, 255, 150), 
                             (int(self.x) - 5, int(self.y) - 5), BALL_RADIUS // 3)
    
    paddle_gap = 50
    paddle1_x = court_x + paddle_gap
    paddle2_x = court_x + court_width - paddle_gap - PADDLE_WIDTH
    paddle_y = court_y + (court_height - PADDLE_HEIGHT) // 2
    
    paddle1 = Paddle(paddle1_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT, BLUE, 1)
    paddle2 = Paddle(paddle2_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT, RED, 2)
    paddles = [paddle1, paddle2]
    
    court_center_x = court_x + court_width // 2
    court_center_y = court_y + court_height // 2
    ball = Ball(court_center_x, court_center_y)
    
    game_over = False
    winner = None
    countdown = 0
    message = ""
    
    death_panel = pygame.Rect(W//2-250, H//2-220, 500, 440)
    restart_btn = pygame.Rect(W//2-150, H//2+60, 300, 60)
    quit_btn    = pygame.Rect(W//2-150, H//2+140, 300, 60)
    menu_index = 0
    dead_select_pressed = False
    paused = False
    pause_select_pressed = False
    
    return {
        'paddles': paddles,
        'ball': ball,
        'game_over': game_over,
        'winner': winner,
        'countdown': countdown,
        'message': message,
        'court_x': court_x,
        'court_y': court_y,
        'court_width': court_width,
        'court_height': court_height,
        'court_center_x': court_center_x,
        'court_center_y': court_center_y,
        'game_screen': game_screen,
        'win_score': win_score,
        'death_panel': death_panel,
        'restart_btn': restart_btn,
        'quit_btn': quit_btn,
        'menu_index': menu_index,
        'dead_select_pressed': dead_select_pressed,
        'paused': paused,
        'pause_select_pressed': pause_select_pressed,
        'Paddle': Paddle,
        'Ball': Ball
    }

# ---------- SPACE INVADERS GAME FUNCTIONS ----------
def init_space_invaders_game(difficulty=5):
    global screen, W, H
    
    game_screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
    
    class SpaceInvadersPlayer:
        def __init__(self):
            self.width = 50
            self.height = 30
            self.x = W // 2 - self.width // 2
            self.y = H - 100
            self.speed = 8
            self.lives = 3
            self.score = 0
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
            self.shoot_cooldown = 0
            self.max_cooldown = 15
            self.move_left_pressed = False
            self.move_right_pressed = False
            
        def move_left(self):
            self.move_left_pressed = True
            
        def move_right(self):
            self.move_right_pressed = True
            
        def update(self):
            if self.move_left_pressed:
                self.x = max(0, self.x - self.speed)
            if self.move_right_pressed:
                self.x = min(W - self.width, self.x + self.speed)
                
            self.rect.x = self.x
            
            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1
                
        def shoot(self):
            if self.shoot_cooldown <= 0:
                self.shoot_cooldown = self.max_cooldown
                return SpaceInvadersBullet(self.x + self.width // 2 - 2, self.y, -1)
            return None
                
        def draw(self, surface):
            points = [
                (self.x + self.width // 2, self.y),
                (self.x + self.width, self.y + self.height),
                (self.x, self.y + self.height)
            ]
            pygame.draw.polygon(surface, CYAN, points)
            pygame.draw.polygon(surface, WHITE, points, 2)

    class SpaceInvadersEnemy:
        def __init__(self, x, y, enemy_type):
            self.x = x
            self.y = y
            self.type = enemy_type
            self.width = 35
            self.height = 30
            self.rect = pygame.Rect(x, y, self.width, self.height)
            self.alive = True
            self.shoot_timer = 0
            
            if self.type == 0:
                self.color = RED
                self.points = 30
            elif self.type == 1:
                self.color = PURPLE
                self.points = 20
            else:
                self.color = YELLOW
                self.points = 10
                
        def update_shoot_timer(self):
            if self.shoot_timer > 0:
                self.shoot_timer -= 1
                
        def can_shoot(self, chance):
            return self.alive and self.shoot_timer <= 0 and random.randint(1, 100) <= chance
                
        def reset_shoot_timer(self):
            self.shoot_timer = random.randint(30, 90)
                
        def draw(self, surface):
            if not self.alive:
                return
                
            pygame.draw.rect(surface, self.color, 
                           (self.x + 5, self.y + 5, self.width - 10, self.height - 10),
                           border_radius=3)
            
            pygame.draw.circle(surface, WHITE, (self.x + 10, self.y + 12), 4)
            pygame.draw.circle(surface, WHITE, (self.x + 25, self.y + 12), 4)
            pygame.draw.circle(surface, BLACK, (self.x + 11, self.y + 12), 2)
            pygame.draw.circle(surface, BLACK, (self.x + 26, self.y + 12), 2)

    class SpaceInvadersBullet:
        def __init__(self, x, y, direction):
            self.x = x
            self.y = y
            self.width = 4
            self.height = 10
            self.direction = direction
            self.speed = 8
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
            
        def update(self):
            self.y += self.speed * self.direction
            self.rect.y = self.y
            
        def draw(self, surface):
            if self.direction == -1:
                pygame.draw.rect(surface, YELLOW, (self.x, self.y, self.width, self.height))
            else:
                pygame.draw.rect(surface, RED, (self.x, self.y, self.width, self.height))
            
        def off_screen(self):
            return self.y < 0 or self.y > H

    class SpaceInvadersGame:
        def __init__(self, difficulty):
            self.player = SpaceInvadersPlayer()
            self.enemies = []
            self.bullets = []
            self.game_over = False
            self.victory = False
            self.paused = False
            self.difficulty = difficulty
            self.enemy_direction = 1
            self.enemy_move_counter = 0
            self.enemy_move_delay = max(15, 30 - difficulty)
            self.enemy_shoot_chance = difficulty * 3
            self.max_enemy_bullets = difficulty
            self.dead_menu_index = 0
            self.dead_select_pressed = False
            self.pause_select_pressed = False
            self.create_enemies()
            
        def create_enemies(self):
            rows = min(5, 3 + self.difficulty // 3)
            cols = min(8, 4 + self.difficulty // 2)
            
            start_x = (W - (cols * 45)) // 2
            start_y = 50
            
            for row in range(rows):
                for col in range(cols):
                    x = start_x + col * 45
                    y = start_y + row * 45
                    enemy_type = row % 3
                    self.enemies.append(SpaceInvadersEnemy(x, y, enemy_type))
                    
        def update(self):
            if self.game_over or self.victory or self.paused:
                return
                
            self.player.update()
            
            self.enemy_move_counter += 1
            if self.enemy_move_counter >= self.enemy_move_delay:
                self.enemy_move_counter = 0
                
                edge_hit = False
                for enemy in self.enemies:
                    if enemy.alive:
                        if enemy.x <= 0 or enemy.x + enemy.width >= W:
                            edge_hit = True
                            break
                
                move_down = edge_hit
                for enemy in self.enemies:
                    if enemy.alive:
                        if move_down:
                            enemy.y += 15
                            self.enemy_direction *= -1
                        else:
                            enemy.x += 5 * self.enemy_direction
                        
                        enemy.rect.x = enemy.x
                        enemy.rect.y = enemy.y
                        
                        if enemy.y + enemy.height >= self.player.y - 20:
                            self.game_over = True
            
            for enemy in self.enemies:
                enemy.update_shoot_timer()
            
            enemy_bullets = sum(1 for b in self.bullets if b.direction == 1)
            
            if enemy_bullets < self.max_enemy_bullets:
                for enemy in self.enemies:
                    if enemy.can_shoot(self.enemy_shoot_chance):
                        self.bullets.append(SpaceInvadersBullet(
                            enemy.x + enemy.width//2 - 2, 
                            enemy.y + enemy.height, 1))
                        enemy.reset_shoot_timer()
                        break
            
            for bullet in self.bullets[:]:
                bullet.update()
                
                if bullet.off_screen():
                    self.bullets.remove(bullet)
                    continue
                    
                if bullet.direction == 1:
                    if self.player.rect.colliderect(bullet.rect):
                        self.player.lives -= 1
                        self.bullets.remove(bullet)
                        if self.player.lives <= 0:
                            self.game_over = True
                            
                if bullet.direction == -1:
                    for enemy in self.enemies:
                        if enemy.alive and enemy.rect.colliderect(bullet.rect):
                            enemy.alive = False
                            self.player.score += enemy.points
                            if bullet in self.bullets:
                                self.bullets.remove(bullet)
                            break
            
            if all(not enemy.alive for enemy in self.enemies):
                self.victory = True
                if self.player.score > game_highscores["SPACE INVADERS"]:
                    game_highscores["SPACE INVADERS"] = self.player.score
                
        def handle_input(self, action, shoot_pressed, pause_pressed, back_pressed):
            if pause_pressed and not self.game_over and not self.victory:
                self.paused = not self.paused
                self.pause_select_pressed = True
                return
                
            if self.game_over or self.victory:
                return
                
            if self.paused:
                return
                
            if action == "left":
                self.player.move_left_pressed = True
                self.player.move_right_pressed = False
            elif action == "right":
                self.player.move_left_pressed = False
                self.player.move_right_pressed = True
            else:
                self.player.move_left_pressed = False
                self.player.move_right_pressed = False
                
            if shoot_pressed:
                bullet = self.player.shoot()
                if bullet:
                    self.bullets.append(bullet)
        
        def handle_dead_screen_input(self, dy, select_pressed):
            if self.game_over or self.victory:
                if dy == 1:
                    self.dead_menu_index = 1
                elif dy == -1:
                    self.dead_menu_index = 0
                
                if select_pressed and not self.dead_select_pressed:
                    self.dead_select_pressed = True
                    return True
                elif not select_pressed:
                    self.dead_select_pressed = False
            return False
        
        def handle_pause_input(self, dx, select_pressed):
            if self.paused:
                if select_pressed and not self.pause_select_pressed:
                    self.pause_select_pressed = True
                    self.paused = False
                    return True
                elif not select_pressed:
                    self.pause_select_pressed = False
            return False
                    
        def draw(self, surface):
            surface.fill(BLACK)
            
            for i in range(50):
                x = random.randint(0, W)
                y = random.randint(0, H)
                pygame.draw.circle(surface, (100, 100, 100), (x, y), 1)
            
            for enemy in self.enemies:
                if enemy.alive:
                    enemy.draw(surface)
            
            self.player.draw(surface)
            
            for bullet in self.bullets:
                bullet.draw(surface)
            
            score_text = score_font.render(f"SCORE: {self.player.score}", True, WHITE)
            surface.blit(score_text, (20, 20))
            
            lives_text = score_font.render(f"LIVES: {self.player.lives}", True, WHITE)
            surface.blit(lives_text, (20, 60))
            
            diff_text = score_font.render(f"DIFF: {self.difficulty}", True, YELLOW)
            surface.blit(diff_text, (W - 150, 20))
            
            enemies_left = sum(1 for e in self.enemies if e.alive)
            enemy_text = score_font.render(f"ENEMIES: {enemies_left}", True, GREEN)
            surface.blit(enemy_text, (W - 150, 60))
            
            if self.paused:
                self.draw_pause_screen(surface)
            
            if self.game_over:
                self.draw_dead_screen(surface)
            elif self.victory:
                self.draw_victory_screen(surface)
                
        def draw_pause_screen(self, surface):
            overlay = pygame.Surface((W, H))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))
            
            panel_width = 600
            panel_height = 350
            panel_x = W//2 - panel_width//2
            panel_y = H//2 - panel_height//2
            
            pygame.draw.rect(surface, (40, 40, 60), (panel_x, panel_y, panel_width, panel_height), border_radius=20)
            pygame.draw.rect(surface, YELLOW, (panel_x, panel_y, panel_width, panel_height), 4, border_radius=20)
            
            pause_text = title_font.render("PAUSED", True, YELLOW)
            pause_rect = pause_text.get_rect(center=(W//2, panel_y + 100))
            surface.blit(pause_text, pause_rect)
            
            resume_text = btn_font.render("PRESS SELECT TO RESUME", True, WHITE)
            resume_rect = resume_text.get_rect(center=(W//2, panel_y + 200))
            surface.blit(resume_text, resume_rect)
                
        def draw_dead_screen(self, surface):
            overlay = pygame.Surface((W, H))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))
            
            panel_width = 500
            panel_height = 400
            panel_x = W//2 - panel_width//2
            panel_y = H//2 - panel_height//2
            
            pygame.draw.rect(surface, DARK_RED, (panel_x, panel_y, panel_width, panel_height), border_radius=20)
            pygame.draw.rect(surface, RED, (panel_x, panel_y, panel_width, panel_height), 4, border_radius=20)
            
            died_text = title_font.render("YOU DIED", True, WHITE)
            died_rect = died_text.get_rect(center=(W//2, panel_y + 80))
            surface.blit(died_text, died_rect)
            
            score_display = btn_font.render(f"SCORE: {self.player.score}", True, YELLOW)
            score_rect = score_display.get_rect(center=(W//2, panel_y + 160))
            surface.blit(score_display, score_rect)
            
            diff_display = score_font.render(f"DIFFICULTY: {self.difficulty}", True, WHITE)
            diff_rect = diff_display.get_rect(center=(W//2, panel_y + 210))
            surface.blit(diff_display, diff_rect)
            
            button_width = 200
            button_height = 60
            button_x = W//2 - button_width//2
            restart_y = panel_y + 260
            quit_y = panel_y + 330
            
            restart_color = DARK_GREEN_ALT if self.dead_menu_index == 0 else (50, 50, 50)
            pygame.draw.rect(surface, restart_color, (button_x, restart_y, button_width, button_height), border_radius=15)
            pygame.draw.rect(surface, GREEN if self.dead_menu_index == 0 else GRAY, 
                            (button_x, restart_y, button_width, button_height), 3, border_radius=15)
            restart_text = btn_font.render("RESTART", True, WHITE)
            restart_text_rect = restart_text.get_rect(center=(button_x + button_width//2, restart_y + button_height//2))
            surface.blit(restart_text, restart_text_rect)
            
            quit_color = DARK_RED if self.dead_menu_index == 1 else (50, 50, 50)
            pygame.draw.rect(surface, quit_color, (button_x, quit_y, button_width, button_height), border_radius=15)
            pygame.draw.rect(surface, RED if self.dead_menu_index == 1 else GRAY, 
                            (button_x, quit_y, button_width, button_height), 3, border_radius=15)
            quit_text = btn_font.render("QUIT", True, WHITE)
            quit_text_rect = quit_text.get_rect(center=(button_x + button_width//2, quit_y + button_height//2))
            surface.blit(quit_text, quit_text_rect)
            
        def draw_victory_screen(self, surface):
            overlay = pygame.Surface((W, H))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))
            
            panel_width = 500
            panel_height = 400
            panel_x = W//2 - panel_width//2
            panel_y = H//2 - panel_height//2
            
            pygame.draw.rect(surface, DARK_GREEN_ALT, (panel_x, panel_y, panel_width, panel_height), border_radius=20)
            pygame.draw.rect(surface, GREEN, (panel_x, panel_y, panel_width, panel_height), 4, border_radius=20)
            
            victory_text = title_font.render("VICTORY!", True, WHITE)
            victory_rect = victory_text.get_rect(center=(W//2, panel_y + 80))
            surface.blit(victory_text, victory_rect)
            
            score_display = btn_font.render(f"SCORE: {self.player.score}", True, YELLOW)
            score_rect = score_display.get_rect(center=(W//2, panel_y + 160))
            surface.blit(score_display, score_rect)
            
            diff_display = score_font.render(f"DIFFICULTY: {self.difficulty}", True, WHITE)
            diff_rect = diff_display.get_rect(center=(W//2, panel_y + 210))
            surface.blit(diff_display, diff_rect)
            
            button_width = 200
            button_height = 60
            button_x = W//2 - button_width//2
            restart_y = panel_y + 260
            quit_y = panel_y + 330
            
            restart_color = DARK_GREEN_ALT if self.dead_menu_index == 0 else (50, 50, 50)
            pygame.draw.rect(surface, restart_color, (button_x, restart_y, button_width, button_height), border_radius=15)
            pygame.draw.rect(surface, GREEN if self.dead_menu_index == 0 else GRAY, 
                            (button_x, restart_y, button_width, button_height), 3, border_radius=15)
            restart_text = btn_font.render("RESTART", True, WHITE)
            restart_text_rect = restart_text.get_rect(center=(button_x + button_width//2, restart_y + button_height//2))
            surface.blit(restart_text, restart_text_rect)
            
            quit_color = DARK_RED if self.dead_menu_index == 1 else (50, 50, 50)
            pygame.draw.rect(surface, quit_color, (button_x, quit_y, button_width, button_height), border_radius=15)
            pygame.draw.rect(surface, RED if self.dead_menu_index == 1 else GRAY, 
                            (button_x, quit_y, button_width, button_height), 3, border_radius=15)
            quit_text = btn_font.render("QUIT", True, WHITE)
            quit_text_rect = quit_text.get_rect(center=(button_x + button_width//2, quit_y + button_height//2))
            surface.blit(quit_text, quit_text_rect)
    
    return {
        'game': SpaceInvadersGame(difficulty),
        'game_screen': game_screen,
        'difficulty': difficulty
    }

# ========== MULTIPLAYER PONG - MET VAST IP ==========
class MultiplayerPong:
    def __init__(self, win_score=5):
        self.screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.win_score = win_score
        self.is_host = self._check_if_host()
        
        if self.is_host:
            print("🎮 Ik ben HOST - wacht op speler 2...")
            self.game = MultiplayerPongHost(win_score)
        else:
            print("🎮 Ik ben CLIENT - verbind met host...")
            self.game = MultiplayerPongClient()
    
    def _check_if_host(self):
        """Eerste apparaat wordt host, tweede wordt client met vast IP"""
        # Dit is een SIMPELE manier: eerste start wordt host
        # Voor client moet je het IP aanpassen in MultiplayerPongClient
        return True  # ALTijd host - voor client zie hieronder
    
    def run(self):
        self.game.run()

class MultiplayerPongHost:
    def __init__(self, win_score=5):
        self.screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.win_score = win_score
        
        # Court
        self.court_margin = 40
        self.court_width = W - self.court_margin * 2
        self.court_height = H - self.court_margin * 2
        self.court_x = self.court_margin
        self.court_y = self.court_margin
        
        # Paddles
        paddle_gap = 50
        paddle1_x = self.court_x + paddle_gap
        paddle2_x = self.court_x + self.court_width - paddle_gap - PADDLE_WIDTH
        paddle_y = self.court_y + (self.court_height - PADDLE_HEIGHT) // 2
        
        self.paddle1 = pygame.Rect(paddle1_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.paddle2 = pygame.Rect(paddle2_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT)
        
        # Ball
        self.ball_x = self.court_x + self.court_width // 2
        self.ball_y = self.court_y + self.court_height // 2
        self.ball_speed_x = MP_BALL_SPEED
        self.ball_speed_y = MP_BALL_SPEED / 2
        
        self.score1 = 0
        self.score2 = 0
        self.game_over = False
        self.winner = None
        
        # Network
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', 5555))
        self.server.listen(1)
        self.server.settimeout(0.1)
        self.client = None
        self.running = True
        self.client_connected = False
        self.game_started = False
        self.start_timer = None
        
    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def reset_ball(self):
        self.ball_x = self.court_x + self.court_width // 2
        self.ball_y = self.court_y + self.court_height // 2
        angle = random.uniform(-45, 45) * (math.pi / 180)
        direction = 1 if random.random() < 0.5 else -1
        self.ball_speed_x = direction * math.cos(angle) * MP_BALL_SPEED
        self.ball_speed_y = math.sin(angle) * MP_BALL_SPEED
        
    def run(self):
        # Laad background
        try:
            bg_img = pygame.image.load("background.png").convert()
            bg_img = pygame.transform.scale(bg_img, (W, H))
        except:
            bg_img = pygame.Surface((W, H))
            bg_img.fill((10, 20, 40))
        
        print(f"🖥️ HOST gestart op IP: {self.get_ip()}")
        print(f"🔌 Wacht op client op poort 5555...")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE and self.game_over:
                        self.score1 = 0
                        self.score2 = 0
                        self.game_over = False
                        self.reset_ball()
                        self.game_started = False
                        self.start_timer = None
            
            # Probeer client te accepteren
            if not self.client:
                try:
                    self.client, addr = self.server.accept()
                    self.client.settimeout(0.1)
                    print(f"✅ Client verbonden: {addr}")
                    self.client_connected = True
                    self.start_timer = time.time() + 3
                except:
                    pass
            
            # Wacht scherm
            if not self.client_connected:
                self.screen.blit(bg_img, (0,0))
                txt = title_font.render("WACHTEN OP SPELER 2", True, YELLOW)
                self.screen.blit(txt, (W//2 - txt.get_width()//2, H//2-50))
                
                ip_text = self.font.render(f"IP: {self.get_ip()}", True, CYAN)
                self.screen.blit(ip_text, (W//2 - ip_text.get_width()//2, H//2+50))
                
                dots = "." * (int(time.time() * 2) % 4)
                wait_text = self.font.render(f"Wachten{dots}", True, GRAY)
                self.screen.blit(wait_text, (W//2 - wait_text.get_width()//2, H//2+100))
                
                pygame.display.flip()
                self.clock.tick(30)
                continue
            
            # Start countdown
            if not self.game_started and self.start_timer:
                if time.time() < self.start_timer:
                    self.screen.blit(bg_img, (0,0))
                    txt = title_font.render("SPELER 2 GEVONDEN!", True, GREEN)
                    self.screen.blit(txt, (W//2 - txt.get_width()//2, H//2-50))
                    
                    wacht = int(self.start_timer - time.time()) + 1
                    count = title_font.render(str(wacht), True, YELLOW)
                    self.screen.blit(count, (W//2 - count.get_width()//2, H//2+50))
                    
                    pygame.display.flip()
                    self.clock.tick(30)
                    continue
                else:
                    self.game_started = True
                    self.reset_ball()
                    print("🎮 Spel gestart!")
            
            # GAME LOOP
            if self.game_started and not self.game_over:
                # Host input (WASD)
                keys = pygame.key.get_pressed()
                if keys[pygame.K_w] and self.paddle1.top > self.court_y:
                    self.paddle1.y -= MP_PADDLE_SPEED
                if keys[pygame.K_s] and self.paddle1.bottom < self.court_y + self.court_height:
                    self.paddle1.y += MP_PADDLE_SPEED
                
                # Bal update
                self.ball_x += self.ball_speed_x
                self.ball_y += self.ball_speed_y
                
                # Randen
                if self.ball_y - BALL_RADIUS < self.court_y or self.ball_y + BALL_RADIUS > self.court_y + self.court_height:
                    self.ball_speed_y *= -1
                
                # Score
                if self.ball_x - BALL_RADIUS < self.court_x:
                    self.score2 += 1
                    self.reset_ball()
                    if self.score2 >= self.win_score:
                        self.game_over = True
                        self.winner = 2
                elif self.ball_x + BALL_RADIUS > self.court_x + self.court_width:
                    self.score1 += 1
                    self.reset_ball()
                    if self.score1 >= self.win_score:
                        self.game_over = True
                        self.winner = 1
                
                # Paddle botsingen
                ball_rect = pygame.Rect(self.ball_x - BALL_RADIUS, self.ball_y - BALL_RADIUS, BALL_RADIUS*2, BALL_RADIUS*2)
                
                if ball_rect.colliderect(self.paddle1) and self.ball_speed_x < 0:
                    relative_y = (self.ball_y - self.paddle1.centery) / (PADDLE_HEIGHT / 2)
                    bounce_angle = relative_y * (math.pi / 4)
                    self.ball_speed_x = -self.ball_speed_x * 1.1
                    self.ball_speed_y = math.sin(bounce_angle) * abs(self.ball_speed_x)
                    
                if ball_rect.colliderect(self.paddle2) and self.ball_speed_x > 0:
                    relative_y = (self.ball_y - self.paddle2.centery) / (PADDLE_HEIGHT / 2)
                    bounce_angle = relative_y * (math.pi / 4)
                    self.ball_speed_x = -self.ball_speed_x * 1.1
                    self.ball_speed_y = math.sin(bounce_angle) * abs(self.ball_speed_x)
            
            # Ontvang client paddle
            try:
                data = self.client.recv(1024)
                if data:
                    self.paddle2.y = pickle.loads(data)
            except:
                pass
            
            # Stuur game state
            state = {
                'ball_x': self.ball_x,
                'ball_y': self.ball_y,
                'ball_speed_x': self.ball_speed_x,
                'ball_speed_y': self.ball_speed_y,
                'paddle1_y': self.paddle1.y,
                'score1': self.score1,
                'score2': self.score2,
                'game_over': self.game_over,
                'winner': self.winner,
                'court_x': self.court_x,
                'court_y': self.court_y,
                'court_w': self.court_width,
                'court_h': self.court_height,
                'game_started': self.game_started
            }
            try:
                self.client.send(pickle.dumps(state))
            except:
                self.client = None
                self.client_connected = False
                self.game_started = False
                print("❌ Client verbinding verbroken")
            
            # Teken
            self.screen.blit(bg_img, (0,0))
            
            # Court
            pygame.draw.rect(self.screen, (100,100,150), (self.court_x-5, self.court_y-5, self.court_width+10, self.court_height+10), 5, 15)
            pygame.draw.rect(self.screen, (50,50,100), (self.court_x, self.court_y, self.court_width, self.court_height), 0, 10)
            
            # Center lijn
            for y in range(self.court_y, self.court_y + self.court_height, 35):
                pygame.draw.line(self.screen, WHITE, (self.court_x + self.court_width//2, y), 
                               (self.court_x + self.court_width//2, min(y+20, self.court_y + self.court_height)), 3)
            
            # Paddles
            pygame.draw.rect(self.screen, BLUE, self.paddle1, border_radius=10)
            pygame.draw.rect(self.screen, RED, self.paddle2, border_radius=10)
            
            # Ball
            pygame.draw.circle(self.screen, YELLOW, (int(self.ball_x), int(self.ball_y)), BALL_RADIUS)
            
            # Score
            s1 = title_font.render(str(self.score1), True, BLUE)
            s2 = title_font.render(str(self.score2), True, RED)
            self.screen.blit(s1, (W//4 - s1.get_width()//2, 50))
            self.screen.blit(s2, (3*W//4 - s2.get_width()//2, 50))
            
            # Win score
            ws = small_font.render(f"EERSTE TOT {self.win_score}", True, YELLOW)
            self.screen.blit(ws, (W//2 - ws.get_width()//2, 120))
            
            # Game over
            if self.game_over:
                overlay = pygame.Surface((W, H), pygame.SRCALPHA)
                overlay.fill((0,0,0,180))
                self.screen.blit(overlay, (0,0))
                
                win_txt = title_font.render(f"SPELER {self.winner} WINT!", True, YELLOW)
                self.screen.blit(win_txt, (W//2 - win_txt.get_width()//2, H//2-50))
                
                restart = self.font.render("DRUK SPATIE OM OPNIEUW", True, WHITE)
                self.screen.blit(restart, (W//2 - restart.get_width()//2, H//2+50))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        if self.client:
            self.client.close()
        self.server.close()

class MultiplayerPongClient:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # Game objects
        self.paddle2 = pygame.Rect(0, 0, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.ball_x = W//2
        self.ball_y = H//2
        self.score1 = 0
        self.score2 = 0
        self.game_over = False
        self.winner = None
        self.court_x = 40
        self.court_y = 40
        self.court_w = W - 80
        self.court_h = H - 80
        self.paddle1_y = H//2 - 60
        self.game_started = False
        
        # 🔴🔴🔴 HIER VUL JE HET IP VAN DE HOST IN 🔴🔴🔴
        self.host_ip = "10.156.5.44"  # ← VERVANG DIT MET HET JUISTE IP!
        
        # Verbind met host
        self.socket = None
        self._connect_to_host()
        self.running = True
    
    def _connect_to_host(self):
        """Maak direct verbinding met de host op het vaste IP"""
        print(f"🔌 Verbinden met host op {self.host_ip}:5555...")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(3)
            self.socket.connect((self.host_ip, 5555))
            print(f"✅ Verbonden met host!")
            return True
        except Exception as e:
            print(f"❌ Kan niet verbinden: {e}")
            self.socket = None
            return False
    
    def run(self):
        if not self.socket:
            print("❌ Geen verbinding met host. Controleer IP!")
            time.sleep(3)
            return
        
        try:
            bg_img = pygame.image.load("background.png").convert()
            bg_img = pygame.transform.scale(bg_img, (W, H))
        except:
            bg_img = pygame.Surface((W, H))
            bg_img.fill((10, 20, 40))
        
        print("🎮 Wacht op start van host...")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            # Client input (pijltjes)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP] and self.paddle2.top > self.court_y:
                self.paddle2.y -= MP_PADDLE_SPEED
            if keys[pygame.K_DOWN] and self.paddle2.bottom < self.court_y + self.court_h:
                self.paddle2.y += MP_PADDLE_SPEED
            
            # Stuur paddle positie
            try:
                self.socket.send(pickle.dumps(self.paddle2.y))
            except:
                print("❌ Verbinding verbroken")
                self.running = False
                break
            
            # Ontvang game state
            try:
                data = self.socket.recv(4096)
                if data:
                    state = pickle.loads(data)
                    self.ball_x = state['ball_x']
                    self.ball_y = state['ball_y']
                    self.score1 = state['score1']
                    self.score2 = state['score2']
                    self.game_over = state['game_over']
                    self.winner = state['winner']
                    self.court_x = state['court_x']
                    self.court_y = state['court_y']
                    self.court_w = state['court_w']
                    self.court_h = state['court_h']
                    self.game_started = state['game_started']
                    self.paddle1_y = state['paddle1_y']
            except:
                print("❌ Fout bij ontvangen data")
                self.running = False
                break
            
            # Teken
            self.screen.blit(bg_img, (0,0))
            
            # Court
            pygame.draw.rect(self.screen, (100,100,150), (self.court_x-5, self.court_y-5, self.court_w+10, self.court_h+10), 5, 15)
            pygame.draw.rect(self.screen, (50,50,100), (self.court_x, self.court_y, self.court_w, self.court_h), 0, 10)
            
            # Center lijn
            for y in range(self.court_y, self.court_y + self.court_h, 35):
                pygame.draw.line(self.screen, WHITE, (self.court_x + self.court_w//2, y), 
                               (self.court_x + self.court_w//2, min(y+20, self.court_y + self.court_h)), 3)
            
            # Paddles
            paddle1 = pygame.Rect(self.court_x + 50, self.paddle1_y, PADDLE_WIDTH, PADDLE_HEIGHT)
            pygame.draw.rect(self.screen, BLUE, paddle1, border_radius=10)
            pygame.draw.rect(self.screen, RED, self.paddle2, border_radius=10)
            
            # Ball
            pygame.draw.circle(self.screen, YELLOW, (int(self.ball_x), int(self.ball_y)), BALL_RADIUS)
            
            # Score
            s1 = title_font.render(str(self.score1), True, BLUE)
            s2 = title_font.render(str(self.score2), True, RED)
            self.screen.blit(s1, (W//4 - s1.get_width()//2, 50))
            self.screen.blit(s2, (3*W//4 - s2.get_width()//2, 50))
            
            # Wacht status
            if not self.game_started:
                txt = self.font.render("WACHTEN OP START...", True, YELLOW)
                self.screen.blit(txt, (W//2 - txt.get_width()//2, H//2))
            
            # Game over
            if self.game_over:
                overlay = pygame.Surface((W, H), pygame.SRCALPHA)
                overlay.fill((0,0,0,180))
                self.screen.blit(overlay, (0,0))
                
                win_txt = title_font.render(f"SPELER {self.winner} WINT!", True, YELLOW)
                self.screen.blit(win_txt, (W//2 - win_txt.get_width()//2, H//2-50))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        if self.socket:
            self.socket.close()

def restore_original_screen():
    global screen, W, H
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    W, H = screen.get_size()

# ---------- MAIN LOOP ----------
snake_game_state = None
pong_game_state = None
space_invaders_game_state = None
mp_pong_game = None

last_pause_state = [False, False]
pause_cooldown = [0, 0]

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Input handling
    if state in ["menu", "choose", "game_select", "pong_score_select", 
                 "space_invaders_difficulty_select", "mp_mode_select"]:
        players = range(min(2, len(joysticks)))
        direction, select_pressed, back_pressed = menu_input.get_menu_input(players)
        dx, dy = direction
    elif state == "game_1":
        if active_joystick is None and len(joysticks) > 0:
            active_joystick = 0
        if active_joystick is not None:
            direction, pause_pressed, select_pressed, back_pressed = snake_input.get_snake_input(active_joystick)
            dx, dy = direction
    elif state == "game_space_invaders":
        if active_joystick is None and len(joysticks) > 0:
            active_joystick = 0
        if active_joystick is not None:
            action, shoot_pressed, pause_pressed, _ = space_invaders_input.get_space_invaders_input(active_joystick)
            select_pressed = shoot_pressed
            back_pressed = pause_pressed
            
            if space_invaders_game_state and (space_invaders_game_state['game'].game_over or space_invaders_game_state['game'].victory):
                direction, menu_select, _ = menu_input.get_menu_input([active_joystick])
                _, dy_menu = direction
                selection_made = space_invaders_game_state['game'].handle_dead_screen_input(dy_menu, menu_select)
                
                if selection_made:
                    if space_invaders_game_state['game'].dead_menu_index == 0:
                        space_invaders_game_state = init_space_invaders_game(space_invaders_difficulty)
                        screen = space_invaders_game_state['game_screen']
                    else:
                        restore_original_screen()
                        state = "game_select"
            
            if space_invaders_game_state and pause_pressed and not last_pause_state[active_joystick] and pause_cooldown[active_joystick] <= 0:
                space_invaders_game_state['game'].paused = not space_invaders_game_state['game'].paused
                pause_cooldown[active_joystick] = 15
    elif state == "game_pong":
        if pong_game_state:
            for p in range(min(2, len(joysticks))):
                j = joysticks[p]
                pause_btn = MENU_INPUT_CONFIG["back_button"]
                if pause_btn < j.get_numbuttons():
                    pause_pressed = j.get_button(pause_btn)
                    
                    if pause_pressed and not last_pause_state[p] and pause_cooldown[p] <= 0 and not pong_game_state['game_over']:
                        pong_game_state['paused'] = not pong_game_state['paused']
                        pause_cooldown[p] = 15
                    last_pause_state[p] = pause_pressed
    elif state == "game_mp_pong":
        pass
    else:
        players = range(min(2, len(joysticks)))
        direction, select_pressed, back_pressed = menu_input.get_menu_input(players)
        dx, dy = direction

    # Update cooldowns
    for i in range(2):
        if pause_cooldown[i] > 0:
            pause_cooldown[i] -= 1

    # ---------- STATE LOGIC ----------
    if state == "menu":
        if dx == 1:
            menu_selected = min(2, menu_selected + 1)
        elif dx == -1:
            menu_selected = max(0, menu_selected - 1)
        
        if dy == 1:
            menu_selected = 1
        elif dy == -1:
            menu_selected = 1
            
        if select_pressed:
            if menu_selected == 0: 
                state = "choose"
                is_two_player_mode = False
            elif menu_selected == 1: 
                state = "game_select"
                active_joystick = None
                is_two_player_mode = True
            elif menu_selected == 2: 
                state = "mp_mode_select"
                is_two_player_mode = False

    elif state == "choose":
        if dx == 1:
            choose_selected = 1
        elif dx == -1:
            choose_selected = 0
        if dy == 1:
            choose_selected = 1
        elif dy == -1:
            choose_selected = 0
        
        if select_pressed:
            active_joystick = 1 if choose_selected == 0 else 0
            state = "game_select"
            if is_two_player_mode:
                active_joystick = None
        
        if back_pressed:
            state = "menu"

    elif state == "game_select":
        if is_two_player_mode:
            current_games = two_player_games
        else:
            current_games = one_player_games
        
        if dx == 1:
            game_selected = min(len(current_games)-1, game_selected + 1)
        elif dx == -1:
            game_selected = max(0, game_selected - 1)
            
        if select_pressed:
            selected_game = current_games[game_selected]["name"]
            
            if active_joystick is not None:
                if selected_game == "SNAKE":
                    state = "game_1"
                    snake_game_state = init_snake_game()
                    screen = snake_game_state['game_screen']
                elif selected_game == "SPACE INVADERS":
                    state = "space_invaders_difficulty_select"
                    space_invaders_difficulty = 5
            elif selected_game == "PONG":
                state = "pong_score_select"
                pong_score_limit = 5
        
        if back_pressed:
            if is_two_player_mode:
                state = "menu"
            else:
                state = "choose"

    elif state == "mp_mode_select":
        current_games = mp_games
        
        if select_pressed:
            selected_game = current_games[0]["name"]
            if selected_game == "MP PONG":
                state = "pong_score_select"
        
        if back_pressed:
            state = "menu"

    elif state == "pong_score_select":
        if dx == 1:
            pong_score_limit = min(20, pong_score_limit + 1)
        elif dx == -1:
            pong_score_limit = max(5, pong_score_limit - 1)
        
        if select_pressed:
            state = "game_mp_pong"
            mp_pong_game = MultiplayerPong(pong_score_limit)
        
        if back_pressed:
            state = "mp_mode_select"

    elif state == "space_invaders_difficulty_select":
        if dx == 1:
            space_invaders_difficulty = min(10, space_invaders_difficulty + 1)
        elif dx == -1:
            space_invaders_difficulty = max(1, space_invaders_difficulty - 1)
        
        if select_pressed:
            state = "game_space_invaders"
            space_invaders_game_state = init_space_invaders_game(space_invaders_difficulty)
            screen = space_invaders_game_state['game_screen']
        
        if back_pressed:
            state = "game_select"

    # ---------- DRAW ----------
    if state == "menu":
        screen.blit(bg,(0,0))
        star_surf.fill((0,0,0,0))
        for s in stars: s.update(); s.draw(star_surf)
        screen.blit(star_surf,(0,0))
        for i in range(len(arcade_texts)):
            arcade_texts[i]+=arcade_speed
            if arcade_texts[i]-arcade_width>W: arcade_texts[i]=-arcade_width
            draw_3d_text("ARCADE",title_font,(arcade_texts[i],arcade_y))
        for i,(txt,r) in enumerate(menu_buttons):
            pygame.draw.rect(screen,(0,0,0),r,border_radius=30)
            if i==menu_selected: pygame.draw.rect(screen,WHITE,r,4,border_radius=30)
            draw_text(txt,btn_font,r.center,WHITE if i==menu_selected else ORANGE)

    elif state == "choose":
        screen.fill(BLACK)
        draw_3d_text("CHOOSE PLAYER",title_font,(W//2,120))
        pygame.draw.rect(screen,BLUE,blue_btn)
        pygame.draw.rect(screen,RED,red_btn)
        pygame.draw.rect(screen,WHITE,blue_btn if choose_selected==0 else red_btn,6)

    elif state == "game_select":
        for y in range(H):
            color_val = int(10 + (y / H) * 30)
            pygame.draw.line(screen, (color_val, color_val, color_val), (0, y), (W, y))
        
        star_surf.fill((0,0,0,0))
        for s in stars: s.update(); s.draw(star_surf)
        screen.blit(star_surf,(0,0))
        
        current_games = two_player_games if is_two_player_mode else one_player_games
        mode_title = "2 PLAYER GAMES" if is_two_player_mode else "1 PLAYER GAMES"
        
        draw_3d_text("SELECT GAME", title_font, (W//2, 100))
        draw_text(mode_title, small_font, (W//2, 170), YELLOW if is_two_player_mode else CYAN)
        
        for i, game in enumerate(current_games):
            rect = game["rect"]
            is_selected = (i == game_selected)
            
            if is_selected:
                for glow in range(5, 0, -1):
                    glow_rect = pygame.Rect(
                        rect.x - glow,
                        rect.y - glow,
                        rect.width + glow*2,
                        rect.height + glow*2
                    )
                    pygame.draw.rect(screen, (game["color"][0]//2, game["color"][1]//2, game["color"][2]//2, 50), 
                                   glow_rect, border_radius=25)
                
                pygame.draw.rect(screen, (30, 30, 40), rect, border_radius=20)
                pygame.draw.rect(screen, game["color"], rect, 5, border_radius=20)
                game["preview_func"](screen, rect)
                
                name_shadow = btn_font.render(game["name"], True, (0, 0, 0))
                name_text = btn_font.render(game["name"], True, game["color"])
                screen.blit(name_shadow, (rect.centerx - name_shadow.get_width()//2 + 2, rect.y - 45))
                screen.blit(name_text, (rect.centerx - name_text.get_width()//2, rect.y - 47))
                
                desc = small_font.render(game["description"], True, WHITE)
                screen.blit(desc, (rect.centerx - desc.get_width()//2, rect.bottom + 10))
                
                highscore_val = game_highscores.get(game["name"], 0)
                highscore_text = small_font.render(f"{game['highscore_label']}: {highscore_val}", True, YELLOW)
                screen.blit(highscore_text, (rect.centerx - highscore_text.get_width()//2, rect.bottom + 35))
                
                indicator_y = rect.bottom + 70
                pygame.draw.polygon(screen, YELLOW, [
                    (rect.centerx - 10, indicator_y),
                    (rect.centerx + 10, indicator_y),
                    (rect.centerx, indicator_y + 15)
                ])
                
                if is_two_player_mode:
                    pygame.draw.circle(screen, BLUE, (rect.centerx - 40, indicator_y + 30), 10)
                    pygame.draw.circle(screen, WHITE, (rect.centerx - 40, indicator_y + 30), 10, 2)
                    p1_text = small_font.render("P1", True, BLUE)
                    screen.blit(p1_text, (rect.centerx - 45, indicator_y + 45))
                    
                    pygame.draw.circle(screen, RED, (rect.centerx + 40, indicator_y + 30), 10)
                    pygame.draw.circle(screen, WHITE, (rect.centerx + 40, indicator_y + 30), 10, 2)
                    p2_text = small_font.render("P2", True, RED)
                    screen.blit(p2_text, (rect.centerx + 35, indicator_y + 45))
                
            else:
                pygame.draw.rect(screen, (20, 20, 30), rect, border_radius=20)
                pygame.draw.rect(screen, (game["color"][0]//2, game["color"][1]//2, game["color"][2]//2), 
                               rect, 3, border_radius=20)
                game["preview_func"](screen, rect)
                name_text = btn_font.render(game["name"], True, (game["color"][0]//2, game["color"][1]//2, game["color"][2]//2))
                screen.blit(name_text, (rect.centerx - name_text.get_width()//2, rect.y - 40))

    elif state == "mp_mode_select":
        screen.fill((10, 5, 30))
        
        draw_3d_text("MULTIPLAYER", title_font, (W//2, 150))
        
        for i, game in enumerate(mp_games):
            rect = game["rect"]
            is_selected = True
            
            for glow in range(5, 0, -1):
                glow_rect = pygame.Rect(
                    rect.x - glow,
                    rect.y - glow,
                    rect.width + glow*2,
                    rect.height + glow*2
                )
                pygame.draw.rect(screen, (GOLD[0]//2, GOLD[1]//2, GOLD[2]//2, 50), 
                               glow_rect, border_radius=25)
            
            pygame.draw.rect(screen, (30, 30, 50), rect, border_radius=20)
            pygame.draw.rect(screen, GOLD, rect, 5, border_radius=20)
            game["preview_func"](screen, rect)
            
            name_shadow = btn_font.render(game["name"], True, (0, 0, 0))
            name_text = btn_font.render(game["name"], True, GOLD)
            screen.blit(name_shadow, (rect.centerx - name_shadow.get_width()//2 + 2, rect.y - 45))
            screen.blit(name_text, (rect.centerx - name_text.get_width()//2, rect.y - 47))
            
            desc = small_font.render(game["description"], True, WHITE)
            screen.blit(desc, (rect.centerx - desc.get_width()//2, rect.bottom + 10))
            
            indicator_y = rect.bottom + 70
            pygame.draw.polygon(screen, YELLOW, [
                (rect.centerx - 10, indicator_y),
                (rect.centerx + 10, indicator_y),
                (rect.centerx, indicator_y + 15)
            ])
            
            inst_text = small_font.render("START OP BEIDE APPARATEN", True, GOLD)
            screen.blit(inst_text, (W//2 - inst_text.get_width()//2, rect.bottom + 40))

    elif state == "pong_score_select":
        screen.fill((20, 10, 40))
        
        draw_3d_text("PONG SETTINGS", title_font, (W//2, 150))
        
        instructions = [
            "STEL HET WINNENDE SCORE LIMIET IN",
            "START OP BEIDE APPARATEN"
        ]
        for i, line in enumerate(instructions):
            inst_text = btn_font.render(line, True, CYAN if i == 0 else WHITE)
            screen.blit(inst_text, (W//2 - inst_text.get_width()//2, 250 + i*50))
        
        slider_x = W//2 - 300
        slider_y = H//2 + 50
        slider_width = 600
        draw_slider(screen, slider_x, slider_y, slider_width, pong_score_limit, 5, 20, 1)
        
        score_text = btn_font.render(f"EERSTE TOT {pong_score_limit} PUNTEN WINT", True, YELLOW)
        screen.blit(score_text, (W//2 - score_text.get_width()//2, H//2 + 120))

    elif state == "space_invaders_difficulty_select":
        screen.fill((10, 5, 20))
        
        draw_3d_text("SPACE INVADERS", title_font, (W//2, 150))
        
        diff_text = btn_font.render("SELECT DIFFICULTY", True, YELLOW)
        screen.blit(diff_text, (W//2 - diff_text.get_width()//2, 280))
        
        value_text = btn_font.render(str(space_invaders_difficulty), True, CYAN)
        screen.blit(value_text, (W//2 - value_text.get_width()//2, 350))
        
        slider_x = W//2 - 200
        slider_y = 400
        slider_width = 400
        
        pygame.draw.rect(screen, GRAY, (slider_x, slider_y, slider_width, 20))
        
        fill_width = (space_invaders_difficulty - 1) * (slider_width / 9)
        pygame.draw.rect(screen, GREEN, (slider_x, slider_y, fill_width, 20))
        
        handle_x = slider_x + (space_invaders_difficulty - 1) * (slider_width / 9)
        pygame.draw.circle(screen, WHITE, (int(handle_x), slider_y + 10), 15)
        pygame.draw.circle(screen, YELLOW, (int(handle_x), slider_y + 10), 12)

    # ---------- GAME_1 (SNAKE) ----------
    elif state == "game_1" and snake_game_state is not None:
        snake = snake_game_state['snake']
        apple = snake_game_state['apple']
        timer = snake_game_state['timer']
        base_speed = snake_game_state['base_speed']
        speed_multiplier = snake_game_state['speed_multiplier']
        dead = snake_game_state['dead']
        menu_index = snake_game_state['menu_index']
        dead_select_pressed = snake_game_state['dead_select_pressed']
        paused = snake_game_state['paused']
        pause_select_pressed = snake_game_state['pause_select_pressed']
        cols = snake_game_state['cols']
        rows = snake_game_state['rows']
        cell = snake_game_state['cell']
        grid_x = snake_game_state['grid_x']
        grid_y = snake_game_state['grid_y']
        grid_width = snake_game_state['grid_width']
        grid_height = snake_game_state['grid_height']
        grid_pattern = snake_game_state['grid_pattern']
        death_panel = snake_game_state['death_panel']
        restart_btn = snake_game_state['restart_btn']
        quit_btn = snake_game_state['quit_btn']
        pause_panel = snake_game_state['pause_panel']
        speed_slider_rect = snake_game_state['speed_slider_rect']
        new_game_func = snake_game_state['new_game']

        if active_joystick is None and len(joysticks) > 0: 
            active_joystick = 0
        
        if active_joystick is not None and active_joystick < len(joysticks):
            direction, pause_pressed, select_pressed, back_pressed = snake_input.get_snake_input(active_joystick)
            dx_snake, dy_snake = direction

            if pause_pressed and not last_pause_state[active_joystick] and pause_cooldown[active_joystick] <= 0 and not dead:
                paused = not paused
                pause_cooldown[active_joystick] = 20
            last_pause_state[active_joystick] = pause_pressed
            
            if paused and not dead:
                if dx_snake == 1:
                    speed_multiplier = min(2.0, speed_multiplier + 0.1)
                elif dx_snake == -1:
                    speed_multiplier = max(0.3, speed_multiplier - 0.1)
                
                if active_joystick < len(joysticks):
                    j = joysticks[active_joystick]
                    axis0 = snake_input.deadzone(j.get_axis(0))
                    if axis0 > 0.5:
                        speed_multiplier = min(2.0, speed_multiplier + 0.1)
                    elif axis0 < -0.5:
                        speed_multiplier = max(0.3, speed_multiplier - 0.1)
                
                if select_pressed and not pause_select_pressed:
                    paused = False
                pause_select_pressed = select_pressed
                
                if back_pressed and not pause_select_pressed:
                    paused = False
            
            if not paused and not dead:
                if dx_snake != 0 or dy_snake != 0:
                    snake.set_dir(dx_snake, dy_snake)

                timer += 1
                current_speed = base_speed / speed_multiplier
                if timer >= current_speed:
                    alive = snake.update()
                    timer = 0
                    if not alive or snake.body[0] in snake.body[1:]:
                        dead = True
                        if snake.score > highscore:
                            highscore = snake.score
                            try:
                                open(HS_FILE,"w").write(str(highscore))
                            except:
                                pass
                            game_highscores["SNAKE"] = highscore
                    if snake.body[0] == apple.pos:
                        snake.grow += 1
                        snake.score += 1
                        apple.spawn(snake)

            if dead:
                if dy_snake == 1:
                    menu_index = 1
                elif dy_snake == -1:
                    menu_index = 0
                
                if select_pressed and not dead_select_pressed:
                    dead_select_pressed = True
                    if menu_index == 0:
                        snake, apple = new_game_func()
                        dead = False
                        timer = 0
                        menu_index = 0
                        dead_select_pressed = False
                        speed_multiplier = 1.0
                        paused = False
                    else:
                        restore_original_screen()
                        state = "game_select"
                        continue
                elif not select_pressed:
                    dead_select_pressed = False
                
                if back_pressed and not dead_select_pressed:
                    restore_original_screen()
                    state = "game_select"
                    continue

        snake_game_state.update({
            'snake': snake,
            'apple': apple,
            'timer': timer,
            'speed_multiplier': speed_multiplier,
            'dead': dead,
            'menu_index': menu_index,
            'dead_select_pressed': dead_select_pressed,
            'paused': paused,
            'pause_select_pressed': pause_select_pressed
        })

        screen.fill(LIGHT_BLUE)
        
        pygame.draw.rect(screen, DARK_GREEN_ALT, 
                        (grid_x-5, grid_y-5, grid_width+10, grid_height+10), 
                        border_radius=15)
        
        screen.blit(grid_pattern, (grid_x, grid_y))
        
        for i in range(cols+1):
            x = grid_x + i*cell
            pygame.draw.line(screen, (20, 80, 20, 100), 
                            (x, grid_y), (x, grid_y + rows*cell), 2)
        for i in range(rows+1):
            y = grid_y + i*cell
            pygame.draw.line(screen, (20, 80, 20, 100), 
                            (grid_x, y), (grid_x + cols*cell, y), 2)
        
        apple.draw(screen)
        snake.draw(screen)
        
        score_bg = pygame.Rect(15, 15, 250, 50)
        pygame.draw.rect(screen, (0, 0, 0, 150), score_bg, border_radius=10)
        pygame.draw.rect(screen, WHITE, score_bg, 2, border_radius=10)
        score_text = score_font.render(f"SCORE: {snake.score}", True, YELLOW)
        screen.blit(score_text, (30, 30))
        
        speed_bg = pygame.Rect(W - 265, 15, 250, 50)
        pygame.draw.rect(screen, (0, 0, 0, 150), speed_bg, border_radius=10)
        pygame.draw.rect(screen, WHITE, speed_bg, 2, border_radius=10)
        speed_text = score_font.render(f"SPEED: {speed_multiplier:.1f}x", True, YELLOW)
        screen.blit(speed_text, (W - speed_text.get_width() - 30, 30))
        
        if not paused and not dead:
            pause_hint = small_font.render("PRESS PAUSE (BUTTON 4) TO PAUSE", True, WHITE)
            screen.blit(pause_hint, (W//2 - pause_hint.get_width()//2, H - 50))

        if paused and not dead:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(screen, (40, 40, 80), pause_panel, border_radius=24)
            pygame.draw.rect(screen, YELLOW, pause_panel, 6, border_radius=24)
            
            title = title_font.render("PAUSED", True, YELLOW)
            title_shadow = title_font.render("PAUSED", True, (100, 100, 0))
            screen.blit(title_shadow, (W//2 - title.get_width()//2 + 4, pause_panel.y + 44))
            screen.blit(title, (W//2 - title.get_width()//2, pause_panel.y + 40))
            
            speed_title = btn_font.render("SPEED MULTIPLIER", True, LIGHT_BLUE)
            screen.blit(speed_title, (W//2 - speed_title.get_width()//2, pause_panel.y + 140))
            
            speed_value = title_font.render(f"{speed_multiplier:.1f}x", True, YELLOW)
            screen.blit(speed_value, (W//2 - speed_value.get_width()//2, pause_panel.y + 200))
            
            draw_slider(screen, speed_slider_rect.x, speed_slider_rect.y + 20, 
                       speed_slider_rect.width, speed_multiplier, 0.3, 2.0, 0.1)
            
            control1 = score_font.render("LEFT/RIGHT: Adjust Speed", True, WHITE)
            screen.blit(control1, (W//2 - control1.get_width()//2, pause_panel.y + 300))
            
            control2 = btn_font.render("PRESS SELECT TO RESUME", True, GREEN)
            screen.blit(control2, (W//2 - control2.get_width()//2, pause_panel.y + 380))

        if dead:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(screen, (60, 20, 20), death_panel, border_radius=24)
            pygame.draw.rect(screen, (150, 50, 50), death_panel, 4, border_radius=24)
            
            title = title_font.render("YOU DIED", True, (255, 100, 100))
            title_shadow = title_font.render("YOU DIED", True, (100, 0, 0))
            screen.blit(title_shadow, (W//2 - title.get_width()//2 + 3, death_panel.y + 23))
            screen.blit(title, (W//2 - title.get_width()//2, death_panel.y + 20))
            
            s = score_font.render(f"SCORE: {snake.score}", True, YELLOW)
            h = score_font.render(f"HIGHSCORE: {highscore}", True, YELLOW)
            screen.blit(s, (W//2 - s.get_width()//2, death_panel.y + 130))
            screen.blit(h, (W//2 - h.get_width()//2, death_panel.y + 180))
            
            restart_color = (40, 80, 40) if menu_index == 0 else (30, 60, 30)
            quit_color = (80, 40, 40) if menu_index == 1 else (60, 30, 30)
            
            pygame.draw.rect(screen, restart_color, restart_btn, border_radius=16)
            pygame.draw.rect(screen, quit_color, quit_btn, border_radius=16)
            
            sel = restart_btn if menu_index == 0 else quit_btn
            pygame.draw.rect(screen, WHITE, sel, 3, border_radius=16)
            
            r = btn_font.render("RESTART", True, WHITE)
            q = btn_font.render("QUIT", True, WHITE)
            screen.blit(r, r.get_rect(center=restart_btn.center))
            screen.blit(q, q.get_rect(center=quit_btn.center))

    # ---------- GAME_PONG (2-Player Pong) ----------
    elif state == "game_pong" and pong_game_state is not None:
        paddles = pong_game_state['paddles']
        ball = pong_game_state['ball']
        game_over = pong_game_state['game_over']
        winner = pong_game_state['winner']
        countdown = pong_game_state['countdown']
        message = pong_game_state['message']
        court_x = pong_game_state['court_x']
        court_y = pong_game_state['court_y']
        court_width = pong_game_state['court_width']
        court_height = pong_game_state['court_height']
        court_center_x = pong_game_state['court_center_x']
        court_center_y = pong_game_state['court_center_y']
        win_score = pong_game_state['win_score']
        death_panel = pong_game_state['death_panel']
        restart_btn = pong_game_state['restart_btn']
        quit_btn = pong_game_state['quit_btn']
        menu_index = pong_game_state['menu_index']
        dead_select_pressed = pong_game_state['dead_select_pressed']
        paused = pong_game_state['paused']
        pause_select_pressed = pong_game_state['pause_select_pressed']
        
        if paused and not game_over:
            select_pressed = False
            for p in range(min(2, len(joysticks))):
                j = joysticks[p]
                select_btn = MENU_INPUT_CONFIG["select_button"]
                if select_btn < j.get_numbuttons() and j.get_button(select_btn):
                    select_pressed = True
                    break
            
            if select_pressed and not pause_select_pressed:
                paused = False
            pause_select_pressed = select_pressed
        
        if not game_over and not paused:
            if len(joysticks) > 0:
                move_p2 = pong_input.get_pong_input(0)
                if move_p2 != 0:
                    paddles[1].move(move_p2, court_y, court_y + court_height)
            
            if len(joysticks) > 1:
                move_p1 = pong_input.get_pong_input(1)
                if move_p1 != 0:
                    paddles[0].move(move_p1, court_y, court_y + court_height)
            
            scored, scoring_player = ball.update(
                court_y, 
                court_y + court_height,
                court_x,
                court_x + court_width,
                paddles
            )
            
            if scored:
                message = f"PLAYER {scoring_player} SCORES!"
                countdown = 60
                
                for paddle in paddles:
                    if paddle.score >= win_score:
                        game_over = True
                        winner = paddle.player_num
                        message = f"PLAYER {winner} WINS!"
                        game_highscores["PONG"] = max(game_highscores["PONG"], max(paddles[0].score, paddles[1].score))
        
        if countdown > 0:
            countdown -= 1
            if countdown == 0:
                message = ""
        
        if game_over:
            players = range(min(2, len(joysticks)))
            direction, select_pressed, back_pressed = menu_input.get_menu_input(players)
            dx, dy = direction
            
            if dy == 1:
                menu_index = 1
            elif dy == -1:
                menu_index = 0
            
            if select_pressed and not dead_select_pressed:
                dead_select_pressed = True
                if menu_index == 0:
                    pong_game_state = init_pong_game(win_score)
                    screen = pong_game_state['game_screen']
                    continue
                else:
                    restore_original_screen()
                    state = "game_select"
                    continue
            elif not select_pressed:
                dead_select_pressed = False
        
        pong_game_state.update({
            'paddles': paddles,
            'ball': ball,
            'game_over': game_over,
            'winner': winner,
            'countdown': countdown,
            'message': message,
            'menu_index': menu_index,
            'dead_select_pressed': dead_select_pressed,
            'paused': paused,
            'pause_select_pressed': pause_select_pressed
        })

        screen.fill(COURT_COLOR)
        
        pygame.draw.rect(screen, (100, 100, 150), 
                        (court_x - 5, court_y - 5, court_width + 10, court_height + 10), 
                        5, border_radius=15)
        pygame.draw.rect(screen, (50, 50, 100), 
                        (court_x, court_y, court_width, court_height), 
                        border_radius=10)
        
        dash_length = 20
        gap_length = 15
        for y in range(court_y, court_y + court_height, dash_length + gap_length):
            pygame.draw.line(screen, CENTER_LINE_COLOR, 
                            (court_center_x, y), 
                            (court_center_x, min(y + dash_length, court_y + court_height)), 
                            3)
        
        pygame.draw.circle(screen, CENTER_LINE_COLOR, 
                          (court_center_x, court_center_y), 60, 3)
        
        for paddle in paddles:
            paddle.draw(screen)
        
        ball.draw(screen)
        
        score_y = 30
        p1_score_bg = pygame.Rect(W//4 - 60, score_y - 25, 120, 80)
        pygame.draw.rect(screen, (0, 0, 50, 200), p1_score_bg, border_radius=15)
        pygame.draw.rect(screen, BLUE, p1_score_bg, 3, border_radius=15)
        p1_score_text = title_font.render(str(paddles[0].score), True, BLUE)
        screen.blit(p1_score_text, (W//4 - p1_score_text.get_width()//2, score_y - 25))
        p1_label = score_font.render("PLAYER 1", True, LIGHT_BLUE)
        screen.blit(p1_label, (W//4 - p1_label.get_width()//2, score_y + 50))
        
        colon = title_font.render(":", True, YELLOW)
        screen.blit(colon, (W//2 - colon.get_width()//2, score_y))
        
        p2_score_bg = pygame.Rect(3*W//4 - 60, score_y - 25, 120, 80)
        pygame.draw.rect(screen, (50, 0, 0, 200), p2_score_bg, border_radius=15)
        pygame.draw.rect(screen, RED, p2_score_bg, 3, border_radius=15)
        p2_score_text = title_font.render(str(paddles[1].score), True, RED)
        screen.blit(p2_score_text, (3*W//4 - p2_score_text.get_width()//2, score_y - 25))
        p2_label = score_font.render("PLAYER 2", True, (255, 150, 150))
        screen.blit(p2_label, (3*W//4 - p2_label.get_width()//2, score_y + 50))
        
        win_score_text = small_font.render(f"FIRST TO {win_score} WINS", True, YELLOW)
        screen.blit(win_score_text, (W//2 - win_score_text.get_width()//2, score_y + 90))
        
        if not paused and not game_over:
            pause_hint = small_font.render("PRESS PAUSE (BUTTON 4) TO PAUSE", True, WHITE)
            screen.blit(pause_hint, (W//2 - pause_hint.get_width()//2, H - 50))
        
        if message and not game_over and not paused:
            msg_bg = pygame.Rect(W//2 - 300, H//2 - 50, 600, 100)
            pygame.draw.rect(screen, (0, 0, 0, 180), msg_bg, border_radius=20)
            pygame.draw.rect(screen, YELLOW, msg_bg, 3, border_radius=20)
            
            msg_text = btn_font.render(message, True, YELLOW)
            screen.blit(msg_text, (W//2 - msg_text.get_width()//2, H//2 - msg_text.get_height()//2))
        
        if paused and not game_over:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            pause_panel_width = 600
            pause_panel_height = 350
            pause_panel_x = W//2 - pause_panel_width//2
            pause_panel_y = H//2 - pause_panel_height//2
            
            pygame.draw.rect(screen, (40, 40, 80), (pause_panel_x, pause_panel_y, pause_panel_width, pause_panel_height), border_radius=20)
            pygame.draw.rect(screen, YELLOW, (pause_panel_x, pause_panel_y, pause_panel_width, pause_panel_height), 6, border_radius=20)
            
            pause_text = title_font.render("PAUSED", True, YELLOW)
            pause_rect = pause_text.get_rect(center=(W//2, pause_panel_y + 120))
            screen.blit(pause_text, pause_rect)
            
            resume_text = btn_font.render("PRESS SELECT TO RESUME", True, GREEN)
            resume_rect = resume_text.get_rect(center=(W//2, pause_panel_y + 240))
            screen.blit(resume_text, resume_rect)
        
        if game_over:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(screen, (60, 20, 20), death_panel, border_radius=24)
            pygame.draw.rect(screen, (150, 50, 50), death_panel, 4, border_radius=24)
            
            title = title_font.render("GAME OVER", True, (255, 100, 100))
            title_shadow = title_font.render("GAME OVER", True, (100, 0, 0))
            screen.blit(title_shadow, (W//2 - title.get_width()//2 + 3, death_panel.y + 23))
            screen.blit(title, (W//2 - title.get_width()//2, death_panel.y + 20))
            
            final_score = f"PLAYER {winner} WINS!  {paddles[0].score} - {paddles[1].score}"
            s = score_font.render(final_score, True, YELLOW)
            screen.blit(s, (W//2 - s.get_width()//2, death_panel.y + 130))
            
            highscore_val = game_highscores.get("PONG", 0)
            h = score_font.render(f"BEST SCORE: {highscore_val}", True, YELLOW)
            screen.blit(h, (W//2 - h.get_width()//2, death_panel.y + 180))
            
            restart_color = (40, 80, 40) if menu_index == 0 else (30, 60, 30)
            quit_color = (80, 40, 40) if menu_index == 1 else (60, 30, 30)
            
            pygame.draw.rect(screen, restart_color, restart_btn, border_radius=16)
            pygame.draw.rect(screen, quit_color, quit_btn, border_radius=16)
            
            sel = restart_btn if menu_index == 0 else quit_btn
            pygame.draw.rect(screen, WHITE, sel, 3, border_radius=16)
            
            r = btn_font.render("RESTART", True, WHITE)
            q = btn_font.render("QUIT", True, WHITE)
            screen.blit(r, r.get_rect(center=restart_btn.center))
            screen.blit(q, q.get_rect(center=quit_btn.center))

    # ---------- GAME_SPACE_INVADERS ----------
    elif state == "game_space_invaders" and space_invaders_game_state is not None:
        game = space_invaders_game_state['game']
        
        if active_joystick is None and len(joysticks) > 0:
            active_joystick = 0
        
        if active_joystick is not None and active_joystick < len(joysticks):
            action, shoot_pressed, pause_pressed, _ = space_invaders_input.get_space_invaders_input(active_joystick)
            
            if pause_pressed and not last_pause_state[active_joystick] and pause_cooldown[active_joystick] <= 0 and not game.game_over and not game.victory:
                game.paused = not game.paused
                pause_cooldown[active_joystick] = 15
            last_pause_state[active_joystick] = pause_pressed
            
            if game.paused:
                select_btn = MENU_INPUT_CONFIG["select_button"]
                if select_btn < joysticks[active_joystick].get_numbuttons():
                    select_pressed = joysticks[active_joystick].get_button(select_btn)
                    if select_pressed and not game.pause_select_pressed:
                        game.paused = False
                    game.pause_select_pressed = select_pressed
            
            if not game.game_over and not game.victory and not game.paused:
                game.handle_input(action, shoot_pressed, False, False)
            
            if game.game_over or game.victory:
                direction, menu_select, _ = menu_input.get_menu_input([active_joystick])
                _, dy_menu = direction
                selection_made = game.handle_dead_screen_input(dy_menu, menu_select)
                
                if selection_made:
                    if game.dead_menu_index == 0:
                        space_invaders_game_state = init_space_invaders_game(space_invaders_difficulty)
                        screen = space_invaders_game_state['game_screen']
                        continue
                    else:
                        restore_original_screen()
                        state = "game_select"
                        continue
        
        game.update()
        game.draw(screen)

    # ---------- GAME_MP_PONG ----------
    elif state == "game_mp_pong" and mp_pong_game is not None:
        mp_pong_game.run()
        restore_original_screen()
        state = "menu"
        mp_pong_game = None

    pygame.display.flip()
    clock.tick(60)
