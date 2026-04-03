#!/usr/bin/env python3
"""
Matrix Digital Rain - A faithful recreation of the iconic falling code effect.

Controls:
  q - Quit
  c - Cycle color mode (green / blue / red / rainbow)

Usage:
  python3 matrix.py
"""

import curses
import random
import time
import locale

# Ensure wide-char support
locale.setlocale(locale.LC_ALL, "")

# ---------------------------------------------------------------------------
# Character pools
# ---------------------------------------------------------------------------

# Half-width katakana (ｱ-ﾝ)
KATAKANA = [chr(c) for c in range(0xFF66, 0xFF9E)]

# ASCII digits + symbols used in the movie
ASCII_CHARS = list("0123456789ABCDEFabcdef!@#$%^&*()_+-=[]{}|;':\",./<>?~`\\")

# Random CJK Unified Ideographs subset (common kanji / hanzi)
CJK_CHARS = [chr(c) for c in range(0x4E00, 0x4E00 + 200)]

ALL_CHARS = KATAKANA + ASCII_CHARS + CJK_CHARS


def rand_char() -> str:
    return random.choice(ALL_CHARS)


# ---------------------------------------------------------------------------
# Color setup
# ---------------------------------------------------------------------------

COLOR_MODE_GREEN = 0
COLOR_MODE_BLUE = 1
COLOR_MODE_RED = 2
COLOR_MODE_RAINBOW = 3
COLOR_MODE_COUNT = 4

COLOR_MODE_NAMES = ["GREEN", "BLUE", "RED", "RAINBOW"]


def init_colors():
    """Set up color pairs for each mode.

    Pair layout per mode (mode * 10 + offset):
      +1  bright head (white on black)
      +2  bright body (bright color on black)
      +3  medium body
      +4  dim body
      +5  very dim tail
    """
    curses.start_color()
    curses.use_default_colors()

    # Base colors per mode
    bases = {
        COLOR_MODE_GREEN: curses.COLOR_GREEN,
        COLOR_MODE_BLUE: curses.COLOR_CYAN,
        COLOR_MODE_RED: curses.COLOR_RED,
    }

    for mode, color in bases.items():
        off = mode * 10
        curses.init_pair(off + 1, curses.COLOR_WHITE, -1)
        curses.init_pair(off + 2, color, -1)
        curses.init_pair(off + 3, color, -1)
        curses.init_pair(off + 4, color, -1)
        curses.init_pair(off + 5, color, -1)

    # Rainbow uses green pairs as default; the head rotates
    off = COLOR_MODE_RAINBOW * 10
    curses.init_pair(off + 1, curses.COLOR_WHITE, -1)
    curses.init_pair(off + 2, curses.COLOR_GREEN, -1)
    curses.init_pair(off + 3, curses.COLOR_CYAN, -1)
    curses.init_pair(off + 4, curses.COLOR_BLUE, -1)
    curses.init_pair(off + 5, curses.COLOR_MAGENTA, -1)


def get_attr(mode: int, depth: int, length: int) -> int:
    """Return curses attribute for a character at *depth* positions behind the
    head of a stream with total visible *length*.

    depth=0 is the leading (head) character.
    """
    off = mode * 10
    ratio = depth / max(length, 1)

    if depth == 0:
        # Bright white head
        return curses.color_pair(off + 1) | curses.A_BOLD
    elif ratio < 0.25:
        return curses.color_pair(off + 2) | curses.A_BOLD
    elif ratio < 0.50:
        return curses.color_pair(off + 3) | curses.A_BOLD
    elif ratio < 0.75:
        return curses.color_pair(off + 3)
    elif ratio < 0.90:
        return curses.color_pair(off + 4) | curses.A_DIM
    else:
        return curses.color_pair(off + 5) | curses.A_DIM


# ---------------------------------------------------------------------------
# Stream (one column of falling characters)
# ---------------------------------------------------------------------------

class Stream:
    """A single column of falling characters."""

    __slots__ = (
        "col", "speed", "length", "head_y", "chars",
        "delay", "max_rows", "alive", "mutate_rate",
    )

    def __init__(self, col: int, max_rows: int):
        self.col = col
        self.max_rows = max_rows
        self.reset()

    def reset(self):
        self.speed = random.choice([1, 1, 1, 2, 2, 3])  # cells per tick
        self.length = random.randint(4, max(5, self.max_rows - 4))
        self.head_y = random.randint(-self.max_rows, -1)  # start above screen
        self.delay = random.randint(0, 40)  # ticks before starting
        self.chars = [rand_char() for _ in range(self.length)]
        self.alive = True
        self.mutate_rate = random.uniform(0.02, 0.12)

    def tick(self):
        if self.delay > 0:
            self.delay -= 1
            return

        self.head_y += self.speed

        # Randomly mutate characters in the trail
        for i in range(len(self.chars)):
            if random.random() < self.mutate_rate:
                self.chars[i] = rand_char()

        # Stream has fully left the screen
        if self.head_y - self.length > self.max_rows:
            self.reset()

    def draw(self, stdscr, mode: int, max_cols: int):
        if self.delay > 0:
            return

        for i in range(self.length):
            y = self.head_y - i
            if y < 0 or y >= self.max_rows:
                continue
            if self.col >= max_cols:
                continue

            ch = self.chars[i % len(self.chars)]
            attr = get_attr(mode, i, self.length)

            try:
                stdscr.addstr(y, self.col, ch, attr)
            except curses.error:
                # Writing to bottom-right corner raises an error; ignore
                pass


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main(stdscr):
    # Curses setup
    curses.curs_set(0)          # Hide cursor
    stdscr.nodelay(True)        # Non-blocking getch
    stdscr.timeout(0)
    init_colors()

    color_mode = COLOR_MODE_GREEN
    target_fps = 30
    frame_duration = 1.0 / target_fps

    max_rows, max_cols = stdscr.getmaxyx()

    # Create streams -- roughly one per column, some columns get extras
    streams: list[Stream] = []
    for col in range(0, max_cols):
        streams.append(Stream(col, max_rows))
        # ~30% chance of a second overlapping stream for density
        if random.random() < 0.3:
            s = Stream(col, max_rows)
            s.delay += random.randint(10, 50)
            streams.append(s)

    show_hud = True
    frame_count = 0

    while True:
        t0 = time.monotonic()

        # --- Input ---
        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            break
        elif key == ord("c") or key == ord("C"):
            color_mode = (color_mode + 1) % COLOR_MODE_COUNT
        elif key == ord("h") or key == ord("H"):
            show_hud = not show_hud
        elif key == curses.KEY_RESIZE:
            max_rows, max_cols = stdscr.getmaxyx()
            # Rebuild streams for new size
            streams.clear()
            for col in range(0, max_cols):
                streams.append(Stream(col, max_rows))
                if random.random() < 0.3:
                    s = Stream(col, max_rows)
                    s.delay += random.randint(10, 50)
                    streams.append(s)

        # --- Update ---
        for stream in streams:
            stream.max_rows = max_rows
            stream.tick()

        # --- Draw ---
        stdscr.erase()

        for stream in streams:
            stream.draw(stdscr, color_mode, max_cols)

        # HUD overlay
        if show_hud:
            hud = f" [{COLOR_MODE_NAMES[color_mode]}]  q:quit  c:color  h:hud "
            try:
                stdscr.addstr(0, max_cols - len(hud) - 1, hud,
                              curses.color_pair(color_mode * 10 + 1) | curses.A_DIM)
            except curses.error:
                pass

        stdscr.refresh()

        # --- Frame limiter ---
        elapsed = time.monotonic() - t0
        sleep_time = frame_duration - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

        frame_count += 1


if __name__ == "__main__":
    curses.wrapper(main)


def main_entry():
    import curses
    curses.wrapper(main)

