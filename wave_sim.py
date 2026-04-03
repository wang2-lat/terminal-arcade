#!/usr/bin/env python3
"""🌊 Terminal Wave Interference - Beautiful wave pattern simulator"""
import curses
import math
import time
import random

CHARS = " ·∙•◦○◎●◉█"


class WaveSource:
    def __init__(self, x, y, freq=1.0, amp=1.0, phase=0):
        self.x = x
        self.y = y
        self.freq = freq
        self.amp = amp
        self.phase = phase
        self.color = random.choice([1, 2, 3, 4, 5, 6])


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

    h, w = stdscr.getmaxyx()
    sources = [
        WaveSource(w // 3, h // 2, 2.0, 1.0, 0),
        WaveSource(2 * w // 3, h // 2, 2.0, 1.0, 0),
    ]

    t = 0
    speed = 1.0
    mode = 0  # 0=interference, 1=ripple, 2=standing
    last_time = time.time()
    color_mode = True

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
        elif key == ord('+') or key == ord('='):
            speed = min(5, speed + 0.2)
        elif key == ord('-'):
            speed = max(0.1, speed - 0.2)
        elif key == ord('a') or key == ord('A'):
            sources.append(WaveSource(
                random.randint(5, w - 5), random.randint(3, h - 5),
                random.uniform(1, 4), 1.0, random.uniform(0, math.pi * 2)
            ))
        elif key == ord('r') or key == ord('R'):
            sources = [WaveSource(w // 3, h // 2), WaveSource(2 * w // 3, h // 2)]
        elif key == ord('c') or key == ord('C'):
            color_mode = not color_mode
        elif key == ord('m') or key == ord('M'):
            mode = (mode + 1) % 3

        h, w = stdscr.getmaxyx()
        stdscr.erase()

        for sy in range(h - 1):
            for sx in range(w - 1):
                total = 0
                for src in sources:
                    dx = (sx - src.x) * 0.5  # aspect correction
                    dy = sy - src.y
                    dist = math.sqrt(dx * dx + dy * dy)

                    if mode == 0:  # Circular waves
                        total += src.amp * math.sin(dist * src.freq - t * 4 + src.phase)
                    elif mode == 1:  # Decaying ripples
                        decay = 1.0 / (1 + dist * 0.1)
                        total += src.amp * decay * math.sin(dist * src.freq - t * 4 + src.phase)
                    else:  # Standing waves
                        total += src.amp * math.sin(dist * src.freq + src.phase) * math.cos(t * 4)

                # Normalize
                val = total / max(1, len(sources))
                val = max(-1, min(1, val))

                # Map to character
                ci = int((val + 1) / 2 * (len(CHARS) - 1))
                ci = max(0, min(len(CHARS) - 1, ci))
                ch = CHARS[ci]

                if ch == ' ':
                    continue

                if color_mode:
                    color = int((val + 1) / 2 * 6) % 7 + 1
                else:
                    color = 4

                try:
                    attr = curses.A_BOLD if val > 0.5 else 0
                    stdscr.addstr(sy, sx, ch, curses.color_pair(color) | attr)
                except curses.error:
                    pass

        # Source markers
        for i, src in enumerate(sources):
            if 0 <= int(src.y) < h - 1 and 0 <= int(src.x) < w - 1:
                try:
                    stdscr.addstr(int(src.y), int(src.x), "◉",
                                 curses.color_pair(src.color) | curses.A_BOLD)
                except curses.error:
                    pass

        modes = ["Interference", "Ripple", "Standing"]
        try:
            status = f" 🌊 {modes[mode]} | Sources: {len(sources)} | A:Add R:Reset M:Mode C:Color +/-:Speed Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.04)


if __name__ == "__main__":
    curses.wrapper(main)
