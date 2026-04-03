#!/usr/bin/env python3
"""🌊 ASCII Fluid Simulation - Mesmerizing terminal fluid dynamics"""
import curses
import math
import time
import random


class FluidSim:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.density = [[0.0] * w for _ in range(h)]
        self.vx = [[0.0] * w for _ in range(h)]
        self.vy = [[0.0] * w for _ in range(h)]
        self.density_prev = [[0.0] * w for _ in range(h)]
        self.vx_prev = [[0.0] * w for _ in range(h)]
        self.vy_prev = [[0.0] * w for _ in range(h)]
        self.dt = 0.1
        self.diff = 0.0001
        self.visc = 0.0

    def add_density(self, y, x, amount):
        if 0 <= y < self.h and 0 <= x < self.w:
            self.density[y][x] += amount

    def add_velocity(self, y, x, vy, vx):
        if 0 <= y < self.h and 0 <= x < self.w:
            self.vy[y][x] += vy
            self.vx[y][x] += vx

    def diffuse(self, grid, prev, diff):
        a = self.dt * diff * (self.h - 2) * (self.w - 2)
        for _ in range(4):
            for y in range(1, self.h - 1):
                for x in range(1, self.w - 1):
                    grid[y][x] = (prev[y][x] + a * (
                        grid[y-1][x] + grid[y+1][x] +
                        grid[y][x-1] + grid[y][x+1]
                    )) / (1 + 4 * a)

    def advect(self, grid, prev, vy, vx):
        dt0_h = self.dt * (self.h - 2)
        dt0_w = self.dt * (self.w - 2)
        for y in range(1, self.h - 1):
            for x in range(1, self.w - 1):
                yy = y - dt0_h * vy[y][x]
                xx = x - dt0_w * vx[y][x]
                yy = max(0.5, min(self.h - 1.5, yy))
                xx = max(0.5, min(self.w - 1.5, xx))
                y0, x0 = int(yy), int(xx)
                y1, x1 = y0 + 1, x0 + 1
                sy, sx = yy - y0, xx - x0
                if y1 < self.h and x1 < self.w:
                    grid[y][x] = (
                        (1 - sy) * ((1 - sx) * prev[y0][x0] + sx * prev[y0][x1]) +
                        sy * ((1 - sx) * prev[y1][x0] + sx * prev[y1][x1])
                    )

    def project(self):
        div = [[0.0] * self.w for _ in range(self.h)]
        p = [[0.0] * self.w for _ in range(self.h)]
        h_inv = 1.0 / max(1, self.h - 2)

        for y in range(1, self.h - 1):
            for x in range(1, self.w - 1):
                div[y][x] = -0.5 * h_inv * (
                    self.vx[y][x+1] - self.vx[y][x-1] +
                    self.vy[y+1][x] - self.vy[y-1][x]
                )

        for _ in range(4):
            for y in range(1, self.h - 1):
                for x in range(1, self.w - 1):
                    p[y][x] = (div[y][x] +
                        p[y-1][x] + p[y+1][x] +
                        p[y][x-1] + p[y][x+1]) / 4

        for y in range(1, self.h - 1):
            for x in range(1, self.w - 1):
                self.vx[y][x] -= 0.5 * (p[y][x+1] - p[y][x-1]) * (self.w - 2)
                self.vy[y][x] -= 0.5 * (p[y+1][x] - p[y-1][x]) * (self.h - 2)

    def step(self):
        # Swap and process velocity
        self.vx, self.vx_prev = self.vx_prev, self.vx
        self.vy, self.vy_prev = self.vy_prev, self.vy
        self.diffuse(self.vx, self.vx_prev, self.visc)
        self.diffuse(self.vy, self.vy_prev, self.visc)
        self.project()
        self.vx, self.vx_prev = self.vx_prev, self.vx
        self.vy, self.vy_prev = self.vy_prev, self.vy
        self.advect(self.vx, self.vx_prev, self.vy_prev, self.vx_prev)
        self.advect(self.vy, self.vy_prev, self.vy_prev, self.vx_prev)
        self.project()

        # Swap and process density
        self.density, self.density_prev = self.density_prev, self.density
        self.diffuse(self.density, self.density_prev, self.diff)
        self.density, self.density_prev = self.density_prev, self.density
        self.advect(self.density, self.density_prev, self.vy, self.vx)

        # Decay
        for y in range(self.h):
            for x in range(self.w):
                self.density[y][x] *= 0.99


CHARS_WATER = " ·∙•◦○◎●◉█"
CHARS_SMOKE = " .:-=+*#%@█"
CHARS_BLOCK = " ░▒▓█"


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_BLUE, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    sim_h = h - 2
    sim_w = w - 1

    # Use smaller sim for performance
    scale = 2
    fluid = FluidSim(sim_h // scale + 2, sim_w // scale + 2)

    mode = 0  # 0=water, 1=fire, 2=smoke, 3=rainbow
    mode_names = ["WATER 🌊", "FIRE 🔥", "SMOKE 💨", "RAINBOW 🌈"]
    char_sets = [CHARS_WATER, CHARS_SMOKE, CHARS_SMOKE, CHARS_BLOCK]

    t = 0
    auto_source = True
    paused = False

    while True:
        t += 0.05

        # Input
        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord(' '):
            paused = not paused
        elif key == ord('m') or key == ord('M'):
            mode = (mode + 1) % len(mode_names)
        elif key == ord('a') or key == ord('A'):
            auto_source = not auto_source
        elif key == ord('r') or key == ord('R'):
            fluid = FluidSim(sim_h // scale + 2, sim_w // scale + 2)

        if paused:
            time.sleep(0.05)
            continue

        fh, fw = fluid.h, fluid.w

        # Auto source
        if auto_source:
            if mode == 0:  # Water - waves from bottom
                for x in range(1, fw - 1):
                    wave = math.sin(t * 2 + x * 0.3) * 0.5 + 0.5
                    fluid.add_density(fh - 3, x, wave * 30)
                    fluid.add_velocity(fh - 3, x, -3 * wave, math.sin(t + x * 0.2) * 2)
                # Side currents
                cx = int(fw * (0.5 + 0.3 * math.sin(t * 0.5)))
                for dy in range(-2, 3):
                    y = max(1, min(fh - 2, fh // 2 + dy))
                    fluid.add_density(y, cx, 50)
                    fluid.add_velocity(y, cx, math.sin(t) * 5, math.cos(t) * 5)

            elif mode == 1:  # Fire - flames from bottom center
                center = fw // 2
                for dx in range(-3, 4):
                    x = max(1, min(fw - 2, center + dx))
                    intensity = 50 * (1 - abs(dx) / 4)
                    fluid.add_density(fh - 3, x, intensity + random.random() * 20)
                    fluid.add_velocity(fh - 3, x, -8 - random.random() * 4, random.gauss(0, 2))

            elif mode == 2:  # Smoke - rising columns
                for i in range(3):
                    sx = int(fw * (i + 1) / 4)
                    fluid.add_density(fh - 3, sx, 40 + random.random() * 20)
                    fluid.add_velocity(fh - 3, sx, -4, random.gauss(0, 1.5))

            elif mode == 3:  # Rainbow - circular
                cx, cy = fw // 2, fh // 2
                for angle in range(0, 360, 30):
                    rad = math.radians(angle + t * 50)
                    r = min(fh, fw) // 4
                    x = int(cx + r * math.cos(rad))
                    y = int(cy + r * math.sin(rad))
                    if 1 <= y < fh - 1 and 1 <= x < fw - 1:
                        fluid.add_density(y, x, 40)
                        fluid.add_velocity(y, x, math.sin(rad + t) * 3, math.cos(rad + t) * 3)

        # Step simulation
        fluid.step()

        # Render
        stdscr.erase()
        chars = char_sets[mode]
        max_char = len(chars) - 1

        for sy in range(min(sim_h, h - 2)):
            for sx in range(min(sim_w, w - 1)):
                fy = min(fh - 1, sy // scale + 1)
                fx = min(fw - 1, sx // scale + 1)
                d = fluid.density[fy][fx]

                if d < 0.5:
                    continue

                ci = min(max_char, int(d / 8))
                ch = chars[ci]

                if mode == 0:  # Water
                    color = curses.color_pair(1) if d < 10 else curses.color_pair(2) if d < 25 else curses.color_pair(7)
                elif mode == 1:  # Fire
                    if d < 8:
                        color = curses.color_pair(5)  # dark red
                    elif d < 20:
                        color = curses.color_pair(5) | curses.A_BOLD  # red
                    elif d < 35:
                        color = curses.color_pair(4)  # yellow
                    else:
                        color = curses.color_pair(4) | curses.A_BOLD  # bright yellow
                elif mode == 2:  # Smoke
                    color = curses.color_pair(8) if d < 15 else curses.color_pair(7)
                else:  # Rainbow
                    hue = (d + t * 10 + sy + sx) % 6
                    color_idx = int(hue) % 6 + 1
                    color = curses.color_pair(color_idx)

                try:
                    stdscr.addstr(sy, sx, ch, color)
                except curses.error:
                    pass

        # Status
        try:
            status = f" {mode_names[mode]} | Auto: {'ON' if auto_source else 'OFF'} | M:Mode A:Auto R:Reset Q:Quit SPACE:Pause "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.03)


if __name__ == "__main__":
    curses.wrapper(main)


def main_entry():
    import curses
    curses.wrapper(main)

