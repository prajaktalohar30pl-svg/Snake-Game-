"""
main.py - Snake Game (Pygame). Draws the screens and handles input.
Game rules live in game.py.

Run on your computer:   python main.py
Run in a browser:       pygbag main.py   (see README.md)
"""
import asyncio
import os
import sys

import pygame

from game import SnakeGame, COLS, ROWS, UP, DOWN, LEFT, RIGHT

# ---- Window / layout -------------------------------------------------------
W, H = 480, 830
CELL = 20
BOARD_X, BOARD_Y = 40, 120
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL

# ---- Colours ---------------------------------------------------------------
BG = (15, 23, 42)
PANEL = (30, 41, 59)
BOARD_A, BOARD_B = (17, 94, 89), (15, 118, 110)
SNAKE_BODY, SNAKE_HEAD = (74, 222, 128), (187, 247, 208)
FOOD, OBSTACLE = (239, 68, 68), (100, 116, 139)
TEXT, MUTED, ACCENT = (241, 245, 249), (148, 163, 184), (250, 204, 21)
BTN, BTN_HOVER = (34, 197, 94), (74, 222, 128)

HS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")
WEB = sys.platform == "emscripten"

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def text(surf, msg, size, color, center):
    img = font(size).render(msg, True, color)
    surf.blit(img, img.get_rect(center=center))


# ---- High score (file on PC, localStorage in browser) ---------------------
def load_high():
    try:
        if WEB:
            import platform
            v = platform.window.localStorage.getItem("snake_high")
            return int(v) if v else 0
        with open(HS_FILE) as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def save_high(value):
    try:
        if WEB:
            import platform
            platform.window.localStorage.setItem("snake_high", str(value))
        else:
            with open(HS_FILE, "w") as f:
                f.write(str(value))
    except Exception:
        pass


# ---- Simple button ---------------------------------------------------------
class Button:
    def __init__(self, label, center, size=(260, 64)):
        self.label = label
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center

    def draw(self, surf):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surf, BTN_HOVER if hover else BTN, self.rect, border_radius=16)
        text(surf, self.label, 36, (5, 46, 22), self.rect.center)

    def hit(self, pos):
        return self.rect.collidepoint(pos)


# ---- Direction pad: UP top, LEFT / centre / RIGHT middle, DOWN bottom -----
PAD = 90
GAP = 8
PAD_CX, PAD_CY = W // 2, 676


def make_pad():
    step = PAD + GAP
    spots = {"up": (PAD_CX, PAD_CY - step, UP), "left": (PAD_CX - step, PAD_CY, LEFT),
             "right": (PAD_CX + step, PAD_CY, RIGHT), "down": (PAD_CX, PAD_CY + step, DOWN)}
    pad = {}
    for name, (cx, cy, d) in spots.items():
        r = pygame.Rect(0, 0, PAD, PAD)
        r.center = (cx, cy)
        pad[name] = (r, d)
    return pad


def draw_pad(surf, pad, pressed):
    for name, (r, _) in pad.items():
        color = (71, 85, 105) if name == pressed else PANEL
        pygame.draw.rect(surf, color, r, border_radius=18)
        pygame.draw.rect(surf, (71, 85, 105), r, width=2, border_radius=18)
        cx, cy = r.center
        a = 18
        pts = {"up": [(cx, cy - a), (cx - a, cy + a // 2), (cx + a, cy + a // 2)],
               "down": [(cx, cy + a), (cx - a, cy - a // 2), (cx + a, cy - a // 2)],
               "left": [(cx - a, cy), (cx + a // 2, cy - a), (cx + a // 2, cy + a)],
               "right": [(cx + a, cy), (cx - a // 2, cy - a), (cx - a // 2, cy + a)]}[name]
        pygame.draw.polygon(surf, TEXT, pts)
    pygame.draw.circle(surf, PANEL, (PAD_CX, PAD_CY), 14)   # empty centre


# ---- Drawing the game ------------------------------------------------------
def cell_rect(c):
    return pygame.Rect(BOARD_X + c[0] * CELL, BOARD_Y + c[1] * CELL, CELL, CELL)


def draw_hud(surf, game, high):
    boxes = [("SCORE", str(game.score)), ("LEVEL", str(game.level)),
             ("HIGH SCORE", str(high)), ("SPEED", f"{game.speed_percent}%")]
    w, gap, x = 107, 8, 14
    for label, value in boxes:
        r = pygame.Rect(x, 24, w, 76)
        pygame.draw.rect(surf, PANEL, r, border_radius=14)
        text(surf, label, 20, MUTED, (r.centerx, r.y + 20))
        text(surf, value, 38, ACCENT if label == "HIGH SCORE" else TEXT, (r.centerx, r.y + 50))
        x += w + gap


def draw_board(surf, game):
    pygame.draw.rect(surf, PANEL, (BOARD_X - 6, BOARD_Y - 6, BOARD_W + 12, BOARD_H + 12),
                     border_radius=12)
    for x in range(COLS):
        for y in range(ROWS):
            pygame.draw.rect(surf, BOARD_A if (x + y) % 2 == 0 else BOARD_B, cell_rect((x, y)))
    for o in game.obstacles:
        pygame.draw.rect(surf, OBSTACLE, cell_rect(o).inflate(-2, -2), border_radius=4)
    if game.food:
        fr = cell_rect(game.food)
        pygame.draw.circle(surf, FOOD, fr.center, CELL // 2 - 2)
        pygame.draw.circle(surf, (254, 202, 202), (fr.centerx - 3, fr.centery - 3), 2)
    for i, seg in enumerate(game.snake):
        r = cell_rect(seg).inflate(-2, -2)
        pygame.draw.rect(surf, SNAKE_HEAD if i == 0 else SNAKE_BODY, r, border_radius=6)
    hr = cell_rect(game.snake[0])          # eyes
    dx, dy = game.direction
    for s in (-1, 1):
        ex = hr.centerx + dx * 4 + (-dy) * 4 * s
        ey = hr.centery + dy * 4 + dx * 4 * s
        pygame.draw.circle(surf, (15, 23, 42), (ex, ey), 2)


def draw_start(surf, btn, high):
    surf.fill(BG)
    for i in range(7):                       # decorative snake
        pygame.draw.circle(surf, SNAKE_BODY if i else SNAKE_HEAD, (110 + i * 42, 190), 20)
    text(surf, "SNAKE GAME", 80, TEXT, (W // 2, 290))
    text(surf, "Eat the food, grow your snake", 30, MUTED, (W // 2, 360))
    text(surf, "and beat your high score!", 30, MUTED, (W // 2, 392))
    text(surf, f"HIGH SCORE: {high}", 40, ACCENT, (W // 2, 470))
    btn.draw(surf)
    text(surf, "Arrow keys / WASD or the on-screen buttons", 22, MUTED, (W // 2, 700))


def draw_over(surf, game, high, new_high, again, home):
    surf.fill(BG)
    text(surf, "GAME OVER", 84, FOOD, (W // 2, 210))
    text(surf, f"Final Score: {game.score}", 46, TEXT, (W // 2, 320))
    text(surf, f"Level: {game.level}", 40, TEXT, (W // 2, 375))
    text(surf, f"High Score: {high}", 40, ACCENT, (W // 2, 430))
    if new_high:
        text(surf, "NEW HIGH SCORE!", 34, BTN_HOVER, (W // 2, 485))
    again.draw(surf)
    home.draw(surf)


# ---- Main loop -------------------------------------------------------------
async def main():
    pygame.init()
    pygame.display.set_caption("Snake Game")
    screen = pygame.display.set_mode((W, H), pygame.SCALED | pygame.RESIZABLE)
    clock = pygame.time.Clock()

    game = SnakeGame()
    high = load_high()
    state = "start"                          # start / playing / over
    new_high = False
    last_move = 0
    banner_until = 0
    pressed, pressed_until = None, 0

    start_btn = Button("START GAME", (W // 2, 560))
    again_btn = Button("PLAY AGAIN", (W // 2, 560))
    home_btn = Button("HOME", (W // 2, 650))
    pad = make_pad()
    keys = {pygame.K_UP: UP, pygame.K_w: UP, pygame.K_DOWN: DOWN, pygame.K_s: DOWN,
            pygame.K_LEFT: LEFT, pygame.K_a: LEFT, pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT}

    def start_game():
        nonlocal state, new_high, last_move
        game.reset()
        state, new_high = "playing", False
        last_move = pygame.time.get_ticks()

    while True:
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                return
            if e.type == pygame.KEYDOWN:
                if state == "playing" and e.key in keys:
                    game.set_direction(keys[e.key])
                elif state == "start" and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    start_game()
                elif state == "over" and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    start_game()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:   # also = finger tap
                if state == "start" and start_btn.hit(e.pos):
                    start_game()
                elif state == "over":
                    if again_btn.hit(e.pos):
                        start_game()
                    elif home_btn.hit(e.pos):
                        state = "start"
                elif state == "playing":
                    for name, (r, d) in pad.items():
                        if r.collidepoint(e.pos):
                            game.set_direction(d)
                            pressed, pressed_until = name, now + 120

        if state == "playing" and now - last_move >= 1000 / game.speed:
            last_move = now
            game.step()
            if game.leveled_up:
                banner_until = now + 1200
            if game.score > high:
                high, new_high = game.score, True
                save_high(high)
            if game.game_over:
                state = "over"

        if state == "start":
            draw_start(screen, start_btn, high)
        elif state == "over":
            draw_over(screen, game, high, new_high, again_btn, home_btn)
        else:
            screen.fill(BG)
            draw_hud(screen, game, high)
            draw_board(screen, game)
            if now < banner_until:
                text(screen, f"LEVEL {game.level}!", 70, ACCENT, (W // 2, BOARD_Y + BOARD_H // 2))
            draw_pad(screen, pad, pressed if now < pressed_until else None)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)               # required so it also runs in the browser


asyncio.run(main())
