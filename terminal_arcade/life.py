#!/usr/bin/env python3
"""🔮 Conway's Game of Life - Terminal Edition with colors and presets!"""
import curses
import random
import time

# Preset patterns
PRESETS = {
    "glider": [(0,1),(1,2),(2,0),(2,1),(2,2)],
    "blinker": [(0,0),(0,1),(0,2)],
    "toad": [(0,1),(0,2),(0,3),(1,0),(1,1),(1,2)],
    "beacon": [(0,0),(0,1),(1,0),(1,1),(2,2),(2,3),(3,2),(3,3)],
    "pulsar": [
        (0,2),(0,3),(0,4),(0,8),(0,9),(0,10),
        (2,0),(2,5),(2,7),(2,12),
        (3,0),(3,5),(3,7),(3,12),
        (4,0),(4,5),(4,7),(4,12),
        (5,2),(5,3),(5,4),(5,8),(5,9),(5,10),
        (7,2),(7,3),(7,4),(7,8),(7,9),(7,10),
        (8,0),(8,5),(8,7),(8,12),
        (9,0),(9,5),(9,7),(9,12),
        (10,0),(10,5),(10,7),(10,12),
        (12,2),(12,3),(12,4),(12,8),(12,9),(12,10),
    ],
    "glider_gun": [
        (0,24),
        (1,22),(1,24),
        (2,12),(2,13),(2,20),(2,21),(2,34),(2,35),
        (3,11),(3,15),(3,20),(3,21),(3,34),(3,35),
        (4,0),(4,1),(4,10),(4,16),(4,20),(4,21),
        (5,0),(5,1),(5,10),(5,14),(5,16),(5,17),(5,22),(5,24),
        (6,10),(6,16),(6,24),
        (7,11),(7,15),
        (8,12),(8,13),
    ],
    "spaceship": [(0,1),(0,4),(1,0),(2,0),(2,4),(3,0),(3,1),(3,2),(3,3)],
    "pentadecathlon": [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0)],  # simplified
    "diehard": [(0,6),(1,0),(1,1),(2,1),(2,5),(2,6),(2,7)],
    "acorn": [(0,1),(1,3),(2,0),(2,1),(2,4),(2,5),(2,6)],
    "r_pentomino": [(0,1),(0,2),(1,0),(1,1),(2,1)],
}

AGE_CHARS = [" ", "·", "•", "◦", "○", "●", "◉", "█"]
AGE_THRESHOLDS = [0, 1, 2, 4, 8, 16, 32, 64]


def create_grid(h, w):
    return [[0] * w for _ in range(h)]


def random_fill(grid, density=0.3):
    h, w = len(grid), len(grid[0])
    for y in range(h):
        for x in range(w):
            grid[y][x] = 1 if random.random() < density else 0


def place_pattern(grid, pattern, offset_y, offset_x):
    h, w = len(grid), len(grid[0])
    for dy, dx in pattern:
        y, x = offset_y + dy, offset_x + dx
        if 0 <= y < h and 0 <= x < w:
            grid[y][x] = 1


def count_neighbors(grid, y, x):
    h, w = len(grid), len(grid[0])
    count = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            ny, nx = (y + dy) % h, (x + dx) % w
            if grid[ny][nx] > 0:
                count += 1
    return count


def step(grid):
    h, w = len(grid), len(grid[0])
    new_grid = create_grid(h, w)
    births = deaths = 0
    for y in range(h):
        for x in range(w):
            n = count_neighbors(grid, y, x)
            if grid[y][x] > 0:
                if n in (2, 3):
                    new_grid[y][x] = grid[y][x] + 1  # age
                else:
                    deaths += 1
            else:
                if n == 3:
                    new_grid[y][x] = 1
                    births += 1
    return new_grid, births, deaths


def get_age_char(age):
    for i in range(len(AGE_THRESHOLDS) - 1, -1, -1):
        if age >= AGE_THRESHOLDS[i]:
            return AGE_CHARS[min(i, len(AGE_CHARS) - 1)]
    return " "


def get_age_color(age):
    if age <= 0:
        return 0
    elif age <= 2:
        return 2  # green (newborn)
    elif age <= 5:
        return 3  # cyan
    elif age <= 15:
        return 4  # yellow
    elif age <= 40:
        return 5  # magenta
    else:
        return 1  # red (ancient)


def count_alive(grid):
    return sum(1 for row in grid for cell in row if cell > 0)


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    h, w = stdscr.getmaxyx()
    grid_h = h - 3
    grid_w = w - 1

    grid = create_grid(grid_h, grid_w)

    # Start with some cool patterns
    mid_y, mid_x = grid_h // 2, grid_w // 2
    place_pattern(grid, PRESETS["r_pentomino"], mid_y - 5, mid_x - 5)
    place_pattern(grid, PRESETS["glider"], 3, 3)
    place_pattern(grid, PRESETS["glider"], 3, grid_w - 10)
    place_pattern(grid, PRESETS["acorn"], mid_y + 10, mid_x + 10)

    generation = 0
    paused = False
    speed = 0.05  # seconds per frame
    color_mode = True
    show_age = True
    total_births = 0
    total_deaths = 0

    preset_names = list(PRESETS.keys())
    preset_idx = 0

    stdscr.nodelay(True)
    stdscr.keypad(True)

    while True:
        # Draw
        stdscr.erase()

        # Grid
        for y in range(min(grid_h, h - 3)):
            for x in range(min(grid_w, w - 1)):
                age = grid[y][x]
                if age > 0:
                    if show_age:
                        ch = get_age_char(age)
                    else:
                        ch = "█"
                    if color_mode:
                        color = curses.color_pair(get_age_color(age))
                    else:
                        color = curses.color_pair(2)
                    try:
                        stdscr.addstr(y, x, ch, color | curses.A_BOLD)
                    except curses.error:
                        pass

        # Status bar
        alive = count_alive(grid)
        status_y = h - 2
        status = (f" Gen: {generation} | Alive: {alive} | "
                  f"Births: {total_births} | Deaths: {total_deaths} | "
                  f"Speed: {1/speed:.0f}fps | {'PAUSED' if paused else 'RUNNING'} ")
        try:
            stdscr.addstr(status_y, 0, "═" * (w - 1), curses.color_pair(4))
            stdscr.addstr(status_y + 1, 0, status[:w-1], curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

        # Controls hint
        controls = " Q:Quit SPACE:Pause +/-:Speed R:Random C:Clear P:Pattern N:Next A:AgeMode "
        try:
            stdscr.addstr(h - 1, max(0, w - len(controls) - 1), controls[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()

        # Input
        try:
            key = stdscr.getch()
        except:
            key = -1

        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == ord('+') or key == ord('='):
            speed = max(0.01, speed - 0.01)
        elif key == ord('-'):
            speed = min(0.5, speed + 0.01)
        elif key == ord('r') or key == ord('R'):
            grid = create_grid(grid_h, grid_w)
            random_fill(grid, 0.3)
            generation = 0
            total_births = total_deaths = 0
        elif key == ord('c') or key == ord('C'):
            grid = create_grid(grid_h, grid_w)
            generation = 0
            total_births = total_deaths = 0
        elif key == ord('p') or key == ord('P'):
            grid = create_grid(grid_h, grid_w)
            pattern = PRESETS[preset_names[preset_idx]]
            place_pattern(grid, pattern, mid_y, mid_x)
            preset_idx = (preset_idx + 1) % len(preset_names)
            generation = 0
            total_births = total_deaths = 0
        elif key == ord('n') or key == ord('N'):
            if paused:
                grid, births, deaths = step(grid)
                generation += 1
                total_births += births
                total_deaths += deaths
        elif key == ord('a') or key == ord('A'):
            show_age = not show_age
        elif key == ord('k') or key == ord('K'):
            color_mode = not color_mode

        # Step
        if not paused:
            grid, births, deaths = step(grid)
            generation += 1
            total_births += births
            total_deaths += deaths

        time.sleep(speed)


if __name__ == "__main__":
    curses.wrapper(main)


def main_entry():
    import curses
    curses.wrapper(main)

