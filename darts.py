#!/usr/bin/env python3
"""🎯 Terminal Darts - Aim and throw at the dartboard!"""
import curses
import math
import time
import random


def draw_dartboard(stdscr, cy, cx, radius, h, w):
    """Draw a dartboard with scoring rings."""
    sections = [20,1,18,4,13,6,10,15,2,17,3,19,7,16,8,11,14,9,12,5]

    for y in range(max(0, cy - radius - 1), min(h - 1, cy + radius + 2)):
        for x in range(max(0, cx - radius * 2 - 2), min(w - 1, cx + radius * 2 + 3)):
            dx = (x - cx) / 2  # aspect ratio
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > radius:
                continue

            angle = math.atan2(dy, dx)
            section_idx = int(((angle + math.pi) / (2 * math.pi) * 20 + 10.5) % 20)
            section_num = sections[section_idx]

            # Determine ring
            r_ratio = dist / radius
            if r_ratio < 0.04:
                ch, color = "◉", 1  # Double bull (50)
            elif r_ratio < 0.1:
                ch, color = "●", 2  # Single bull (25)
            elif r_ratio < 0.55:
                ch, color = "░" if section_idx % 2 else "▒", 7 if section_idx % 2 else 8
            elif r_ratio < 0.62:
                ch, color = "█", 1 if section_idx % 2 else 2  # Triple ring
            elif r_ratio < 0.88:
                ch, color = "░" if section_idx % 2 else "▒", 7 if section_idx % 2 else 8
            elif r_ratio < 0.95:
                ch, color = "█", 1 if section_idx % 2 else 2  # Double ring
            else:
                ch, color = "·", 8

            try:
                stdscr.addstr(y, x, ch, curses.color_pair(color))
            except curses.error:
                pass

    # Section numbers around the edge
    for i, num in enumerate(sections):
        angle = (i / 20) * 2 * math.pi - math.pi / 2
        nx = int(cx + math.cos(angle) * (radius + 1) * 2)
        ny = int(cy + math.sin(angle) * (radius + 1))
        if 0 <= ny < h and 0 <= nx < w - 2:
            try:
                stdscr.addstr(ny, nx, f"{num:>2}", curses.color_pair(3))
            except curses.error:
                pass


def calculate_score(cx, cy, hit_x, hit_y, radius):
    """Calculate dart score based on where it landed."""
    sections = [20,1,18,4,13,6,10,15,2,17,3,19,7,16,8,11,14,9,12,5]
    dx = (hit_x - cx) / 2
    dy = hit_y - cy
    dist = math.sqrt(dx * dx + dy * dy)

    if dist > radius:
        return 0, "Miss!"

    r_ratio = dist / radius
    angle = math.atan2(dy, dx)
    section_idx = int(((angle + math.pi) / (2 * math.pi) * 20 + 10.5) % 20)
    section_num = sections[section_idx]

    if r_ratio < 0.04:
        return 50, "BULLSEYE! 50"
    elif r_ratio < 0.1:
        return 25, f"Bull! 25"
    elif r_ratio < 0.55:
        return section_num, f"Single {section_num}"
    elif r_ratio < 0.62:
        return section_num * 3, f"TRIPLE {section_num}! ({section_num*3})"
    elif r_ratio < 0.88:
        return section_num, f"Single {section_num}"
    elif r_ratio < 0.95:
        return section_num * 2, f"Double {section_num} ({section_num*2})"
    else:
        return section_num, f"Outer {section_num}"


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
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

    h, w = stdscr.getmaxyx()
    board_cx, board_cy = w // 2, h // 2
    radius = min(h // 2 - 3, w // 4 - 2)

    # Crosshair
    aim_x, aim_y = float(board_cx), float(board_cy)
    aim_vx, aim_vy = 0.4, 0.3  # Wobbly aim
    wobble_phase = 0

    score_total = 0
    darts_thrown = 0
    darts_left = 3
    round_num = 1
    dart_hits = []  # List of (x, y) for placed darts
    message = ""
    last_score_text = ""
    game_mode = "501"  # 501 countdown
    target_score = 501
    last_time = time.time()

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now
        wobble_phase += dt * 3

        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord(' '):
            # Throw dart!
            hit_x = int(aim_x + random.gauss(0, 1.5))
            hit_y = int(aim_y + random.gauss(0, 0.8))
            pts, desc = calculate_score(board_cx, board_cy, hit_x, hit_y, radius)
            dart_hits.append((hit_x, hit_y))
            darts_thrown += 1
            darts_left -= 1

            if game_mode == "501":
                if target_score - pts >= 0:
                    target_score -= pts
                    score_total += pts
                    last_score_text = desc
                else:
                    last_score_text = "BUST! (over target)"
            else:
                score_total += pts
                last_score_text = desc

            if darts_left <= 0:
                darts_left = 3
                round_num += 1
                dart_hits.clear()

            if target_score == 0:
                message = f"🎉 FINISHED in {round_num} rounds! 🎉"
        elif key in (ord('r'), ord('R')):
            score_total = 0
            target_score = 501
            darts_thrown = 0
            darts_left = 3
            round_num = 1
            dart_hits.clear()
            last_score_text = ""
            message = ""

        h, w = stdscr.getmaxyx()

        # Wobble the aim
        wobble_amp = max(0.5, 3.0 - darts_thrown * 0.05)  # Gets steadier with practice
        aim_x = board_cx + math.sin(wobble_phase * 1.3) * wobble_amp * 4
        aim_y = board_cy + math.cos(wobble_phase * 0.9) * wobble_amp * 2

        # Draw
        stdscr.erase()

        # Title
        draw_centered(stdscr, 0, f"🎯 DARTS 501 | Round {round_num} | Remaining: {target_score}",
                     curses.color_pair(3) | curses.A_BOLD)

        # Dartboard
        draw_dartboard(stdscr, board_cy, board_cx, radius, h, w)

        # Previous dart hits
        for hx, hy in dart_hits:
            if 0 <= hy < h and 0 <= hx < w:
                try:
                    stdscr.addstr(hy, hx, "✦", curses.color_pair(5) | curses.A_BOLD)
                except curses.error:
                    pass

        # Crosshair
        ax, ay = int(aim_x), int(aim_y)
        for dx, dy, ch in [(-2,0,"─"),(-1,0,"─"),(1,0,"─"),(2,0,"─"),(0,-1,"│"),(0,1,"│"),(0,0,"+")]:
            px, py = ax + dx, ay + dy
            if 0 <= py < h and 0 <= px < w:
                try:
                    stdscr.addstr(py, px, ch, curses.color_pair(4) | curses.A_BOLD)
                except curses.error:
                    pass

        # HUD
        try:
            hud_x = 2
            stdscr.addstr(1, hud_x, f"Score: {score_total}", curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(2, hud_x, f"Darts: {'⬥ ' * darts_left}{'⬦ ' * (3 - darts_left)}",
                         curses.color_pair(4))
            if last_score_text:
                stdscr.addstr(3, hud_x, last_score_text, curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

        if message:
            draw_centered(stdscr, h - 3, message, curses.color_pair(2) | curses.A_BOLD)

        try:
            stdscr.addstr(h - 1, 0, " SPACE:Throw  R:Reset  Q:Quit ", curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.03)


if __name__ == "__main__":
    curses.wrapper(main)
