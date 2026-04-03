#!/usr/bin/env python3
"""✨ Terminal Lissajous Curves - Mesmerizing parametric patterns"""
import curses
import math
import time

PRESETS = [
    (1, 2, 0, "Figure-8"),
    (3, 2, math.pi/2, "Trefoil"),
    (3, 4, 0, "Bow Tie"),
    (5, 4, math.pi/4, "Star"),
    (3, 5, math.pi/6, "Flower"),
    (7, 6, 0, "Complex"),
    (1, 1, math.pi/4, "Circle→Ellipse"),
    (5, 3, math.pi/3, "Butterfly"),
]


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    for i in range(1, 8):
        curses.init_pair(i, i, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    stdscr.nodelay(True)
    stdscr.keypad(True)

    preset_idx = 0
    t = 0
    speed = 1.0
    trail_len = 500
    trail = []
    phase_drift = 0
    auto_morph = True
    last_time = time.time()

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
        elif key == ord('p') or key == ord('P'):
            preset_idx = (preset_idx + 1) % len(PRESETS)
            trail.clear()
        elif key == ord('+') or key == ord('='):
            speed = min(5, speed + 0.2)
        elif key == ord('-'):
            speed = max(0.1, speed - 0.2)
        elif key == ord('m') or key == ord('M'):
            auto_morph = not auto_morph
        elif key == ord('c') or key == ord('C'):
            trail.clear()

        h, w = stdscr.getmaxyx()
        cx, cy = w // 2, (h - 2) // 2

        a, b, delta, name = PRESETS[preset_idx]
        if auto_morph:
            phase_drift += dt * 0.3
            delta = delta + math.sin(phase_drift) * 0.5

        # Calculate new point
        scale_x = (w - 4) // 2
        scale_y = (h - 6) // 2
        px = cx + int(math.sin(a * t + delta) * scale_x)
        py = cy + int(math.sin(b * t) * scale_y)

        trail.append((px, py, t))
        if len(trail) > trail_len:
            trail.pop(0)

        stdscr.erase()

        # Draw trail
        for i, (tx, ty, tt) in enumerate(trail):
            if 0 <= ty < h - 1 and 0 <= tx < w - 1:
                age = i / len(trail)
                color = int(age * 6) % 7 + 1
                if age > 0.9:
                    ch, attr = "●", curses.A_BOLD
                elif age > 0.7:
                    ch, attr = "◉", curses.A_BOLD
                elif age > 0.4:
                    ch, attr = "○", 0
                elif age > 0.2:
                    ch, attr = "·", 0
                else:
                    ch, attr = "·", curses.A_DIM
                try:
                    stdscr.addstr(ty, tx, ch, curses.color_pair(color) | attr)
                except curses.error:
                    pass

        # Status
        try:
            status = f" ✨ {name} (a={a},b={b}) | Morph:{'ON' if auto_morph else 'OFF'} | P:Preset M:Morph C:Clear +/-:Speed Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.02)


if __name__ == "__main__":
    curses.wrapper(main)
