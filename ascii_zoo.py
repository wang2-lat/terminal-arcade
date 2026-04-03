#!/usr/bin/env python3
"""🦁 ASCII Zoo - Animated ASCII animals parade!"""
import curses
import time
import random
import math

ANIMALS = {
    "cat": {
        "frames": [
            [r"  /\_/\  ", r" ( o.o ) ", r"  > ^ <  ", r" /|   |\ "],
            [r"  /\_/\  ", r" ( o.o ) ", r"  > ^ <  ", r"  |   |  "],
        ],
        "color": 3, "speed": 0.3,
    },
    "dog": {
        "frames": [
            [r"  / \__  ", r" (    @\___", r" /         O", r"/   (_____/ ", r"/_____/   U "],
            [r"  / \__  ", r" (    @\___", r" /         O", r"/   (_____/ ", r"/_____/ U   "],
        ],
        "color": 3, "speed": 0.4,
    },
    "bird": {
        "frames": [
            [r"  _  ", r" / \ ", r"(o  >", r" \_/ ", r" /|  "],
            [r"  _  ", r" / \ ", r"(o  >", r" \-/ ", r"  |\ "],
        ],
        "color": 4, "speed": 0.5,
    },
    "fish": {
        "frames": [
            [r" ><(((°> "],
            [r" ><)))°> "],
        ],
        "color": 6, "speed": 0.3,
    },
    "rabbit": {
        "frames": [
            [r" (\(\  ", r" (-.-)  ", r" o_(')_(')"],
            [r" (\ (\ ", r" ( -.-) ", r" o_(')(') "],
        ],
        "color": 7, "speed": 0.35,
    },
    "snake": {
        "frames": [
            [r"    /^\/^\  ", r"  _|__|  O| ", r" \/     /  \", r"  \  __/    "],
            [r"    /^\/^\  ", r"  _|__|  o| ", r" \/     /  \", r"  \  __/    "],
        ],
        "color": 2, "speed": 0.2,
    },
    "elephant": {
        "frames": [
            [r"    ___     ", r"   /   \    ", r"  | O O |   ", r"  |  _  |---)", r"   \___/    ", r"   /| |\    ", r"  / | | \   "],
            [r"    ___     ", r"   /   \    ", r"  | O O |   ", r"  |  _  |---)", r"   \___/    ", r"   /|  |\   ", r"  / |  | \  "],
        ],
        "color": 7, "speed": 0.15,
    },
    "turtle": {
        "frames": [
            [r"    ____   ", r"  /(____)\ ", r" |  O  O | ", r" |   __  | ", r"  \_____/  ", r"   _|  |_  "],
            [r"    ____   ", r"  /(____)\ ", r" |  O  O | ", r" |   __  | ", r"  \_____/  ", r"  _|   |_  "],
        ],
        "color": 2, "speed": 0.1,
    },
}


class AnimalSprite:
    def __init__(self, animal_type, h, w):
        self.type = animal_type
        data = ANIMALS[animal_type]
        self.frames = data["frames"]
        self.color = data["color"]
        self.speed = data["speed"] + random.uniform(-0.05, 0.05)
        self.direction = random.choice([-1, 1])
        self.frame_idx = 0
        self.frame_timer = 0

        sprite_w = max(len(line) for frame in self.frames for line in frame)
        if self.direction > 0:
            self.x = -sprite_w - 5
        else:
            self.x = w + 5

        self.y = random.randint(3, h - 10)

    def update(self, dt):
        self.x += self.direction * self.speed * dt * 30
        self.frame_timer += dt
        if self.frame_timer > 0.3:
            self.frame_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)

    def draw(self, stdscr, h, w):
        frame = self.frames[self.frame_idx]
        # Flip if going left
        if self.direction < 0:
            frame = [line[::-1].replace('/', 'TEMP').replace('\\', '/').replace('TEMP', '\\')
                    .replace('(', 'TEMP').replace(')', '(').replace('TEMP', ')')
                    .replace('<', 'TEMP').replace('>', '<').replace('TEMP', '>')
                    for line in frame]

        for dy, line in enumerate(frame):
            py = int(self.y) + dy
            for dx, ch in enumerate(line):
                px = int(self.x) + dx
                if ch != ' ' and 0 <= py < h - 1 and 0 <= px < w - 1:
                    try:
                        stdscr.addstr(py, px, ch, curses.color_pair(self.color))
                    except curses.error:
                        pass

    def is_offscreen(self, w):
        sprite_w = max(len(line) for line in self.frames[0])
        if self.direction > 0 and self.x > w + 10:
            return True
        if self.direction < 0 and self.x < -sprite_w - 10:
            return True
        return False


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
    sprites = []
    spawn_timer = 0
    last_time = time.time()
    animal_names = list(ANIMALS.keys())

    # Start with a few
    for _ in range(3):
        name = random.choice(animal_names)
        s = AnimalSprite(name, h, w)
        s.x = random.uniform(5, w - 15)
        sprites.append(s)

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now

        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord(' '):
            name = random.choice(animal_names)
            sprites.append(AnimalSprite(name, h, w))

        h, w = stdscr.getmaxyx()

        # Auto-spawn
        spawn_timer += dt
        if spawn_timer > 2 and len(sprites) < 15:
            spawn_timer = 0
            name = random.choice(animal_names)
            sprites.append(AnimalSprite(name, h, w))

        for s in sprites:
            s.update(dt)
        sprites = [s for s in sprites if not s.is_offscreen(w)]

        stdscr.erase()

        # Ground
        ground_y = h - 3
        for x in range(w - 1):
            try:
                stdscr.addstr(ground_y, x, "~" if x % 8 < 4 else "─", curses.color_pair(2) | curses.A_DIM)
                if x % 15 == 7:
                    stdscr.addstr(ground_y - 1, x, "🌿" if random.random() < 0.5 else "*",
                                 curses.color_pair(2))
            except curses.error:
                pass

        # Draw sprites sorted by Y position
        for s in sorted(sprites, key=lambda s: s.y):
            s.draw(stdscr, h, w)

        # Title
        try:
            title = "🦁 ASCII ZOO 🐘"
            stdscr.addstr(0, max(0, (w - len(title)) // 2), title, curses.color_pair(3) | curses.A_BOLD)
            status = f" Animals: {len(sprites)} | SPACE:Add Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.05)


if __name__ == "__main__":
    curses.wrapper(main)
