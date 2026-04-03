#!/usr/bin/env python3
"""🐚 Terminal Aquarium - A peaceful ASCII fish tank"""
import curses
import random
import math
import time

FISH_RIGHT = [
    ["><>"],
    ["><>>"],
    [" /\\", "><))'>", " \\/"],
    ["  __", "><(((°>", "  ‾‾"],
    ["><>", " ><>"],
]

FISH_LEFT = [
    ["<><"],
    ["<<><"],
    [" /\\", "'<))><", " \\/"],
    ["  __", "<°)))><", "  ‾‾"],
    ["<><", "<>< "],
]

FISH_COLORS = [1, 2, 3, 4, 5, 6]

SEAWEED_FRAMES = [
    ["|", ")", "|", "(", "|"],
    [")", "|", "(", "|", ")"],
    ["(", "|", ")", "|", "("],
]

CRAB = [
    " _  _ ",
    "(o)(o)",
    " /||\\",
]

STARFISH = ["*"]
SHELL = ["@"]


class Fish:
    def __init__(self, h, w):
        self.style = random.randint(0, len(FISH_RIGHT) - 1)
        self.direction = random.choice([-1, 1])
        self.speed = random.uniform(0.1, 0.4)
        self.color = random.choice(FISH_COLORS)
        sprite = FISH_RIGHT[self.style]
        self.y = random.uniform(2, h - 8)
        if self.direction > 0:
            self.x = -len(sprite[0])
        else:
            self.x = w + 1
        self.wobble_speed = random.uniform(1, 3)
        self.wobble_amp = random.uniform(0.3, 1.0)
        self.base_y = self.y

    def update(self, dt, t):
        self.x += self.direction * self.speed * dt * 30
        self.y = self.base_y + math.sin(t * self.wobble_speed) * self.wobble_amp

    def get_sprite(self):
        if self.direction > 0:
            return FISH_RIGHT[self.style]
        else:
            return FISH_LEFT[self.style]

    def is_offscreen(self, w):
        sprite = self.get_sprite()
        max_w = max(len(line) for line in sprite)
        if self.direction > 0 and self.x > w + 5:
            return True
        if self.direction < 0 and self.x < -max_w - 5:
            return True
        return False


class Bubble:
    def __init__(self, x, y):
        self.x = x + random.gauss(0, 0.5)
        self.y = y
        self.speed = random.uniform(0.15, 0.4)
        self.size = random.choice(['°', 'o', 'O', '○', '◯'])
        self.wobble = random.uniform(0.5, 2)

    def update(self, dt, t):
        self.y -= self.speed * dt * 20
        self.x += math.sin(t * self.wobble + self.y) * 0.05
        return self.y > 0


class Seaweed:
    def __init__(self, x, h, height):
        self.x = x
        self.base_y = h - 3
        self.height = height
        self.color = random.choice([2, 3])  # green shades

    def draw(self, stdscr, t, frame_idx):
        pattern = SEAWEED_FRAMES[frame_idx % len(SEAWEED_FRAMES)]
        for i in range(self.height):
            y = self.base_y - i
            ch = pattern[i % len(pattern)]
            if y > 0:
                try:
                    bold = curses.A_BOLD if i < 2 else 0
                    stdscr.addstr(y, self.x, ch, curses.color_pair(self.color) | bold)
                except curses.error:
                    pass


class Aquarium:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.fish = []
        self.bubbles = []
        self.seaweeds = []
        self.decorations = []

        # Place seaweed
        for _ in range(random.randint(5, 10)):
            x = random.randint(2, w - 3)
            height = random.randint(3, min(8, h - 6))
            self.seaweeds.append(Seaweed(x, h, height))

        # Place bottom decorations
        for _ in range(random.randint(3, 6)):
            x = random.randint(2, w - 5)
            dtype = random.choice(["crab", "starfish", "shell"])
            self.decorations.append({"type": dtype, "x": x, "y": h - 3})

        # Initial fish
        for _ in range(random.randint(5, 10)):
            f = Fish(h, w)
            f.x = random.uniform(5, w - 10)
            self.fish.append(f)

        # Bubble sources
        self.bubble_sources = [random.randint(5, w - 5) for _ in range(random.randint(2, 4))]

    def update(self, dt, t):
        # Update fish
        for f in self.fish:
            f.update(dt, t)
        self.fish = [f for f in self.fish if not f.is_offscreen(self.w)]

        # Spawn new fish
        if len(self.fish) < 12 and random.random() < 0.02:
            self.fish.append(Fish(self.h, self.w))

        # Update bubbles
        self.bubbles = [b for b in self.bubbles if b.update(dt, t)]

        # Spawn bubbles
        for src in self.bubble_sources:
            if random.random() < 0.05:
                self.bubbles.append(Bubble(src, self.h - 4))

        # Fish bubbles
        for f in self.fish:
            if random.random() < 0.02:
                self.bubbles.append(Bubble(f.x + (3 if f.direction > 0 else -1), f.y))

    def draw(self, stdscr, t):
        h, w = self.h, self.w
        frame_idx = int(t * 2)

        # Water background - subtle wave pattern at top
        for x in range(w - 1):
            wave = int(math.sin(x * 0.3 + t * 2) * 0.5 + 0.5)
            try:
                stdscr.addstr(wave, x, "~", curses.color_pair(6) | curses.A_DIM)
            except curses.error:
                pass

        # Sand floor
        for x in range(w - 1):
            try:
                sand_ch = random.choice([".", ":", "·"]) if random.random() < 0.3 else "═"
                stdscr.addstr(h - 2, x, sand_ch, curses.color_pair(3) | curses.A_DIM)
            except curses.error:
                pass

        # Seaweed
        for sw in self.seaweeds:
            sw.draw(stdscr, t, frame_idx)

        # Bottom decorations
        for dec in self.decorations:
            if dec["type"] == "crab":
                crab_frame = CRAB
                for dy, line in enumerate(crab_frame):
                    try:
                        stdscr.addstr(dec["y"] + dy - len(crab_frame) + 1, dec["x"],
                                     line, curses.color_pair(1))
                    except curses.error:
                        pass
            elif dec["type"] == "starfish":
                try:
                    stdscr.addstr(dec["y"], dec["x"], "✦", curses.color_pair(3) | curses.A_BOLD)
                except curses.error:
                    pass
            elif dec["type"] == "shell":
                try:
                    stdscr.addstr(dec["y"], dec["x"], "⊙", curses.color_pair(5))
                except curses.error:
                    pass

        # Fish
        for f in self.fish:
            sprite = f.get_sprite()
            fx, fy = int(f.x), int(f.y)
            for dy, line in enumerate(sprite):
                py = fy + dy
                if 0 <= py < h - 2:
                    for dx, ch in enumerate(line):
                        px = fx + dx
                        if ch != ' ' and 0 <= px < w - 1:
                            try:
                                stdscr.addstr(py, px, ch, curses.color_pair(f.color) | curses.A_BOLD)
                            except curses.error:
                                pass

        # Bubbles
        for b in self.bubbles:
            bx, by = int(b.x), int(b.y)
            if 0 <= by < h - 2 and 0 <= bx < w - 1:
                try:
                    stdscr.addstr(by, bx, b.size, curses.color_pair(6))
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
    tank = Aquarium(h, w)
    last_time = time.time()
    t = 0

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
        elif key == ord('f') or key == ord('F'):
            tank.fish.append(Fish(h, w))
        elif key == ord('b') or key == ord('B'):
            tank.bubbles.append(Bubble(random.randint(5, w - 5), h - 4))

        h, w = stdscr.getmaxyx()
        tank.h = h
        tank.w = w
        tank.update(dt, t)

        stdscr.erase()
        tank.draw(stdscr, t)

        # Status
        try:
            status = f" 🐚 Aquarium | Fish: {len(tank.fish)} | F:Add fish  B:Bubbles  Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.05)


if __name__ == "__main__":
    curses.wrapper(main)
