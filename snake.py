#!/usr/bin/env python3
"""Terminal Snake Game — curses-based with color, speed scaling, and polish."""

import curses
import random
import time

# Direction vectors: (dy, dx)
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)

# Timing
BASE_DELAY = 0.12  # seconds per frame at score 0
MIN_DELAY = 0.045  # fastest possible
SPEED_STEP = 0.012  # delay reduction per 5 points


def init_colors():
    """Set up color pairs for the game."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)       # snake body
    curses.init_pair(2, curses.COLOR_GREEN, -1)        # snake head (bold)
    curses.init_pair(3, curses.COLOR_RED, -1)          # food
    curses.init_pair(4, curses.COLOR_YELLOW, -1)       # border
    curses.init_pair(5, curses.COLOR_CYAN, -1)         # score / UI text
    curses.init_pair(6, curses.COLOR_WHITE, -1)        # general text
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)      # title accent


def frame_delay(score: int) -> float:
    """Return the frame delay in seconds based on current score."""
    reduction = (score // 5) * SPEED_STEP
    return max(MIN_DELAY, BASE_DELAY - reduction)


def draw_border(win, h, w):
    """Draw a decorative border inside the window."""
    color = curses.color_pair(4)
    # Top and bottom horizontal lines
    for x in range(w):
        win.addch(1, x, curses.ACS_HLINE, color)
        try:
            win.addch(h - 1, x, curses.ACS_HLINE, color)
        except curses.error:
            pass
    # Left and right vertical lines
    for y in range(1, h):
        win.addch(y, 0, curses.ACS_VLINE, color)
        try:
            win.addch(y, w - 1, curses.ACS_VLINE, color)
        except curses.error:
            pass
    # Corners
    win.addch(1, 0, curses.ACS_ULCORNER, color)
    win.addch(1, w - 1, curses.ACS_URCORNER, color)
    try:
        win.addch(h - 1, 0, curses.ACS_LLCORNER, color)
    except curses.error:
        pass
    try:
        win.addch(h - 1, w - 1, curses.ACS_LRCORNER, color)
    except curses.error:
        pass


def draw_score(win, w, score, high_score):
    """Draw the score bar at the top of the screen."""
    win.addstr(0, 2, f" SCORE: {score} ", curses.color_pair(5) | curses.A_BOLD)
    hs_text = f" HIGH: {high_score} "
    win.addstr(0, w - len(hs_text) - 2, hs_text, curses.color_pair(7) | curses.A_BOLD)
    speed_level = score // 5
    speed_text = f" SPEED: {speed_level + 1} "
    mid = (w - len(speed_text)) // 2
    win.addstr(0, mid, speed_text, curses.color_pair(6))


def place_food(snake, play_top, play_bottom, play_left, play_right):
    """Place food at a random position not occupied by the snake."""
    while True:
        fy = random.randint(play_top, play_bottom)
        fx = random.randint(play_left, play_right)
        if (fy, fx) not in snake:
            return (fy, fx)


def welcome_screen(stdscr):
    """Show a welcome screen and wait for any key to start."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = [
        " ____              _        ",
        "/ ___| _ __   __ _| | _____ ",
        "\\___ \\| '_ \\ / _` | |/ / _ \\",
        " ___) | | | | (_| |   <  __/",
        "|____/|_| |_|\\__,_|_|\\_\\___|",
    ]

    start_y = max(0, h // 2 - 8)

    for i, line in enumerate(title):
        x = max(0, (w - len(line)) // 2)
        if start_y + i < h:
            stdscr.addstr(start_y + i, x, line, curses.color_pair(1) | curses.A_BOLD)

    instructions = [
        "",
        "Use ARROW KEYS or WASD to move",
        "Eat the red food to grow and score",
        "Speed increases every 5 points",
        "Don't hit the walls or yourself!",
        "",
        "Press any key to start...",
    ]

    for i, line in enumerate(instructions):
        y = start_y + len(title) + i
        x = max(0, (w - len(line)) // 2)
        if y < h:
            attr = curses.color_pair(5) | curses.A_BOLD if i == len(instructions) - 1 else curses.color_pair(6)
            stdscr.addstr(y, x, line, attr)

    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()


def game_over_screen(stdscr, score, high_score):
    """Show game-over overlay and wait for R (restart) or Q (quit)."""
    h, w = stdscr.getmaxyx()

    box_w = 36
    box_h = 9
    box_y = max(0, (h - box_h) // 2)
    box_x = max(0, (w - box_w) // 2)

    # Draw box background
    for dy in range(box_h):
        for dx in range(box_w):
            y, x = box_y + dy, box_x + dx
            if 0 <= y < h and 0 <= x < w:
                try:
                    stdscr.addch(y, x, ' ', curses.color_pair(3))
                except curses.error:
                    pass

    lines = [
        ("  G A M E   O V E R  ", curses.color_pair(3) | curses.A_BOLD | curses.A_REVERSE),
        ("", 0),
        (f"Final Score: {score}", curses.color_pair(6) | curses.A_BOLD),
        (f"High  Score: {high_score}", curses.color_pair(7) | curses.A_BOLD),
        ("", 0),
        ("Press R to restart", curses.color_pair(5)),
        ("Press Q to quit", curses.color_pair(5)),
    ]

    for i, (text, attr) in enumerate(lines):
        y = box_y + 1 + i
        x = box_x + (box_w - len(text)) // 2
        if 0 <= y < h and 0 <= x < w and text:
            stdscr.addstr(y, x, text, attr)

    stdscr.refresh()
    stdscr.nodelay(False)
    while True:
        ch = stdscr.getch()
        if ch in (ord('r'), ord('R')):
            return True
        if ch in (ord('q'), ord('Q'), 27):  # Q or Escape
            return False


def check_terminal_size(stdscr):
    """Ensure the terminal is large enough to play."""
    h, w = stdscr.getmaxyx()
    if h < 15 or w < 40:
        stdscr.clear()
        msg = "Terminal too small! Need at least 40x15."
        try:
            stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)
        except curses.error:
            pass
        stdscr.refresh()
        stdscr.nodelay(False)
        stdscr.getch()
        return False
    return True


def run_game(stdscr):
    """Main game loop."""
    curses.curs_set(0)
    init_colors()

    if not check_terminal_size(stdscr):
        return

    welcome_screen(stdscr)
    high_score = 0

    while True:
        if not check_terminal_size(stdscr):
            return

        h, w = stdscr.getmaxyx()

        # Playable area: inside the border (row 2..h-2, col 1..w-2)
        play_top = 2
        play_bottom = h - 2
        play_left = 1
        play_right = w - 2

        # Initial snake: 3 segments in the middle, moving right
        mid_y = (play_top + play_bottom) // 2
        mid_x = (play_left + play_right) // 2
        snake = [(mid_y, mid_x - i) for i in range(3)]
        direction = RIGHT
        next_direction = RIGHT
        score = 0
        food = place_food(set(snake), play_top, play_bottom, play_left, play_right)

        stdscr.nodelay(True)
        stdscr.timeout(1)

        last_frame = time.monotonic()

        while True:
            # --- Input (poll all queued keys, keep the last valid one) ---
            while True:
                ch = stdscr.getch()
                if ch == -1:
                    break
                if ch == curses.KEY_UP or ch in (ord('w'), ord('W')):
                    if direction != DOWN:
                        next_direction = UP
                elif ch == curses.KEY_DOWN or ch in (ord('s'), ord('S')):
                    if direction != UP:
                        next_direction = DOWN
                elif ch == curses.KEY_LEFT or ch in (ord('a'), ord('A')):
                    if direction != RIGHT:
                        next_direction = LEFT
                elif ch == curses.KEY_RIGHT or ch in (ord('d'), ord('D')):
                    if direction != LEFT:
                        next_direction = RIGHT
                elif ch in (ord('q'), ord('Q'), 27):
                    return  # quit immediately

            # --- Frame timing ---
            now = time.monotonic()
            delay = frame_delay(score)
            if now - last_frame < delay:
                time.sleep(0.005)
                continue
            last_frame = now

            # --- Update ---
            direction = next_direction
            head_y, head_x = snake[0]
            new_head = (head_y + direction[0], head_x + direction[1])

            # Wall collision
            ny, nx = new_head
            if ny < play_top or ny > play_bottom or nx < play_left or nx > play_right:
                break  # game over

            # Self collision
            if new_head in set(snake):
                break  # game over

            snake.insert(0, new_head)

            # Food collision
            if new_head == food:
                score += 1
                if score > high_score:
                    high_score = score
                food = place_food(set(snake), play_top, play_bottom, play_left, play_right)
            else:
                snake.pop()

            # --- Draw ---
            stdscr.erase()
            draw_border(stdscr, h, w)
            draw_score(stdscr, w, score, high_score)

            # Food
            try:
                stdscr.addch(food[0], food[1], '*', curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass

            # Snake body
            for i, (sy, sx) in enumerate(snake):
                if i == 0:
                    # Head: bright green, bold
                    ch = '@'
                    attr = curses.color_pair(2) | curses.A_BOLD
                else:
                    ch = 'o'
                    attr = curses.color_pair(1)
                try:
                    stdscr.addch(sy, sx, ch, attr)
                except curses.error:
                    pass

            stdscr.refresh()

        # Game over
        if not game_over_screen(stdscr, score, high_score):
            return  # player chose quit


def main():
    curses.wrapper(run_game)


if __name__ == "__main__":
    main()
