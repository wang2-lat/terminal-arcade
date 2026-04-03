#!/usr/bin/env python3
"""🌲 Terminal Forest Scene Generator - Procedural ASCII landscape with day/night cycle"""
import curses
import random
import math
import time

TREE_SMALL = [
    "  *  ",
    " /|\\ ",
    "/ | \\",
    "  |  ",
]

TREE_MEDIUM = [
    "    *    ",
    "   /|\\   ",
    "  / | \\  ",
    " /  |  \\ ",
    "/   |   \\",
    "    |    ",
    "   |||   ",
]

TREE_LARGE = [
    "      *      ",
    "     /|\\     ",
    "    / | \\    ",
    "   /  |  \\   ",
    "  /   |   \\  ",
    " /    |    \\ ",
    "/     |     \\",
    "     /|\\     ",
    "    / | \\    ",
    "   /  |  \\   ",
    "     |||     ",
    "     |||     ",
]

PINE = [
    "    ^    ",
    "   /|\\   ",
    "  //|\\\\  ",
    " ///|\\\\\\ ",
    "    |    ",
]

BUSH = [
    " .-. ",
    "(   )",
    " `-' ",
]

FLOWER = [
    " * ",
    " | ",
]

MUSHROOM = [
    " __ ",
    "/  \\",
    " || ",
]


class Star:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.brightness = random.uniform(0.3, 1.0)
        self.twinkle_speed = random.uniform(1, 4)
        self.char = random.choice([".", "·", "*", "✦", "+"])


class Cloud:
    def __init__(self, x, y, w):
        self.x = x
        self.y = y
        size = random.randint(1, 3)
        if size == 1:
            self.shape = ["  ___  ", " /   \\ ", "(_____)"]
        elif size == 2:
            self.shape = ["    ____    ", "  _/    \\   ", " /  ____  \\ ", "(__________)"]
        else:
            self.shape = [" ___ ", "/   \\", "\\___/"]
        self.speed = random.uniform(0.02, 0.08)

    def update(self, dt, w):
        self.x += self.speed * dt * 20
        max_w = max(len(line) for line in self.shape)
        if self.x > w + 5:
            self.x = -max_w - 5


class Raindrop:
    def __init__(self, x, h):
        self.x = x + random.gauss(0, 0.3)
        self.y = random.uniform(-5, 0)
        self.speed = random.uniform(0.5, 1.0)
        self.char = random.choice(["|", "│", "╎", ":"])

    def update(self, dt, h):
        self.y += self.speed * dt * 30
        return self.y < h


class Snowflake:
    def __init__(self, x, h):
        self.x = x
        self.y = random.uniform(-5, 0)
        self.speed = random.uniform(0.1, 0.3)
        self.drift = random.uniform(-0.05, 0.05)
        self.char = random.choice(["❄", "❆", "*", "·"])

    def update(self, dt, h, t):
        self.y += self.speed * dt * 20
        self.x += (self.drift + math.sin(t + self.y) * 0.02) * dt * 20
        return self.y < h


def generate_terrain(w, h):
    """Generate rolling terrain heights."""
    terrain = []
    y = h - 8
    for x in range(w):
        y += random.gauss(0, 0.3)
        y = max(h - 15, min(h - 4, y))
        terrain.append(int(y))
    # Smooth
    for _ in range(3):
        new_terrain = [terrain[0]]
        for i in range(1, len(terrain) - 1):
            new_terrain.append(int((terrain[i-1] + terrain[i] + terrain[i+1]) / 3))
        new_terrain.append(terrain[-1])
        terrain = new_terrain
    return terrain


def generate_scene(h, w):
    terrain = generate_terrain(w, h)
    trees = []
    objects = []

    # Place trees
    for _ in range(random.randint(8, 20)):
        x = random.randint(3, w - 15)
        ground_y = terrain[min(x, len(terrain) - 1)]
        tree_type = random.choice(["small", "medium", "large", "pine"])
        trees.append({"x": x, "y": ground_y, "type": tree_type})

    # Place bushes, flowers, mushrooms
    for _ in range(random.randint(5, 15)):
        x = random.randint(2, w - 8)
        ground_y = terrain[min(x, len(terrain) - 1)]
        obj_type = random.choice(["bush", "flower", "flower", "mushroom"])
        objects.append({"x": x, "y": ground_y, "type": obj_type})

    # Stars
    stars = [Star(random.randint(0, w - 1), random.randint(0, h // 2)) for _ in range(60)]

    # Clouds
    clouds = [Cloud(random.randint(0, w), random.randint(1, h // 3), w) for _ in range(random.randint(3, 6))]

    return terrain, trees, objects, stars, clouds


def get_sky_color(time_of_day):
    """Return color pair index for sky based on time."""
    if 0.25 <= time_of_day < 0.35:  # sunrise
        return 3  # yellow
    elif 0.35 <= time_of_day < 0.65:  # day
        return 4  # cyan
    elif 0.65 <= time_of_day < 0.75:  # sunset
        return 1  # red
    else:  # night
        return 6  # blue


WEATHERS = ["clear", "rain", "snow"]


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
    terrain, trees, objects, stars, clouds = generate_scene(h, w)

    time_of_day = 0.4  # 0=midnight, 0.5=noon
    time_speed = 0.01
    weather = "clear"
    weather_idx = 0
    raindrops = []
    snowflakes = []
    last_time = time.time()
    t = 0
    wind = 0

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
        elif key == ord('w') or key == ord('W'):
            weather_idx = (weather_idx + 1) % len(WEATHERS)
            weather = WEATHERS[weather_idx]
            raindrops.clear()
            snowflakes.clear()
        elif key == ord('n') or key == ord('N'):
            terrain, trees, objects, stars, clouds = generate_scene(h, w)
        elif key == ord('+') or key == ord('='):
            time_speed = min(0.1, time_speed + 0.005)
        elif key == ord('-'):
            time_speed = max(0.001, time_speed - 0.005)

        # Update time
        time_of_day = (time_of_day + time_speed * dt) % 1.0
        is_night = time_of_day < 0.25 or time_of_day > 0.75

        # Update clouds
        for cloud in clouds:
            cloud.update(dt, w)

        # Weather
        if weather == "rain":
            for _ in range(3):
                raindrops.append(Raindrop(random.randint(0, w - 1), h))
            raindrops = [r for r in raindrops if r.update(dt, h)]
        elif weather == "snow":
            if random.random() < 0.3:
                snowflakes.append(Snowflake(random.randint(0, w - 1), h))
            snowflakes = [s for s in snowflakes if s.update(dt, h, t)]

        # Draw
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        sky_color = get_sky_color(time_of_day)

        # Sun/Moon
        sun_angle = time_of_day * math.pi * 2 - math.pi / 2
        sun_x = int(w / 2 + math.cos(sun_angle) * w * 0.35)
        sun_y = int(h / 3 - math.sin(sun_angle) * h * 0.25)

        if 0 <= sun_y < h and 0 <= sun_x < w:
            try:
                if 0.3 <= time_of_day <= 0.7:  # Day
                    stdscr.addstr(sun_y, sun_x, "☀", curses.color_pair(3) | curses.A_BOLD)
                    # Sun rays
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        rx, ry = sun_x + dx * 2, sun_y + dy
                        if 0 <= ry < h and 0 <= rx < w:
                            stdscr.addstr(ry, rx, "·", curses.color_pair(3))
                else:
                    moon_phase = "🌙"
                    stdscr.addstr(max(1, sun_y), max(0, sun_x), moon_phase, curses.color_pair(7) | curses.A_BOLD)
            except curses.error:
                pass

        # Stars (only at night)
        if is_night:
            for star in stars:
                brightness = (math.sin(t * star.twinkle_speed) + 1) / 2
                if brightness > 0.3 and star.y < min(terrain):
                    try:
                        attr = curses.A_BOLD if brightness > 0.7 else curses.A_DIM
                        stdscr.addstr(star.y, star.x, star.char, curses.color_pair(7) | attr)
                    except curses.error:
                        pass

        # Clouds
        for cloud in clouds:
            cloud_color = 7 if not is_night else 8
            for dy, line in enumerate(cloud.shape):
                cy = cloud.y + dy
                cx = int(cloud.x)
                if 0 <= cy < h:
                    for dx, ch in enumerate(line):
                        px = cx + dx
                        if ch != ' ' and 0 <= px < w - 1:
                            try:
                                stdscr.addstr(cy, px, ch, curses.color_pair(cloud_color))
                            except curses.error:
                                pass

        # Terrain
        for x in range(min(w - 1, len(terrain))):
            ground_y = terrain[x]
            for y in range(ground_y, h - 1):
                try:
                    if y == ground_y:
                        grass_ch = random.choice(["▁", "▂", "~"]) if random.random() < 0.1 else "▔"
                        stdscr.addstr(y, x, grass_ch, curses.color_pair(2))
                    elif y < ground_y + 2:
                        stdscr.addstr(y, x, "░", curses.color_pair(2) | curses.A_DIM)
                    else:
                        stdscr.addstr(y, x, "░", curses.color_pair(3) | curses.A_DIM)
                except curses.error:
                    pass

        # Trees
        tree_color = 2 if not is_night else 8
        for tree in trees:
            if tree["type"] == "small":
                sprite = TREE_SMALL
            elif tree["type"] == "medium":
                sprite = TREE_MEDIUM
            elif tree["type"] == "large":
                sprite = TREE_LARGE
            else:
                sprite = PINE

            for dy, line in enumerate(sprite):
                ty = tree["y"] - len(sprite) + dy
                for dx, ch in enumerate(line):
                    px = tree["x"] + dx
                    if ch != ' ' and 0 <= ty < h - 1 and 0 <= px < w - 1:
                        try:
                            if ch in ('|', '\\', '/', '|'):
                                c = curses.color_pair(3 if not is_night else 8)
                            elif ch == '*':
                                c = curses.color_pair(3) | curses.A_BOLD
                            else:
                                c = curses.color_pair(tree_color)
                            stdscr.addstr(ty, px, ch, c)
                        except curses.error:
                            pass

        # Objects
        for obj in objects:
            if obj["type"] == "bush":
                sprite = BUSH
                color = 2
            elif obj["type"] == "flower":
                sprite = FLOWER
                color = random.choice([1, 5, 3])
            else:
                sprite = MUSHROOM
                color = 1

            for dy, line in enumerate(sprite):
                oy = obj["y"] - len(sprite) + dy
                for dx, ch in enumerate(line):
                    px = obj["x"] + dx
                    if ch != ' ' and 0 <= oy < h - 1 and 0 <= px < w - 1:
                        try:
                            stdscr.addstr(oy, px, ch, curses.color_pair(color))
                        except curses.error:
                            pass

        # Rain
        for drop in raindrops:
            dx, dy = int(drop.x), int(drop.y)
            if 0 <= dy < h - 1 and 0 <= dx < w - 1:
                try:
                    stdscr.addstr(dy, dx, drop.char, curses.color_pair(6))
                except curses.error:
                    pass

        # Snow
        for flake in snowflakes:
            fx, fy = int(flake.x), int(flake.y)
            if 0 <= fy < h - 1 and 0 <= fx < w - 1:
                try:
                    stdscr.addstr(fy, fx, flake.char, curses.color_pair(7))
                except curses.error:
                    pass

        # Time indicator
        hours = int(time_of_day * 24)
        minutes = int((time_of_day * 24 - hours) * 60)
        time_str = f"{hours:02d}:{minutes:02d}"
        period = "Night" if is_night else "Sunrise" if time_of_day < 0.35 else "Day" if time_of_day < 0.65 else "Sunset"

        try:
            status = f" 🌲 {period} {time_str} | {weather.title()} | N:New scene W:Weather +/-:Speed Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.05)


if __name__ == "__main__":
    curses.wrapper(main)
