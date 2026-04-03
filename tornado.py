#!/usr/bin/env python3
"""🌪️ Terminal Tornado - Swirling ASCII particle vortex"""
import curses
import math
import time
import random


class Debris:
    __slots__ = ['angle', 'radius', 'y', 'speed', 'char', 'color', 'drift']

    def __init__(self, h):
        self.angle = random.uniform(0, math.pi * 2)
        self.radius = random.uniform(1, 8)
        self.y = h + random.uniform(0, 10)
        self.speed = random.uniform(0.3, 1.2)
        self.char = random.choice(['·', '•', '*', '~', '░', '▒', '▓', '█', '◦', '○'])
        self.color = random.choice([3, 7, 8, 3, 3])
        self.drift = random.uniform(-0.5, 0.5)


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
    debris = [Debris(h) for _ in range(300)]
    # Place them initially
    for d in debris:
        d.y = random.uniform(0, h)

    t = 0
    tornado_x = w / 2
    tornado_sway = 0
    intensity = 1.0
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
        elif key == ord('+') or key == ord('='):
            intensity = min(3.0, intensity + 0.2)
        elif key == ord('-'):
            intensity = max(0.3, intensity - 0.2)

        h, w = stdscr.getmaxyx()
        cx = w / 2

        # Tornado sways
        tornado_sway = math.sin(t * 0.5) * w * 0.15
        tornado_cx = cx + tornado_sway

        stdscr.erase()

        # Ground
        for x in range(w - 1):
            try:
                stdscr.addstr(h - 2, x, "▓", curses.color_pair(3) | curses.A_DIM)
            except curses.error:
                pass

        # Update and draw debris
        for d in debris:
            # Rise upward
            d.y -= d.speed * intensity * dt * 20
            # Spin around center
            d.angle += (3.0 / max(0.5, d.radius)) * intensity * dt
            # Funnel shape: wider at bottom
            height_ratio = max(0, d.y / h)
            funnel_width = 2 + height_ratio * 15 * intensity
            actual_radius = d.radius * funnel_width / 8

            # Calculate screen position
            px = tornado_cx + math.cos(d.angle) * actual_radius * 2 + d.drift
            py = d.y

            # Recycle if off top
            if py < -5:
                d.y = h - 1 + random.uniform(0, 5)
                d.angle = random.uniform(0, math.pi * 2)
                d.radius = random.uniform(1, 8)

            ix, iy = int(px), int(py)
            if 0 <= iy < h - 2 and 0 <= ix < w - 1:
                # Depth-based rendering
                z = math.sin(d.angle)
                if z > 0:
                    attr = curses.A_BOLD
                    ch = d.char
                else:
                    attr = curses.A_DIM
                    ch = '·'

                try:
                    stdscr.addstr(iy, ix, ch, curses.color_pair(d.color) | attr)
                except curses.error:
                    pass

        # Funnel core (darker center)
        for y in range(0, h - 2):
            height_ratio = y / h
            core_w = int(1 + height_ratio * 3 * intensity)
            core_x = int(tornado_cx)
            for dx in range(-core_w, core_w + 1):
                px = core_x + dx
                if 0 <= y < h - 2 and 0 <= px < w - 1:
                    try:
                        ch = '█' if abs(dx) < core_w // 2 else '▓'
                        stdscr.addstr(y, px, ch, curses.color_pair(8) | curses.A_DIM)
                    except curses.error:
                        pass

        # Cloud top
        cloud_y = max(0, 1)
        cloud_w = int(20 * intensity)
        cloud_cx = int(tornado_cx)
        for dx in range(-cloud_w, cloud_w + 1):
            px = cloud_cx + dx
            if 0 <= px < w - 1:
                dist = abs(dx) / max(1, cloud_w)
                if dist < 0.7:
                    ch = '█'
                elif dist < 0.9:
                    ch = '▓'
                else:
                    ch = '░'
                try:
                    stdscr.addstr(cloud_y, px, ch, curses.color_pair(8))
                    if cloud_y + 1 < h:
                        stdscr.addstr(cloud_y + 1, px, '▒' if dist < 0.5 else ' ',
                                     curses.color_pair(8) | curses.A_DIM)
                except curses.error:
                    pass

        try:
            status = f" 🌪️ Tornado | Intensity: {intensity:.1f}x | +/-:Power Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.03)


if __name__ == "__main__":
    curses.wrapper(main)
