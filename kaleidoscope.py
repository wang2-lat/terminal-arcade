#!/usr/bin/env python3
"""🎪 Terminal Kaleidoscope - Mesmerizing symmetric color patterns"""
import curses
import math
import time
import random

CHARS = "·•◦○●◉◎★✦✧♦♠♣♥♦◆◇■□▲△▼▽"
SYMMETRY_MODES = [4, 6, 8, 12]


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    stdscr.nodelay(True)
    stdscr.keypad(True)

    t = 0
    speed = 1.0
    symmetry_idx = 2  # 8-fold
    pattern = 0
    last_time = time.time()

    # Pattern parameters that evolve
    params = [random.uniform(0.5, 3) for _ in range(8)]
    param_speeds = [random.uniform(-0.3, 0.3) for _ in range(8)]

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now
        t += dt * speed

        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord('s') or key == ord('S'):
            symmetry_idx = (symmetry_idx + 1) % len(SYMMETRY_MODES)
        elif key == ord('p') or key == ord('P'):
            pattern = (pattern + 1) % 5
        elif key == ord('+') or key == ord('='):
            speed = min(5.0, speed + 0.2)
        elif key == ord('-'):
            speed = max(0.1, speed - 0.2)
        elif key == ord('r') or key == ord('R'):
            params = [random.uniform(0.5, 3) for _ in range(8)]
            param_speeds = [random.uniform(-0.3, 0.3) for _ in range(8)]

        # Evolve parameters
        for i in range(len(params)):
            params[i] += param_speeds[i] * dt
            if params[i] > 4 or params[i] < 0.2:
                param_speeds[i] *= -1

        h, w = stdscr.getmaxyx()
        cx, cy = w // 2, h // 2
        symmetry = SYMMETRY_MODES[symmetry_idx]

        stdscr.erase()

        for y in range(h - 1):
            for x in range(w - 1):
                # Convert to centered coordinates
                dx = (x - cx) / max(1, cx)
                dy = (y - cy) / max(1, cy) * 2  # Correct aspect ratio

                # Convert to polar
                r = math.sqrt(dx * dx + dy * dy)
                theta = math.atan2(dy, dx)

                # Apply symmetry
                theta = abs(((theta / math.pi * symmetry / 2) % 2) - 1) * math.pi * 2 / symmetry

                # Generate value based on pattern
                if pattern == 0:  # Spiral
                    val = math.sin(r * params[0] * 5 - t * 2 + theta * params[1]) * \
                          math.cos(theta * params[2] + t) * \
                          math.sin(r * params[3] + t * 0.5)
                elif pattern == 1:  # Rings
                    val = math.sin(r * params[0] * 8 - t * 3) * \
                          math.cos(theta * params[1] * 3 + r * params[2]) * \
                          math.sin(t + r * params[3])
                elif pattern == 2:  # Flowers
                    val = math.sin(theta * params[0] * 4 + math.sin(r * params[1] * 3 + t)) * \
                          math.cos(r * params[2] * 5 - t * 2) * \
                          (1 - r * 0.3)
                elif pattern == 3:  # Waves
                    val = math.sin(dx * params[0] * 5 + t * 2) * \
                          math.cos(dy * params[1] * 5 + t * 1.5) * \
                          math.sin(r * params[2] * 3 - t)
                else:  # Geometric
                    val = math.sin(abs(dx) * params[0] * 6 + t) * \
                          math.sin(abs(dy) * params[1] * 6 + t * 0.7) * \
                          math.cos(theta * params[2] * 2 + t * 0.5) * \
                          math.sin(r * params[3] * 4)

                if abs(val) < 0.15 or r > 1.2:
                    continue

                # Map to character
                char_idx = int((val + 1) / 2 * (len(CHARS) - 1))
                char_idx = max(0, min(len(CHARS) - 1, char_idx))
                ch = CHARS[char_idx]

                # Map to color
                color_val = (val * 3 + r * 2 + t * 0.3) % 7
                color = int(color_val) + 1

                attr = curses.A_BOLD if abs(val) > 0.6 else 0

                try:
                    stdscr.addstr(y, x, ch, curses.color_pair(color) | attr)
                except curses.error:
                    pass

        # Status
        patterns = ["Spiral", "Rings", "Flowers", "Waves", "Geometric"]
        try:
            status = f" 🎪 {patterns[pattern]} | {symmetry}-fold | Speed:{speed:.1f}x | S:Symmetry P:Pattern R:Randomize Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.04)


if __name__ == "__main__":
    curses.wrapper(main)
