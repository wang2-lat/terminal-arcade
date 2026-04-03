#!/usr/bin/env python3
"""🧲 Terminal Magnetic Field Visualizer - See field lines in real time"""
import curses
import math
import time
import random


class Pole:
    def __init__(self, x, y, strength, polarity):
        self.x = x
        self.y = y
        self.strength = strength
        self.polarity = polarity  # +1 = north, -1 = south


FIELD_CHARS = " ·∙•→←↑↓↗↘↙↖◦○●"


def field_at(poles, x, y):
    """Calculate magnetic field vector at point."""
    bx, by = 0, 0
    for pole in poles:
        dx = x - pole.x
        dy = (y - pole.y) * 2  # aspect ratio correction
        dist_sq = dx * dx + dy * dy + 0.1
        dist = math.sqrt(dist_sq)
        # Magnetic field from monopole: B = k * q / r^2, direction = r_hat
        magnitude = pole.strength * pole.polarity / dist_sq
        bx += magnitude * dx / dist
        by += magnitude * dy / dist * 0.5
    return bx, by


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
    poles = [
        Pole(w // 3, h // 2, 50, 1),      # North
        Pole(2 * w // 3, h // 2, 50, -1),  # South
    ]

    cursor_x, cursor_y = w // 2, h // 2
    show_vectors = True
    show_lines = True
    mode = 0  # 0=dipole, 1=quad, 2=custom

    presets = {
        0: lambda: [Pole(w//3, h//2, 50, 1), Pole(2*w//3, h//2, 50, -1)],
        1: lambda: [Pole(w//3, h//3, 50, 1), Pole(2*w//3, h//3, 50, -1),
                    Pole(w//3, 2*h//3, 50, -1), Pole(2*w//3, 2*h//3, 50, 1)],
    }

    while True:
        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == curses.KEY_UP:
            cursor_y = max(1, cursor_y - 1)
        elif key == curses.KEY_DOWN:
            cursor_y = min(h - 3, cursor_y + 1)
        elif key == curses.KEY_LEFT:
            cursor_x = max(1, cursor_x - 1)
        elif key == curses.KEY_RIGHT:
            cursor_x = min(w - 2, cursor_x + 1)
        elif key == ord('n') or key == ord('N'):
            poles.append(Pole(cursor_x, cursor_y, 50, 1))
        elif key == ord('s') or key == ord('S'):
            poles.append(Pole(cursor_x, cursor_y, 50, -1))
        elif key == ord('c') or key == ord('C'):
            poles.clear()
        elif key == ord('1'):
            poles = presets[0]()
        elif key == ord('2'):
            poles = presets[1]()
        elif key == ord('v') or key == ord('V'):
            show_vectors = not show_vectors
        elif key == ord('l') or key == ord('L'):
            show_lines = not show_lines
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            # Remove nearest pole
            if poles:
                nearest = min(poles, key=lambda p: (p.x-cursor_x)**2 + (p.y-cursor_y)**2)
                poles.remove(nearest)

        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Draw field
        step = 2
        for sy in range(1, h - 2, step):
            for sx in range(0, w - 1, step * 2):
                bx, by = field_at(poles, sx, sy)
                magnitude = math.sqrt(bx * bx + by * by)

                if magnitude < 0.01:
                    continue

                # Direction to arrow
                angle = math.atan2(by, bx)
                if show_vectors:
                    if -0.39 <= angle < 0.39:
                        ch = "→"
                    elif 0.39 <= angle < 1.18:
                        ch = "↘"
                    elif 1.18 <= angle < 1.96:
                        ch = "↓"
                    elif 1.96 <= angle < 2.75:
                        ch = "↙"
                    elif angle >= 2.75 or angle < -2.75:
                        ch = "←"
                    elif -2.75 <= angle < -1.96:
                        ch = "↖"
                    elif -1.96 <= angle < -1.18:
                        ch = "↑"
                    else:
                        ch = "↗"
                else:
                    idx = min(len(FIELD_CHARS) - 1, int(magnitude * 2))
                    ch = FIELD_CHARS[idx]

                # Color by strength
                if magnitude > 5:
                    color = 1  # red (strong)
                elif magnitude > 2:
                    color = 3  # yellow
                elif magnitude > 0.5:
                    color = 2  # green
                else:
                    color = 4  # cyan (weak)

                attr = curses.A_BOLD if magnitude > 3 else 0

                try:
                    stdscr.addstr(sy, sx, ch, curses.color_pair(color) | attr)
                except curses.error:
                    pass

        # Draw field lines (trace from near poles)
        if show_lines and poles:
            for pole in poles:
                if pole.polarity > 0:  # Only trace from north poles
                    for angle_deg in range(0, 360, 20):
                        angle = math.radians(angle_deg)
                        lx = pole.x + math.cos(angle) * 3
                        ly = pole.y + math.sin(angle) * 1.5

                        for step_i in range(80):
                            bx, by = field_at(poles, lx, ly)
                            mag = math.sqrt(bx * bx + by * by)
                            if mag < 0.01:
                                break
                            lx += bx / mag * 1.5
                            ly += by / mag * 0.75

                            ix, iy = int(lx), int(ly)
                            if not (0 <= iy < h - 1 and 0 <= ix < w - 1):
                                break

                            # Check if reached south pole
                            for p in poles:
                                if p.polarity < 0 and abs(lx - p.x) < 2 and abs(ly - p.y) < 2:
                                    break

                            try:
                                stdscr.addstr(iy, ix, "·", curses.color_pair(6) | curses.A_DIM)
                            except curses.error:
                                pass

        # Draw poles
        for pole in poles:
            ix, iy = int(pole.x), int(pole.y)
            if 0 <= iy < h - 1 and 0 <= ix < w - 1:
                ch = "N" if pole.polarity > 0 else "S"
                color = 1 if pole.polarity > 0 else 6
                try:
                    stdscr.addstr(iy, ix, ch, curses.color_pair(color) | curses.A_BOLD | curses.A_REVERSE)
                except curses.error:
                    pass

        # Cursor
        try:
            stdscr.addstr(cursor_y, cursor_x, "+", curses.color_pair(7) | curses.A_BLINK)
        except curses.error:
            pass

        # Status
        try:
            status = f" 🧲 Poles: {len(poles)} | N:Add North S:Add South DEL:Remove 1:Dipole 2:Quad C:Clear V:Vectors Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.05)


if __name__ == "__main__":
    curses.wrapper(main)
