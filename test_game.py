"""Run with:  python test_game.py   (checks the game rules without graphics)"""
import random
from game import *


def feed(g):
    """Put food directly in front of the snake's head."""
    hx, hy = g.snake[0]
    g.food = (hx + g.direction[0], hy + g.direction[1])


def test_start():
    g = SnakeGame(random.Random(1))
    assert g.score == 0 and g.level == 1 and g.speed == START_SPEED and g.speed_percent == 0
    assert len(g.snake) == 3 and not g.game_over


def test_move():
    g = SnakeGame(random.Random(1))
    head = g.snake[0]
    g.food = (0, 0)
    assert g.step() == "moved"
    assert g.snake[0] == (head[0] + 1, head[1]) and len(g.snake) == 3


def test_speed_up_after_every_food():
    g = SnakeGame(random.Random(1))
    last = g.speed
    for i in range(1, 6):
        g.direction = RIGHT if i % 2 else LEFT   # keep it on the board
        g.snake = [(10, 10), (9, 10), (8, 10)] if i % 2 else [(10, 10), (11, 10), (12, 10)]
        g.obstacles = set()
        feed(g)
        assert g.step() == "ate"
        assert g.speed > last, "speed must rise after EVERY food"
        last = g.speed
        assert len(g.snake) == 4 and g.score == 10 * i   # grew by 1


def test_speed_cap_and_not_reset_on_level():
    g = SnakeGame(random.Random(1))
    g.foods_eaten = 100
    assert g.speed == MAX_SPEED
    g = SnakeGame(random.Random(1))
    g.foods_eaten, g.score = 4, 40
    before = g.speed
    g.snake, g.direction, g.obstacles = [(10, 10), (9, 10), (8, 10)], RIGHT, set()
    feed(g)
    g.step()                                   # score 50 -> level 2
    assert g.level == 2 and g.leveled_up
    assert g.speed == before + SPEED_STEP      # speed kept and increased
    assert len(g.obstacles) == OBSTACLES_PER_LEVEL


def test_levels():
    assert [SnakeGame.level_for(s) for s in (0, 49, 50, 100, 150, 200, 999)] == [1, 1, 2, 3, 4, 5, 5]


def test_wall_game_over():
    g = SnakeGame(random.Random(1))
    g.snake, g.direction, g.food = [(COLS - 1, 5), (COLS - 2, 5), (COLS - 3, 5)], RIGHT, (0, 0)
    assert g.step() == "dead" and g.game_over


def test_self_game_over():
    g = SnakeGame(random.Random(1))
    g.snake = [(5, 5), (6, 5), (6, 6), (5, 6), (4, 6), (4, 5), (3, 5)]
    g.direction, g.food = UP, (0, 0)
    g.set_direction(LEFT); g.step()            # (4,5) is body -> dead
    assert g.game_over


def test_obstacle_game_over():
    g = SnakeGame(random.Random(1))
    hx, hy = g.snake[0]
    g.obstacles = {(hx + 1, hy)}
    g.food = (0, 0)
    assert g.step() == "dead"


def test_no_reverse():
    g = SnakeGame(random.Random(1))
    g.set_direction(LEFT)                      # opposite of RIGHT -> ignored
    assert g.queue == []
    g.set_direction(UP); g.set_direction(LEFT)
    assert g.queue == [UP, LEFT]


def test_restart():
    g = SnakeGame(random.Random(1))
    g.score, g.foods_eaten, g.game_over = 90, 9, True
    g.reset()
    assert g.score == 0 and g.speed == START_SPEED and not g.game_over and g.level == 1


def test_food_never_on_snake_or_obstacle():
    g = SnakeGame(random.Random(3))
    for _ in range(300):
        g.obstacles = {(2, 2), (3, 3)}
        g._place_food()
        assert g.food not in g.snake and g.food not in g.obstacles


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"\nAll {len(tests)} tests passed.")
