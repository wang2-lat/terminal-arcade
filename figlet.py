#!/usr/bin/env python3
"""🌈 Terminal Rainbow Text - Big ASCII art text with rainbow colors!"""
import curses
import math
import time
import sys

# Simple 5-line font for A-Z and 0-9
FONT = {
    'A': ["  █  ", " █ █ ", "█████", "█   █", "█   █"],
    'B': ["████ ", "█   █", "████ ", "█   █", "████ "],
    'C': [" ████", "█    ", "█    ", "█    ", " ████"],
    'D': ["████ ", "█   █", "█   █", "█   █", "████ "],
    'E': ["█████", "█    ", "████ ", "█    ", "█████"],
    'F': ["█████", "█    ", "████ ", "█    ", "█    "],
    'G': [" ████", "█    ", "█  ██", "█   █", " ████"],
    'H': ["█   █", "█   █", "█████", "█   █", "█   █"],
    'I': ["█████", "  █  ", "  █  ", "  █  ", "█████"],
    'J': ["█████", "    █", "    █", "█   █", " ███ "],
    'K': ["█   █", "█  █ ", "███  ", "█  █ ", "█   █"],
    'L': ["█    ", "█    ", "█    ", "█    ", "█████"],
    'M': ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
    'N': ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
    'O': [" ███ ", "█   █", "█   █", "█   █", " ███ "],
    'P': ["████ ", "█   █", "████ ", "█    ", "█    "],
    'Q': [" ███ ", "█   █", "█ █ █", "█  █ ", " ██ █"],
    'R': ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    'S': [" ████", "█    ", " ███ ", "    █", "████ "],
    'T': ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
    'U': ["█   █", "█   █", "█   █", "█   █", " ███ "],
    'V': ["█   █", "█   █", "█   █", " █ █ ", "  █  "],
    'W': ["█   █", "█   █", "█ █ █", "██ ██", "█   █"],
    'X': ["█   █", " █ █ ", "  █  ", " █ █ ", "█   █"],
    'Y': ["█   █", " █ █ ", "  █  ", "  █  ", "  █  "],
    'Z': ["█████", "   █ ", "  █  ", " █   ", "█████"],
    '0': [" ███ ", "█  ██", "█ █ █", "██  █", " ███ "],
    '1': ["  █  ", " ██  ", "  █  ", "  █  ", " ███ "],
    '2': [" ███ ", "█   █", "  ██ ", " █   ", "█████"],
    '3': ["████ ", "    █", " ███ ", "    █", "████ "],
    '4': ["█   █", "█   █", "█████", "    █", "    █"],
    '5': ["█████", "█    ", "████ ", "    █", "████ "],
    '6': [" ███ ", "█    ", "████ ", "█   █", " ███ "],
    '7': ["█████", "    █", "   █ ", "  █  ", "  █  "],
    '8': [" ███ ", "█   █", " ███ ", "█   █", " ███ "],
    '9': [" ███ ", "█   █", " ████", "    █", " ███ "],
    ' ': ["     ", "     ", "     ", "     ", "     "],
    '!': ["  █  ", "  █  ", "  █  ", "     ", "  █  "],
    '?': [" ███ ", "█   █", "  ██ ", "     ", "  █  "],
    '.': ["     ", "     ", "     ", "     ", "  █  "],
    '-': ["     ", "     ", "█████", "     ", "     "],
    '+': ["     ", "  █  ", "█████", "  █  ", "     "],
    '*': [" █ █ ", "  █  ", "█████", "  █  ", " █ █ "],
    '#': [" █ █ ", "█████", " █ █ ", "█████", " █ █ "],
    '@': [" ███ ", "█ ██ ", "█ ██ ", "█    ", " ███ "],
}

EFFECTS = ["rainbow", "wave", "pulse", "fire", "ice", "neon", "static"]


def render_text(text, font=FONT):
    """Convert text to big ASCII lines."""
    text = text.upper()
    lines = [""] * 5
    for ch in text:
        glyph = font.get(ch, font.get(' '))
        for i in range(5):
            lines[i] += glyph[i] + " "
    return lines


def get_color(effect, x, y, t, total_w):
    if effect == "rainbow":
        hue = (x / max(1, total_w) * 6 + t) % 7
        return int(hue) + 1
    elif effect == "wave":
        val = math.sin(x * 0.2 + t * 3) * 0.5 + 0.5
        return int(val * 6) + 1
    elif effect == "pulse":
        val = (math.sin(t * 4) + 1) / 2
        return int(val * 6) + 1
    elif effect == "fire":
        heat = max(0, 1 - y / 5)
        if heat > 0.6:
            return 3  # yellow
        elif heat > 0.3:
            return 1  # red
        else:
            return 1
    elif effect == "ice":
        return 4 if (x + int(t * 5)) % 3 else 6
    elif effect == "neon":
        colors = [5, 4, 2, 3]
        return colors[int(t + x * 0.1) % len(colors)]
    else:  # static
        return 7


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

    text = "HELLO WORLD"
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])

    effect_idx = 0
    t = 0
    input_mode = False
    input_buf = ""
    last_time = time.time()
    scroll_x = 0
    auto_scroll = False

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now
        t += dt

        try:
            key = stdscr.getch()
        except:
            key = -1

        if input_mode:
            if key == 27:  # ESC
                input_mode = False
            elif key in (curses.KEY_ENTER, 10, 13):
                if input_buf:
                    text = input_buf
                input_mode = False
                input_buf = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                input_buf = input_buf[:-1]
            elif 32 <= key <= 126:
                input_buf += chr(key)
        else:
            if key in (ord('q'), ord('Q')):
                break
            elif key == ord('e') or key == ord('E'):
                effect_idx = (effect_idx + 1) % len(EFFECTS)
            elif key == ord('i') or key == ord('I'):
                input_mode = True
                input_buf = text
            elif key == ord('a') or key == ord('A'):
                auto_scroll = not auto_scroll
                scroll_x = 0

        h, w = stdscr.getmaxyx()
        lines = render_text(text)
        text_w = len(lines[0]) if lines else 0

        if auto_scroll:
            scroll_x = (scroll_x + dt * 15) % (text_w + w)

        stdscr.erase()

        # Render big text
        effect = EFFECTS[effect_idx]
        start_y = max(1, (h - 7) // 2)
        start_x = max(0, (w - text_w) // 2) - int(scroll_x) if auto_scroll else max(0, (w - text_w) // 2)

        for dy, line in enumerate(lines):
            for dx, ch in enumerate(line):
                px = start_x + dx
                py = start_y + dy
                if ch == '█' and 0 <= py < h - 2 and 0 <= px < w - 1:
                    color = get_color(effect, dx, dy, t, text_w)
                    try:
                        stdscr.addstr(py, px, "█", curses.color_pair(color) | curses.A_BOLD)
                    except curses.error:
                        pass

        # Input mode
        if input_mode:
            try:
                stdscr.addstr(h - 4, 2, "Type your text:", curses.color_pair(3))
                stdscr.addstr(h - 3, 2, f"> {input_buf}_", curses.color_pair(7))
                stdscr.addstr(h - 2, 2, "ENTER: Apply  ESC: Cancel", curses.color_pair(8))
            except curses.error:
                pass
        else:
            try:
                status = f" 🌈 {effect.upper()} | I:Input E:Effect A:Auto-scroll Q:Quit "
                stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))

                # Current text preview
                preview = f'"{text}"'
                stdscr.addstr(0, max(0, (w - len(preview)) // 2), preview, curses.color_pair(4))
            except curses.error:
                pass

        stdscr.refresh()
        time.sleep(0.03)


if __name__ == "__main__":
    curses.wrapper(main)
