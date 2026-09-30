"""
game.py - Snake game LOGIC (pure Python, no graphics).

Keeping the rules separate from the drawing code (main.py) makes the game
easy to understand and easy to test.
"""
import random

# ---- Board -----------------------------------------------------------------
COLS, ROWS = 20, 20

# ---- Directions (dx, dy) ---------------------------------------------------
UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)

# ---- Scoring and levels ----------------------------------------------------
POINTS_PER_FOOD = 10
POINTS_PER_LEVEL = 50      # Level 2 at 50, Level 3 at 100, ... Level 5 at 200
MAX_LEVEL = 5
OBSTACLES_PER_LEVEL = 3    # every level-up adds 3 more obstacle blocks

# ---- Speed (moves per second) ----------------------------------------------
START_SPEED = 4.0          # slow at the beginning
SPEED_STEP = 0.5           # added after EVERY food eaten
MAX_SPEED = 16.0           # cap so the game stays playable


class SnakeGame:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]  # head first
        self.direction = RIGHT
        self.queue = []            # buffered direction changes
        self.score = 0
        self.foods_eaten = 0
        self.level = 1
        self.obstacles = set()
        self.game_over = False
        self.leveled_up = False    # True for the step in which a level-up happened
        self.food = None
        self._place_food()

    # ---- Feature: Increasing Speed ----------------------------------------
    @property
    def speed(self):
        """Moves per second. Depends ONLY on foods eaten, never on level."""
        return min(MAX_SPEED, START_SPEED + SPEED_STEP * self.foods_eaten)

    @property
    def speed_percent(self):
        return round((self.speed - START_SPEED) / (MAX_SPEED - START_SPEED) * 100)

    # ---- Feature: Multiple Levels -----------------------------------------
    @staticmethod
    def level_for(score):
        return min(MAX_LEVEL, 1 + score // POINTS_PER_LEVEL)

    # ---- Input --------------------------------------------------------------
    def set_direction(self, new_dir):
        """Queue a turn. Ignores reversing into yourself."""
        ref = self.queue[-1] if self.queue else self.direction
        if new_dir == ref or new_dir == (-ref[0], -ref[1]):
            return
        if len(self.queue) < 2:
            self.queue.append(new_dir)

    # ---- One game tick ------------------------------------------------------
    def step(self):
        """Move the snake one cell. Returns 'moved', 'ate' or 'dead'."""
        if self.game_over:
            return "dead"
        self.leveled_up = False
        if self.queue:
            self.direction = self.queue.pop(0)

        hx, hy = self.snake[0]
        new_head = (hx + self.direction[0], hy + self.direction[1])
        eating = new_head == self.food

        # ---- Feature: Game-over detection ----
        body = self.snake if eating else self.snake[:-1]  # tail cell frees up
        if (not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS)  # wall
                or new_head in body                                     # itself
                or new_head in self.obstacles):                         # obstacle
            self.game_over = True
            return "dead"

        self.snake.insert(0, new_head)
        if not eating:
            self.snake.pop()
            return "moved"

        # ---- Ate food: score up, snake grows (no pop), speed up ----
        self.score += POINTS_PER_FOOD
        self.foods_eaten += 1
        new_level = self.level_for(self.score)
        while self.level < new_level:
            self.level += 1
            self.leveled_up = True
            self._add_obstacles(OBSTACLES_PER_LEVEL)
        self._place_food()
        return "ate"

    # ---- Helpers ------------------------------------------------------------
    def _free_cells(self):
        taken = set(self.snake) | self.obstacles
        return [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in taken]

    def _place_food(self):
        free = self._free_cells()
        if not free:               # board completely full = player won
            self.food = None
            self.game_over = True
            return
        self.food = self.rng.choice(free)

    def _add_obstacles(self, count):
        hx, hy = self.snake[0]
        candidates = [c for c in self._free_cells()
                      if c != self.food and abs(c[0] - hx) + abs(c[1] - hy) >= 5]
        self.rng.shuffle(candidates)
        self.obstacles.update(candidates[:count])
