import pygame, sys, random, math, os

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
DARK_GREEN = (0, 150, 0)

# Pong game constants
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 120
BALL_RADIUS = 15
COURT_COLOR = (10, 20, 40)
CENTER_LINE_COLOR = WHITE

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
    """Draw a slider with tick marks"""
    pygame.draw.rect(surface, GRAY, (x, y-5, width, 10), border_radius=5)
    
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
    """Create a checkerboard pattern surface for the grid background"""
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
    """Draw a snake game preview in the given rectangle"""
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
    """Draw a Pong preview for 2P game"""
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
    """Draw a Space Invaders preview"""
    pygame.draw.rect(surface, (20, 0, 30), rect, border_radius=20)
    pygame.draw.rect(surface, PURPLE, rect, 3, border_radius=20)
    
    # Draw player ship
    ship_x = rect.centerx - 15
    ship_y = rect.bottom - 30
    points = [
        (ship_x + 15, ship_y),
        (ship_x + 30, ship_y + 15),
        (ship_x, ship_y + 15)
    ]
    pygame.draw.polygon(surface, CYAN, points)
    
    # Draw enemies
    for i in range(3):
        enemy_x = rect.x + 30 + i * 40
        enemy_y = rect.y + 30
        pygame.draw.rect(surface, RED, (enemy_x, enemy_y, 25, 20), border_radius=3)
        pygame.draw.circle(surface, WHITE, (enemy_x + 7, enemy_y + 7), 3)
        pygame.draw.circle(surface, WHITE, (enemy_x + 18, enemy_y + 7), 3)
    
    # Draw bullets
    pygame.draw.rect(surface, YELLOW, (rect.centerx - 2, rect.centery, 4, 10))
    pygame.draw.rect(surface, RED, (rect.centerx - 20, rect.centery - 20, 4, 10))

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

# ---------- INPUT STATE ----------
last_horiz = [0, 0]
last_vert  = [0, 0]
select_last = [False, False]
button_last = [[False, False, False, False] for _ in range(2)]
back_last = [False, False]
pause_last = [False, False]

def deadzone(x, t=0.2):
    return 0 if abs(x) < t else x

# ---- HIGHSCORE ----
HS_FILE = "highscore.txt"
try:
    highscore = int(open(HS_FILE).read()) if os.path.exists(HS_FILE) else 0
except:
    highscore = 0

game_highscores = {
    "SNAKE": highscore,
    "PONG": 0,
    "SPACE INVADERS": 0
}

# ---------- CONTROLLER BUTTON MAPPING ----------
btn_map = [
    {0: (0,1), 1:(-1,0), 2:(0,-1), 3:(1,0)},
    {0: (0,1), 1:(1,0), 2:(0,-1), 3:(-1,0)}
]

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
                
                pygame.draw.rect(surface, DARK_GREEN, 
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
            pygame.draw.polygon(surface, DARK_GREEN, stem_points)
    
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
    
    pause_panel = pygame.Rect(W//2-300, H//2-200, 600, 400)
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
        'dead_select_pressed': False,
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
                
        def handle_input(self, joystick, button_dir, button_states, shoot_pressed, select_pressed, back_pressed):
            if back_pressed and not self.game_over and not self.victory:
                self.paused = not self.paused
                return
                
            if self.game_over or self.victory:
                if joystick:
                    v = deadzone(joystick.get_axis(1))
                    if v > 0.5:
                        self.dead_menu_index = 0
                    elif v < -0.5:
                        self.dead_menu_index = 1
                        
                if button_dir != (0, 0):
                    dx, dy = button_dir
                    
                    if dy == 1:
                        self.dead_menu_index = 1
                    elif dy == -1:
                        self.dead_menu_index = 0
                        
                if select_pressed:
                    if self.dead_menu_index == 0:
                        return "restart"
                    else:
                        return "menu"
                return
                
            if self.paused:
                return
                
            if joystick:
                # FIXED: Natural axis movement for Space Invaders (no inversion)
                h = deadzone(joystick.get_axis(0))
                
                if h > 0.2:
                    self.player.move_right_pressed = False
                    self.player.move_left_pressed = True
                elif h < -0.2:
                    self.player.move_left_pressed = False
                    self.player.move_right_pressed = True
                else:
                    self.player.move_left_pressed = False
                    self.player.move_right_pressed = False
            
            if button_states[1]:
                self.player.move_left()
            if button_states[3]:
                self.player.move_right()
                
            if not (button_states[1] or button_states[3]) and not (joystick and abs(deadzone(joystick.get_axis(0))) > 0.2):
                self.player.move_left_pressed = False
                self.player.move_right_pressed = False
                
            if shoot_pressed:
                bullet = self.player.shoot()
                if bullet:
                    self.bullets.append(bullet)
                    
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
            
            pause_text = title_font.render("PAUSED", True, YELLOW)
            pause_rect = pause_text.get_rect(center=(W//2, H//2))
            surface.blit(pause_text, pause_rect)
                
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
            
            restart_color = DARK_GREEN if self.dead_menu_index == 0 else (50, 50, 50)
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
            
            pygame.draw.rect(surface, DARK_GREEN, (panel_x, panel_y, panel_width, panel_height), border_radius=20)
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
            
            restart_color = DARK_GREEN if self.dead_menu_index == 0 else (50, 50, 50)
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

def restore_original_screen():
    global screen, W, H
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    W, H = screen.get_size()

# ---------- MAIN LOOP ----------
snake_game_state = None
pong_game_state = None
space_invaders_game_state = None

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    horiz = 0
    vert = 0
    btn_select_edge = False
    button_dir = (0, 0)
    back_pressed_edge = False
    pause_pressed_edge = False
    button_states = [False, False, False, False]

    if state == "menu":
        players = range(min(2, len(joysticks)))
    elif state == "pong_score_select":
        players = range(min(2, len(joysticks)))
    elif state == "space_invaders_difficulty_select":
        players = range(min(2, len(joysticks)))
    elif state == "game_pong" and pong_game_state is not None and pong_game_state['game_over']:
        players = range(min(2, len(joysticks)))
    else:
        players = [active_joystick] if active_joystick is not None else range(min(2, len(joysticks)))

    for p in players:
        if p < len(joysticks):
            j = joysticks[p]
            
            h = deadzone(j.get_axis(0))
            v = deadzone(j.get_axis(1))
            
            # FIXED: Only invert for Player 1 when NOT in Space Invaders game mode
            if p == 0 and state != "game_space_invaders":
                h = -h
                v = -v
            
            if h > 0.5 and last_horiz[p] <= 0.5: horiz = 1
            elif h < -0.5 and last_horiz[p] >= -0.5: horiz = -1
            last_horiz[p] = h
            
            if v > 0.5 and last_vert[p] <= 0.5: vert = 1
            elif v < -0.5 and last_vert[p] >= -0.5: vert = -1
            last_vert[p] = v

            for btn in range(4):
                pressed = j.get_button(btn)
                button_states[btn] = pressed
                if pressed and not button_last[p][btn]:
                    dx, dy = btn_map[p][btn]
                    button_dir = (dx, dy)
                button_last[p][btn] = pressed

            back_pressed = j.get_button(4)
            if back_pressed and not back_last[p]:
                back_pressed_edge = True
            back_last[p] = back_pressed

            pause_pressed = j.get_button(4)
            if pause_pressed and not pause_last[p]:
                pause_pressed_edge = True
            pause_last[p] = pause_pressed

            sel = j.get_button(5)
            if sel and not select_last[p]: 
                btn_select_edge = True
            select_last[p] = sel

    # ---------- STATE LOGIC ----------
    if state == "menu":
        if horiz: menu_selected = max(0, min(2, menu_selected + horiz))
        
        if button_dir != (0, 0):
            dx, dy = button_dir
            if dx != 0:
                menu_selected = max(0, min(2, menu_selected + dx))
            
        if btn_select_edge:
            if menu_selected == 0: 
                state = "choose"
                is_two_player_mode = False
            elif menu_selected == 1: 
                state = "game_select"
                active_joystick = None
                is_two_player_mode = True
            elif menu_selected == 2: 
                state = "choose"
                is_two_player_mode = False

    elif state == "choose":
        if horiz == 1 and choose_selected == 0: choose_selected = 1
        elif horiz == -1 and choose_selected == 1: choose_selected = 0
        if vert == 1: choose_selected = 1
        elif vert == -1: choose_selected = 0
        
        if button_dir != (0, 0):
            dx, dy = button_dir
            if dx == 1 or dy == 1:
                choose_selected = 1
            elif dx == -1 or dy == -1:
                choose_selected = 0
        
        if btn_select_edge:
            active_joystick = 1 if choose_selected == 0 else 0
            state = "game_select"
            if is_two_player_mode:
                active_joystick = None
        
        if back_pressed_edge:
            state = "menu"

    elif state == "game_select":
        current_games = two_player_games if is_two_player_mode else one_player_games
        
        if horiz: game_selected = max(0, min(len(current_games)-1, game_selected + horiz))
        
        if button_dir != (0, 0):
            dx, dy = button_dir
            if dx != 0:
                game_selected = max(0, min(len(current_games)-1, game_selected + dx))
            
        if btn_select_edge:
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
        
        if back_pressed_edge:
            if is_two_player_mode:
                state = "menu"
            else:
                state = "choose"

    elif state == "pong_score_select":
        if horiz: 
            pong_score_limit = max(5, min(20, pong_score_limit + horiz))
        
        if button_dir != (0, 0):
            dx, dy = button_dir
            if dx == 1:
                pong_score_limit = max(5, min(20, pong_score_limit + 1))
            elif dx == -1:
                pong_score_limit = max(5, min(20, pong_score_limit - 1))
        
        if btn_select_edge:
            state = "game_pong"
            pong_game_state = init_pong_game(pong_score_limit)
            screen = pong_game_state['game_screen']
        
        if back_pressed_edge:
            state = "game_select"

    elif state == "space_invaders_difficulty_select":
        if horiz: 
            space_invaders_difficulty = max(1, min(10, space_invaders_difficulty + horiz))
        
        if button_dir != (0, 0):
            dx, dy = button_dir
            if dx == 1:
                space_invaders_difficulty = min(10, space_invaders_difficulty + 1)
            elif dx == -1:
                space_invaders_difficulty = max(1, space_invaders_difficulty - 1)
        
        if btn_select_edge:
            state = "game_space_invaders"
            space_invaders_game_state = init_space_invaders_game(space_invaders_difficulty)
            screen = space_invaders_game_state['game_screen']
        
        if back_pressed_edge:
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

    elif state == "pong_score_select":
        screen.fill((20, 10, 40))
        
        draw_3d_text("PONG SETTINGS", title_font, (W//2, 150))
        
        instructions = [
            "SET THE WINNING SCORE LIMIT",
            "First player to reach this score wins!"
        ]
        for i, line in enumerate(instructions):
            inst_text = btn_font.render(line, True, CYAN if i == 0 else WHITE)
            screen.blit(inst_text, (W//2 - inst_text.get_width()//2, 250 + i*50))
        
        slider_x = W//2 - 300
        slider_y = H//2 + 50
        slider_width = 600
        draw_slider(screen, slider_x, slider_y, slider_width, pong_score_limit, 5, 20, 1)
        
        score_text = btn_font.render(f"FIRST TO {pong_score_limit} POINTS WINS", True, YELLOW)
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

        if active_joystick is None and len(joysticks) > 0: active_joystick = 0
        
        if active_joystick is not None and active_joystick < len(joysticks):
            j = joysticks[active_joystick]

            if pause_pressed_edge and not dead:
                paused = not paused
                pause_select_pressed = True
            
            if not paused and not dead:
                ax = deadzone(j.get_axis(0))
                ay = deadzone(j.get_axis(1))
                if active_joystick == 0: ax=-ax; ay=-ay
                new_dx,new_dy=snake.dx,snake.dy
                if abs(ax)>0.5 and abs(ax)>abs(ay): new_dx,new_dy=(1,0) if ax>0 else (-1,0)
                elif abs(ay)>0.5 and abs(ay)>abs(ax): new_dx,new_dy=(0,1) if ay>0 else (0,-1)
                
                for k in range(4):
                    if j.get_button(k):
                        dx,dy=btn_map[active_joystick][k]
                        new_dx,new_dy=dx,dy
                if (new_dx,new_dy)!=(-snake.dx,-snake.dy): snake.set_dir(new_dx,new_dy)

                timer+=1
                current_speed = base_speed / speed_multiplier
                if timer>=current_speed:
                    alive=snake.update()
                    timer=0
                    if not alive or snake.body[0] in snake.body[1:]:
                        dead=True
                        if snake.score>highscore:
                            highscore=snake.score
                            try:
                                open(HS_FILE,"w").write(str(highscore))
                            except:
                                pass
                            game_highscores["SNAKE"] = highscore
                    if snake.body[0]==apple.pos:
                        snake.grow+=1
                        snake.score+=1
                        apple.spawn(snake)
            
            elif paused and not dead:
                axis_x = deadzone(j.get_axis(0))
                if active_joystick == 0: axis_x = -axis_x
                
                if abs(axis_x) > 0.5:
                    if axis_x > 0.5 and last_horiz[active_joystick] <= 0.5:
                        speed_multiplier = min(1.5, speed_multiplier + 0.1)
                    elif axis_x < -0.5 and last_horiz[active_joystick] >= -0.5:
                        speed_multiplier = max(0.5, speed_multiplier - 0.1)
                
                for k in range(4):
                    if j.get_button(k) and not button_last[active_joystick][k]:
                        dx, dy = btn_map[active_joystick][k]
                        if dx == 1:
                            speed_multiplier = min(1.5, speed_multiplier + 0.1)
                        elif dx == -1:
                            speed_multiplier = max(0.5, speed_multiplier - 0.1)
                
                last_horiz[active_joystick] = axis_x

            if dead:
                axis_y = deadzone(j.get_axis(1))
                if active_joystick == 0: axis_y = -axis_y
                
                if axis_y > 0.5:
                    menu_index = 1
                elif axis_y < -0.5:
                    menu_index = 0
                
                for k in range(4):
                    if j.get_button(k) and not button_last[active_joystick][k]:
                        dx, dy = btn_map[active_joystick][k]
                        if dy == 1:
                            menu_index = 1
                        elif dy == -1:
                            menu_index = 0
                        elif dx == 1:
                            menu_index = 1
                        elif dx == -1:
                            menu_index = 0
                
                k5_pressed = j.get_button(5)
                
                if k5_pressed and not dead_select_pressed:
                    dead_select_pressed = True
                    if menu_index == 0:
                        snake, apple = new_game_func()
                        dead = False
                        timer = 0
                        menu_index = 0
                        dead_select_pressed = False
                        speed_multiplier = 1.0
                    else:
                        restore_original_screen()
                        state = "game_select"
                        snake_game_state.update({
                            'snake': snake,
                            'apple': apple,
                            'timer': timer,
                            'speed_multiplier': speed_multiplier,
                            'dead': dead,
                            'menu_index': menu_index,
                            'dead_select_pressed': dead_select_pressed,
                            'paused': paused
                        })
                elif not k5_pressed:
                    dead_select_pressed = False

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
        
        pygame.draw.rect(screen, DARK_GREEN, 
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

        if paused and not dead:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(screen, (40, 40, 60), pause_panel, border_radius=24)
            pygame.draw.rect(screen, (100, 100, 150), pause_panel, 4, border_radius=24)
            
            title = title_font.render("PAUSED", True, YELLOW)
            title_shadow = title_font.render("PAUSED", True, (100, 100, 0))
            screen.blit(title_shadow, (W//2 - title.get_width()//2 + 3, pause_panel.y + 33))
            screen.blit(title, (W//2 - title.get_width()//2, pause_panel.y + 30))
            
            speed_title = btn_font.render("SPEED MULTIPLIER", True, LIGHT_BLUE)
            screen.blit(speed_title, (W//2 - speed_title.get_width()//2, pause_panel.y + 120))
            
            draw_slider(screen, speed_slider_rect.x, speed_slider_rect.y + 20, 
                       speed_slider_rect.width, speed_multiplier, 0.5, 1.5, 0.1)

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
        
        for player_num in range(2):
            if player_num < len(joysticks):
                j = joysticks[player_num]
                
                axis_y = deadzone(j.get_axis(1))
                if player_num == 0:
                    axis_y = -axis_y
                    
                if abs(axis_y) > 0.3:
                    paddles[1 - player_num].move(axis_y, court_y, court_y + court_height)
                
                if j.get_button(0):
                    paddles[1 - player_num].move(1, court_y, court_y + court_height)
                if j.get_button(2):
                    paddles[1 - player_num].move(-1, court_y, court_y + court_height)
        
        if game_over:
            for player_num in range(2):
                if player_num < len(joysticks):
                    j = joysticks[player_num]
                    
                    axis_y = deadzone(j.get_axis(1))
                    if player_num == 0:
                        axis_y = -axis_y
                    
                    if axis_y > 0.5:
                        menu_index = 1
                    elif axis_y < -0.5:
                        menu_index = 0
                    
                    for btn in range(4):
                        pressed = j.get_button(btn)
                        if pressed and not button_last[player_num][btn]:
                            dx, dy = btn_map[player_num][btn]
                            if dy == 1:
                                menu_index = 1
                            elif dy == -1:
                                menu_index = 0
                            elif dx == 1:
                                menu_index = 1
                            elif dx == -1:
                                menu_index = 0
            
            if btn_select_edge and not dead_select_pressed:
                dead_select_pressed = True
                if menu_index == 0:
                    state = "pong_score_select"
                    restore_original_screen()
                else:
                    restore_original_screen()
                    state = "game_select"
            elif not btn_select_edge:
                dead_select_pressed = False
        
        if not game_over:
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
        
        pong_game_state.update({
            'paddles': paddles,
            'ball': ball,
            'game_over': game_over,
            'winner': winner,
            'countdown': countdown,
            'message': message,
            'menu_index': menu_index,
            'dead_select_pressed': dead_select_pressed
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
        
        if message and not game_over:
            msg_bg = pygame.Rect(W//2 - 300, H//2 - 50, 600, 100)
            pygame.draw.rect(screen, (0, 0, 0, 180), msg_bg, border_radius=20)
            pygame.draw.rect(screen, YELLOW, msg_bg, 3, border_radius=20)
            
            msg_text = btn_font.render(message, True, YELLOW)
            screen.blit(msg_text, (W//2 - msg_text.get_width()//2, H//2 - msg_text.get_height()//2))
        
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
            j = joysticks[active_joystick]
            
            result = game.handle_input(j, button_dir, button_states, btn_select_edge, btn_select_edge, back_pressed_edge)
            
            if result == "restart":
                restore_original_screen()
                state = "space_invaders_difficulty_select"
                space_invaders_difficulty = 5
            elif result == "menu":
                restore_original_screen()
                state = "game_select"
        
        game.update()
        game.draw(screen)

    pygame.display.flip()
    clock.tick(60)
