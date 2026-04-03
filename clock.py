#!/usr/bin/env python3
"""⌚ Terminal Clock - Beautiful big ASCII clock with themes"""
import curses
import time
import math

# Big digit font (5 high, 6 wide)
BIG_DIGITS = {
    '0': [
        "╔═══╗",
        "║   ║",
        "║   ║",
        "║   ║",
        "╚═══╝",
    ],
    '1': [
        "  ╔══",
        "  ║  ",
        "  ║  ",
        "  ║  ",
        "  ╚══",
    ],
    '2': [
        "╔═══╗",
        "    ║",
        "╔═══╝",
        "║    ",
        "╚═══╗",
    ],
    '3': [
        "╔═══╗",
        "    ║",
        " ═══╣",
        "    ║",
        "╚═══╝",
    ],
    '4': [
        "╔   ╗",
        "║   ║",
        "╚═══╣",
        "    ║",
        "    ╝",
    ],
    '5': [
        "╔═══╗",
        "║    ",
        "╚═══╗",
        "    ║",
        "╚═══╝",
    ],
    '6': [
        "╔═══╗",
        "║    ",
        "╠═══╗",
        "║   ║",
        "╚═══╝",
    ],
    '7': [
        "╔═══╗",
        "    ║",
        "    ║",
        "   ║ ",
        "   ║ ",
    ],
    '8': [
        "╔═══╗",
        "║   ║",
        "╠═══╣",
        "║   ║",
        "╚═══╝",
    ],
    '9': [
        "╔═══╗",
        "║   ║",
        "╚═══╣",
        "    ║",
        "╚═══╝",
    ],
    ':': [
        "     ",
        "  ●  ",
        "     ",
        "  ●  ",
        "     ",
    ],
    ' ': [
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
    ],
}

THEMES = [
    {"name": "Neon Green", "digit": 2, "colon": 2, "date": 2, "border": 2},
    {"name": "Cyberpunk", "digit": 5, "colon": 4, "date": 6, "border": 5},
    {"name": "Ocean", "digit": 4, "colon": 6, "date": 4, "border": 6},
    {"name": "Fire", "digit": 1, "colon": 3, "date": 3, "border": 1},
    {"name": "Classic", "digit": 7, "colon": 7, "date": 7, "border": 3},
    {"name": "Rainbow", "digit": 0, "colon": 0, "date": 0, "border": 0},  # special
]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def draw_big_char(stdscr, y, x, char, color_pair, attr=0):
    if char not in BIG_DIGITS:
        return
    lines = BIG_DIGITS[char]
    for dy, line in enumerate(lines):
        try:
            stdscr.addstr(y + dy, x, line, curses.color_pair(color_pair) | attr)
        except curses.error:
            pass


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


def get_rainbow_color(idx, t):
    return int((idx + t * 2) % 7) + 1


def draw_analog(stdscr, cy, cx, radius, h, m, s, theme_idx):
    """Draw a small analog clock."""
    # Clock face
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        y = int(cy - math.sin(rad) * radius)
        x = int(cx + math.cos(rad) * radius * 2)
        if angle % 90 == 0:
            try:
                stdscr.addstr(y, x, "●", curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass
        else:
            try:
                stdscr.addstr(y, x, "·", curses.color_pair(8))
            except curses.error:
                pass

    # Hour hand
    h_angle = math.radians(90 - (h % 12 + m / 60) * 30)
    h_len = radius * 0.5
    for i in range(1, int(h_len * 3)):
        frac = i / (h_len * 3)
        hy = int(cy - math.sin(h_angle) * frac * h_len)
        hx = int(cx + math.cos(h_angle) * frac * h_len * 2)
        try:
            stdscr.addstr(hy, hx, "█", curses.color_pair(7) | curses.A_BOLD)
        except curses.error:
            pass

    # Minute hand
    m_angle = math.radians(90 - m * 6)
    m_len = radius * 0.75
    for i in range(1, int(m_len * 3)):
        frac = i / (m_len * 3)
        my = int(cy - math.sin(m_angle) * frac * m_len)
        mx = int(cx + math.cos(m_angle) * frac * m_len * 2)
        try:
            stdscr.addstr(my, mx, "▓", curses.color_pair(4))
        except curses.error:
            pass

    # Second hand
    s_angle = math.radians(90 - s * 6)
    s_len = radius * 0.85
    for i in range(1, int(s_len * 3)):
        frac = i / (s_len * 3)
        sy = int(cy - math.sin(s_angle) * frac * s_len)
        sx = int(cx + math.cos(s_angle) * frac * s_len * 2)
        try:
            stdscr.addstr(sy, sx, "·", curses.color_pair(1))
        except curses.error:
            pass

    # Center dot
    try:
        stdscr.addstr(cy, cx, "◉", curses.color_pair(1) | curses.A_BOLD)
    except curses.error:
        pass


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

    theme_idx = 0
    show_seconds = True
    show_analog = True
    show_date = True
    t = 0

    while True:
        h, w = stdscr.getmaxyx()
        now = time.localtime()
        t += 0.05

        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord('t') or key == ord('T'):
            theme_idx = (theme_idx + 1) % len(THEMES)
        elif key == ord('s') or key == ord('S'):
            show_seconds = not show_seconds
        elif key == ord('a') or key == ord('A'):
            show_analog = not show_analog
        elif key == ord('d') or key == ord('D'):
            show_date = not show_date

        stdscr.erase()
        theme = THEMES[theme_idx]

        # Format time
        hour_str = f"{now.tm_hour:02d}"
        min_str = f"{now.tm_min:02d}"
        sec_str = f"{now.tm_sec:02d}"

        # Calculate positions
        if show_seconds:
            time_str = f"{hour_str}:{min_str}:{sec_str}"
            char_count = 8  # HH:MM:SS
        else:
            time_str = f"{hour_str}:{min_str}"
            char_count = 5  # HH:MM

        total_width = char_count * 6
        start_x = max(0, (w - total_width) // 2)
        start_y = max(2, (h - 12) // 2)

        # Draw border
        border_color = theme["border"] if theme["border"] != 0 else get_rainbow_color(0, t)
        border_w = total_width + 6
        border_x = max(0, (w - border_w) // 2)
        try:
            stdscr.addstr(start_y - 2, border_x, "╔" + "═" * (border_w - 2) + "╗",
                         curses.color_pair(border_color))
            for dy in range(-1, 7):
                stdscr.addstr(start_y + dy, border_x, "║",
                             curses.color_pair(border_color))
                stdscr.addstr(start_y + dy, border_x + border_w - 1, "║",
                             curses.color_pair(border_color))
            stdscr.addstr(start_y + 7, border_x, "╚" + "═" * (border_w - 2) + "╝",
                         curses.color_pair(border_color))
        except curses.error:
            pass

        # Draw big time
        cx = start_x
        for i, ch in enumerate(time_str):
            if theme["digit"] == 0:  # Rainbow
                color = get_rainbow_color(i, t)
            elif ch == ':':
                color = theme["colon"]
                # Blink colon
                if now.tm_sec % 2 == 0:
                    ch = ' '
            else:
                color = theme["digit"]

            draw_big_char(stdscr, start_y, cx, ch, color, curses.A_BOLD)
            cx += 6

        # Date
        if show_date:
            date_y = start_y + 8
            weekday = WEEKDAYS[now.tm_wday]
            month = MONTHS[now.tm_mon - 1]
            date_str = f"{weekday}, {month} {now.tm_mday}, {now.tm_year}"

            date_color = theme["date"] if theme["date"] != 0 else get_rainbow_color(5, t)
            draw_centered(stdscr, date_y, date_str, curses.color_pair(date_color))

        # Analog clock
        if show_analog and h > 25:
            analog_y = start_y + 14
            radius = min(5, (h - analog_y - 3) // 2)
            if radius >= 3:
                draw_analog(stdscr, analog_y + radius, w // 2, radius,
                           now.tm_hour, now.tm_min, now.tm_sec, theme_idx)

        # Theme name and controls
        theme_name = THEMES[theme_idx]["name"]
        try:
            controls = f" {theme_name} | T:Theme S:Seconds A:Analog D:Date Q:Quit "
            stdscr.addstr(h - 1, max(0, (w - len(controls)) // 2), controls, curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.1)


if __name__ == "__main__":
    curses.wrapper(main)
