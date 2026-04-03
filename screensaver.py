#!/usr/bin/env python3
"""💫 Terminal Screensaver Collection - Multiple animated screensavers"""
import curses
import math
import time
import random

MODES = ["Starfield", "Pipes", "Toasters", "Bouncing", "Plasma", "Rain"]


def draw_starfield(stdscr, h, w, t, stars):
    """3D starfield flying through space."""
    cx, cy = w // 2, h // 2
    for i, (sx, sy, sz) in enumerate(stars):
        sz -= 0.05
        if sz <= 0.01:
            stars[i] = (random.uniform(-1, 1), random.uniform(-1, 1), 1)
            continue
        stars[i] = (sx, sy, sz)

        px = int(cx + sx / sz * cx * 1.5)
        py = int(cy + sy / sz * cy)

        if 0 <= py < h - 1 and 0 <= px < w - 1:
            if sz < 0.2:
                ch, color = "█", 7
            elif sz < 0.4:
                ch, color = "●", 7
            elif sz < 0.6:
                ch, color = "•", 4
            else:
                ch, color = "·", 8
            try:
                stdscr.addstr(py, px, ch, curses.color_pair(color))
            except curses.error:
                pass


def draw_pipes(stdscr, h, w, pipes, t):
    """Screen pipe screensaver."""
    PIPE_CHARS = "│─┌┐└┘├┤┬┴┼"
    if not pipes or random.random() < 0.05:
        pipes.append({
            "x": random.randint(1, w - 2),
            "y": random.randint(1, h - 3),
            "dir": random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)]),
            "color": random.randint(1, 7),
            "age": 0,
        })

    for pipe in pipes:
        pipe["age"] += 1
        if random.random() < 0.15:
            dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            pipe["dir"] = random.choice(dirs)

        dx, dy = pipe["dir"]
        pipe["x"] += dx
        pipe["y"] += dy

        if not (0 <= pipe["y"] < h - 1 and 0 <= pipe["x"] < w - 1):
            pipe["x"] = random.randint(1, w - 2)
            pipe["y"] = random.randint(1, h - 3)

        ch = "─" if dy == 0 else "│"
        try:
            stdscr.addstr(pipe["y"], pipe["x"], ch,
                         curses.color_pair(pipe["color"]) | curses.A_BOLD)
        except curses.error:
            pass

    if len(pipes) > 10:
        pipes.pop(0)


def draw_bouncing(stdscr, h, w, bouncers, t):
    """Bouncing text logos."""
    if not bouncers:
        texts = ["DVD", "HELLO", "ASCII", "FUN", "PYTHON", "CURSES"]
        for text in texts[:3]:
            bouncers.append({
                "text": text,
                "x": random.uniform(5, w - 10),
                "y": random.uniform(2, h - 5),
                "vx": random.choice([-1, 1]) * random.uniform(0.2, 0.5),
                "vy": random.choice([-1, 1]) * random.uniform(0.1, 0.3),
                "color": random.randint(1, 7),
            })

    for b in bouncers:
        b["x"] += b["vx"]
        b["y"] += b["vy"]

        if b["x"] < 0 or b["x"] + len(b["text"]) > w:
            b["vx"] *= -1
            b["color"] = random.randint(1, 7)
        if b["y"] < 0 or b["y"] > h - 2:
            b["vy"] *= -1
            b["color"] = random.randint(1, 7)

        try:
            stdscr.addstr(int(b["y"]), int(b["x"]), b["text"],
                         curses.color_pair(b["color"]) | curses.A_BOLD)
        except curses.error:
            pass


def draw_plasma(stdscr, h, w, t):
    """Plasma effect."""
    chars = " ·∙•◦○◎●◉█"
    for y in range(h - 1):
        for x in range(w - 1):
            v = math.sin(x * 0.1 + t)
            v += math.sin(y * 0.1 + t * 0.5)
            v += math.sin((x + y) * 0.1 + t * 0.3)
            v += math.sin(math.sqrt(x * x + y * y) * 0.05 + t * 0.7)
            v = (v + 4) / 8  # normalize to 0-1

            ci = int(v * (len(chars) - 1))
            color = int(v * 6) + 1

            if chars[ci] != ' ':
                try:
                    stdscr.addstr(y, x, chars[ci], curses.color_pair(color))
                except curses.error:
                    pass


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

    mode = 0
    t = 0
    stars = [(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.01, 1)) for _ in range(200)]
    pipes = []
    bouncers = []
    last_time = time.time()

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now
        t += dt

        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord(' ') or key == ord('m') or key == ord('M'):
            mode = (mode + 1) % len(MODES)
            pipes.clear()
            bouncers.clear()
            stdscr.clear()

        h, w = stdscr.getmaxyx()

        if mode != 1:  # Don't erase pipes
            stdscr.erase()

        if mode == 0:
            draw_starfield(stdscr, h, w, t, stars)
        elif mode == 1:
            draw_pipes(stdscr, h, w, pipes, t)
        elif mode == 2:  # toasters - use bouncing with emojis
            if not bouncers:
                for _ in range(5):
                    bouncers.append({
                        "text": random.choice(["★", "☆", "✦", "◆", "♦", "⬡"]),
                        "x": random.uniform(5, w - 10),
                        "y": random.uniform(2, h - 5),
                        "vx": random.choice([-1, 1]) * random.uniform(0.3, 0.8),
                        "vy": random.choice([-1, 1]) * random.uniform(0.15, 0.4),
                        "color": random.randint(1, 7),
                    })
            draw_bouncing(stdscr, h, w, bouncers, t)
        elif mode == 3:
            draw_bouncing(stdscr, h, w, bouncers, t)
        elif mode == 4:
            draw_plasma(stdscr, h, w, t)
        elif mode == 5:
            # Digital rain (simplified)
            for x in range(w - 1):
                if random.random() < 0.03:
                    y = random.randint(0, h - 2)
                    ch = random.choice("01アイウエオカキ")
                    try:
                        stdscr.addstr(y, x, ch, curses.color_pair(2))
                    except curses.error:
                        pass

        try:
            status = f" 💫 {MODES[mode]} | SPACE/M:Next mode Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.04 if mode != 4 else 0.06)


if __name__ == "__main__":
    curses.wrapper(main)
