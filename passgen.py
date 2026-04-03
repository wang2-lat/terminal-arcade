#!/usr/bin/env python3
"""🔑 Terminal Password Generator - Secure passwords with strength meter"""
import curses
import random
import string
import math
import time


def generate_password(length=16, upper=True, lower=True, digits=True, symbols=True):
    chars = ""
    required = []
    if upper:
        chars += string.ascii_uppercase
        required.append(random.choice(string.ascii_uppercase))
    if lower:
        chars += string.ascii_lowercase
        required.append(random.choice(string.ascii_lowercase))
    if digits:
        chars += string.digits
        required.append(random.choice(string.digits))
    if symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        required.append(random.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))

    if not chars:
        chars = string.ascii_letters
    remaining = length - len(required)
    password = required + [random.choice(chars) for _ in range(max(0, remaining))]
    random.shuffle(password)
    return ''.join(password[:length])


def password_strength(pwd):
    score = 0
    length = len(pwd)
    score += min(25, length * 2)
    if any(c.isupper() for c in pwd): score += 15
    if any(c.islower() for c in pwd): score += 15
    if any(c.isdigit() for c in pwd): score += 15
    if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in pwd): score += 15
    unique = len(set(pwd))
    score += min(15, unique * 2)
    return min(100, score)


def entropy(pwd):
    pool = 0
    if any(c.isupper() for c in pwd): pool += 26
    if any(c.islower() for c in pwd): pool += 26
    if any(c.isdigit() for c in pwd): pool += 10
    if any(c in string.punctuation for c in pwd): pool += 32
    if pool == 0: pool = 26
    return len(pwd) * math.log2(pool)


def strength_label(score):
    if score >= 90: return ("EXCELLENT", 2)
    elif score >= 70: return ("STRONG", 2)
    elif score >= 50: return ("MODERATE", 3)
    elif score >= 30: return ("WEAK", 1)
    else: return ("VERY WEAK", 1)


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


def draw_strength_bar(stdscr, y, x, width, score):
    filled = int(width * score / 100)
    label, color = strength_label(score)
    try:
        stdscr.addstr(y, x, "█" * filled, curses.color_pair(color) | curses.A_BOLD)
        stdscr.addstr(y, x + filled, "░" * (width - filled), curses.color_pair(8))
        stdscr.addstr(y, x + width + 2, f"{score}% {label}", curses.color_pair(color) | curses.A_BOLD)
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

    stdscr.keypad(True)

    length = 16
    use_upper = True
    use_lower = True
    use_digits = True
    use_symbols = True
    history = []
    password = generate_password(length, use_upper, use_lower, use_digits, use_symbols)
    history.append(password)

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        # Title
        draw_centered(stdscr, 1, "╔═══════════════════════════════════╗", curses.color_pair(3))
        draw_centered(stdscr, 2, "║    🔑 PASSWORD GENERATOR 🔑      ║", curses.color_pair(3) | curses.A_BOLD)
        draw_centered(stdscr, 3, "╚═══════════════════════════════════╝", curses.color_pair(3))

        # Current password
        draw_centered(stdscr, 6, "Generated Password:", curses.color_pair(4))
        draw_centered(stdscr, 8, f"  {password}  ", curses.color_pair(7) | curses.A_BOLD)

        # Strength meter
        score = password_strength(password)
        ent = entropy(password)
        bar_x = max(5, (w - 50) // 2)
        draw_centered(stdscr, 10, "Strength:", curses.color_pair(4))
        draw_strength_bar(stdscr, 11, bar_x, 30, score)
        draw_centered(stdscr, 12, f"Entropy: {ent:.1f} bits", curses.color_pair(8))

        # Crack time estimate
        guesses_per_sec = 1e10  # 10 billion
        total_combos = 2 ** ent
        seconds = total_combos / guesses_per_sec
        if seconds < 60:
            crack_time = f"{seconds:.0f} seconds"
        elif seconds < 3600:
            crack_time = f"{seconds/60:.0f} minutes"
        elif seconds < 86400:
            crack_time = f"{seconds/3600:.0f} hours"
        elif seconds < 86400 * 365:
            crack_time = f"{seconds/86400:.0f} days"
        elif seconds < 86400 * 365 * 1000:
            crack_time = f"{seconds/86400/365:.0f} years"
        else:
            crack_time = f"{seconds/86400/365:.0e} years"
        draw_centered(stdscr, 13, f"Time to crack (10B/s): {crack_time}", curses.color_pair(8))

        # Settings
        settings_y = 16
        draw_centered(stdscr, settings_y, "═══ Settings ═══", curses.color_pair(3))
        opts = [
            (f"Length: {length}", "←/→"),
            (f"Uppercase (A-Z): {'ON' if use_upper else 'OFF'}", "U"),
            (f"Lowercase (a-z): {'ON' if use_lower else 'OFF'}", "L"),
            (f"Digits (0-9): {'ON' if use_digits else 'OFF'}", "D"),
            (f"Symbols (!@#): {'ON' if use_symbols else 'OFF'}", "S"),
        ]
        for i, (text, key) in enumerate(opts):
            try:
                active = [use_upper, use_lower, use_digits, use_symbols]
                color = curses.color_pair(2) if i == 0 or active[i-1] else curses.color_pair(1)
                stdscr.addstr(settings_y + 1 + i, max(5, (w-45)//2), f"  [{key}] {text}", color)
            except curses.error:
                pass

        # History
        if len(history) > 1:
            hist_y = settings_y + 7
            draw_centered(stdscr, hist_y, "─── Recent ───", curses.color_pair(8))
            for i, pwd in enumerate(history[-5:-1]):
                try:
                    stdscr.addstr(hist_y + 1 + i, max(5, (w-40)//2), pwd, curses.color_pair(8) | curses.A_DIM)
                except curses.error:
                    pass

        # Controls
        draw_centered(stdscr, h - 2, "SPACE/G: Generate  ←/→: Length  U/L/D/S: Toggle  Q: Quit",
                     curses.color_pair(8))

        stdscr.refresh()
        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord(' '), ord('g'), ord('G')):
            password = generate_password(length, use_upper, use_lower, use_digits, use_symbols)
            history.append(password)
            if len(history) > 20:
                history.pop(0)
        elif key == curses.KEY_LEFT:
            length = max(4, length - 1)
            password = generate_password(length, use_upper, use_lower, use_digits, use_symbols)
        elif key == curses.KEY_RIGHT:
            length = min(64, length + 1)
            password = generate_password(length, use_upper, use_lower, use_digits, use_symbols)
        elif key in (ord('u'), ord('U')):
            use_upper = not use_upper
        elif key in (ord('l'), ord('L')):
            use_lower = not use_lower
        elif key in (ord('d'), ord('D')):
            use_digits = not use_digits
        elif key in (ord('s'), ord('S')):
            use_symbols = not use_symbols


if __name__ == "__main__":
    curses.wrapper(main)
