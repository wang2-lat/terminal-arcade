#!/usr/bin/env python3
"""🧬 Terminal DNA Helix - Rotating double helix animation"""
import curses
import math
import time
import random

BASE_PAIRS = [('A', 'T'), ('T', 'A'), ('G', 'C'), ('C', 'G')]
BASE_COLORS = {'A': 1, 'T': 2, 'G': 3, 'C': 4}

HELIX_CHARS = {
    "sugar": "○",
    "phosphate": "─",
    "bond_h": "═",
    "bond_v": "║",
    "backbone": "●",
}


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)      # A - Adenine
    curses.init_pair(2, curses.COLOR_GREEN, -1)     # T - Thymine
    curses.init_pair(3, curses.COLOR_YELLOW, -1)    # G - Guanine
    curses.init_pair(4, curses.COLOR_CYAN, -1)      # C - Cytosine
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
    helix_radius = 15
    show_labels = True
    show_bonds = True
    mode = 0  # 0=vertical, 1=horizontal
    last_time = time.time()

    # Generate sequence
    sequence = [random.choice(BASE_PAIRS) for _ in range(100)]

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
        elif key == ord('l') or key == ord('L'):
            show_labels = not show_labels
        elif key == ord('b') or key == ord('B'):
            show_bonds = not show_bonds
        elif key == ord('m') or key == ord('M'):
            mode = (mode + 1) % 2
        elif key == ord('r') or key == ord('R'):
            helix_radius = max(5, min(30, helix_radius + (3 if key == ord('r') else -3)))

        h, w = stdscr.getmaxyx()
        cx, cy = w // 2, h // 2

        stdscr.erase()

        # Title
        title = "🧬 DNA Double Helix 🧬"
        try:
            stdscr.addstr(0, max(0, (w - len(title)) // 2), title, curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

        if mode == 0:  # Vertical helix
            num_steps = h - 4
            for i in range(num_steps):
                y = 2 + i
                angle = t * 2 + i * 0.25
                pair_idx = (i + int(t * 5)) % len(sequence)
                base_l, base_r = sequence[pair_idx]

                # Calculate helix positions
                x1 = cx + int(math.cos(angle) * helix_radius)
                x2 = cx + int(math.cos(angle + math.pi) * helix_radius)

                # Depth (z) for shading
                z1 = math.sin(angle)
                z2 = math.sin(angle + math.pi)

                # Draw backbone strands
                if 0 <= y < h and 0 <= x1 < w:
                    attr1 = curses.A_BOLD if z1 > 0 else curses.A_DIM
                    try:
                        stdscr.addstr(y, x1, "●", curses.color_pair(5) | attr1)
                    except curses.error:
                        pass

                if 0 <= y < h and 0 <= x2 < w:
                    attr2 = curses.A_BOLD if z2 > 0 else curses.A_DIM
                    try:
                        stdscr.addstr(y, x2, "●", curses.color_pair(6) | attr2)
                    except curses.error:
                        pass

                # Draw base pairs (hydrogen bonds)
                if show_bonds and abs(z1) < 0.3:  # Only when strands are at similar depth
                    lx, rx = min(x1, x2) + 1, max(x1, x2)
                    mid = (lx + rx) // 2

                    if rx - lx > 2 and 0 <= y < h:
                        # Draw bond line
                        for bx in range(lx, rx):
                            if 0 <= bx < w:
                                try:
                                    if bx == lx:
                                        stdscr.addstr(y, bx, base_l,
                                                     curses.color_pair(BASE_COLORS[base_l]) | curses.A_BOLD)
                                    elif bx == rx - 1:
                                        stdscr.addstr(y, bx, base_r,
                                                     curses.color_pair(BASE_COLORS[base_r]) | curses.A_BOLD)
                                    elif bx == mid:
                                        stdscr.addstr(y, bx, "═", curses.color_pair(8))
                                    else:
                                        stdscr.addstr(y, bx, "─", curses.color_pair(8) | curses.A_DIM)
                                except curses.error:
                                    pass

                # Labels
                if show_labels and abs(z1) < 0.2 and i % 4 == 0:
                    label = f"{base_l}─{base_r}"
                    label_x = max(0, min(w - len(label), mid - 1))
                    # Don't overlap with bonds
                    try:
                        if x1 < cx:
                            stdscr.addstr(y, max(0, min(x1, x2) - 5), f"{base_l}━{base_r}",
                                         curses.color_pair(7) | curses.A_DIM)
                    except curses.error:
                        pass

        else:  # Horizontal mode
            num_steps = w - 4
            for i in range(num_steps):
                x = 2 + i
                angle = t * 2 + i * 0.15
                pair_idx = (i + int(t * 5)) % len(sequence)
                base_l, base_r = sequence[pair_idx]

                y1 = cy + int(math.cos(angle) * min(helix_radius, h // 3))
                y2 = cy + int(math.cos(angle + math.pi) * min(helix_radius, h // 3))

                z1 = math.sin(angle)
                z2 = math.sin(angle + math.pi)

                if 0 <= y1 < h and 0 <= x < w:
                    attr1 = curses.A_BOLD if z1 > 0 else curses.A_DIM
                    try:
                        stdscr.addstr(y1, x, "●", curses.color_pair(5) | attr1)
                    except curses.error:
                        pass

                if 0 <= y2 < h and 0 <= x < w:
                    attr2 = curses.A_BOLD if z2 > 0 else curses.A_DIM
                    try:
                        stdscr.addstr(y2, x, "●", curses.color_pair(6) | attr2)
                    except curses.error:
                        pass

                # Vertical bonds
                if show_bonds and abs(z1) < 0.3:
                    ly, ry = min(y1, y2) + 1, max(y1, y2)
                    if ry - ly > 1:
                        for by in range(ly, ry):
                            if 0 <= by < h and 0 <= x < w:
                                try:
                                    if by == ly:
                                        stdscr.addstr(by, x, base_l[:1],
                                                     curses.color_pair(BASE_COLORS[base_l]))
                                    elif by == ry - 1:
                                        stdscr.addstr(by, x, base_r[:1],
                                                     curses.color_pair(BASE_COLORS[base_r]))
                                    else:
                                        stdscr.addstr(by, x, "│", curses.color_pair(8) | curses.A_DIM)
                                except curses.error:
                                    pass

        # Legend
        legend_y = h - 3
        try:
            stdscr.addstr(legend_y, 2, "A", curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(legend_y, 3, "=Adenine ", curses.color_pair(8))
            stdscr.addstr(legend_y, 12, "T", curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(legend_y, 13, "=Thymine ", curses.color_pair(8))
            stdscr.addstr(legend_y, 22, "G", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(legend_y, 23, "=Guanine ", curses.color_pair(8))
            stdscr.addstr(legend_y, 32, "C", curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(legend_y, 33, "=Cytosine", curses.color_pair(8))
        except curses.error:
            pass

        # Controls
        try:
            status = f" Speed:{speed:.1f}x | M:Mode L:Labels B:Bonds +/-:Speed Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.04)


if __name__ == "__main__":
    curses.wrapper(main)
