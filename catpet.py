#!/usr/bin/env python3
"""🐱 Terminal Cat Pet - Your desktop ASCII kitty companion!"""
import curses
import random
import time
import math

CAT_IDLE = [
    r"  /\_/\  ",
    r" ( o.o ) ",
    r"  > ^ <  ",
    r" /|   |\ ",
    r"(_|   |_)",
]

CAT_WALK_1 = [
    r"  /\_/\  ",
    r" ( o.o ) ",
    r"  > ^ <  ",
    r" /|   |\ ",
    r"(_/   \_)",
]

CAT_WALK_2 = [
    r"  /\_/\  ",
    r" ( o.o ) ",
    r"  > ^ <  ",
    r" \|   |/ ",
    r" (_| |_) ",
]

CAT_SLEEP_1 = [
    r"  /\_/\  ",
    r" ( -.- ) ",
    r"  > ^ <  ",
    r"  (___)) ",
    r"   z Z   ",
]

CAT_SLEEP_2 = [
    r"  /\_/\  ",
    r" ( -.- ) ",
    r"  > ^ <  ",
    r"  (___)) ",
    r"  z Z z  ",
]

CAT_HAPPY = [
    r"  /\_/\  ",
    r" ( ^.^ ) ",
    r"  > ^ <  ",
    r" /|   |\ ",
    r"(_|   |_)",
]

CAT_PLAY = [
    r"  /\_/\  ",
    r" ( o.O ) ",
    r"  > w <  ",
    r"  \| |/  ",
    r"  _/ \_  ",
]

CAT_SIT = [
    r"  /\_/\  ",
    r" ( o.o ) ",
    r"  > ^ <  ",
    r"  |   |  ",
    r"  (___) ~",
]

CAT_JUMP = [
    r"  /\_/\  ",
    r" ( O.O ) ",
    r"  > ^ <  ",
    r"  \   /  ",
    r"   \_/   ",
]

YARN = [
    "  ___  ",
    " /   \\ ",
    "(  @  )",
    " \\___/ ",
]

FISH = "🐟"
HEART = "♥"
MOUSE = [
    "  /\\  ",
    " (oo) ",
    "('  ')",
    "  \"\" ",
]

THOUGHT_BUBBLES = [
    "fish...", "nap time...", "meow?", "yarn!",
    "*purr*", "pet me!", "hungry!", "play!",
    "zzzz...", "*stretch*", "birb?", "box!",
]


class CatPet:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.x = w // 2
        self.y = h - 8
        self.state = "idle"  # idle, walking, sleeping, playing, sitting, jumping
        self.direction = 1  # 1=right, -1=left
        self.frame = 0
        self.state_timer = 0
        self.state_duration = random.uniform(2, 5)
        self.happiness = 80
        self.energy = 70
        self.hunger = 30
        self.thought = ""
        self.thought_timer = 0
        self.items = []  # Objects on screen
        self.hearts = []  # Floating hearts
        self.jump_height = 0
        self.target_x = None

    def think(self, text):
        self.thought = text
        self.thought_timer = 3

    def pet(self):
        self.happiness = min(100, self.happiness + 15)
        self.state = "happy"
        self.state_timer = 0
        self.state_duration = 2
        self.think("*purr purr*")
        for _ in range(3):
            self.hearts.append([self.x + random.randint(-2, 6), self.y - 2, 2.0])

    def feed(self):
        self.hunger = max(0, self.hunger - 30)
        self.happiness = min(100, self.happiness + 10)
        self.think("yummy!")
        self.state = "happy"
        self.state_timer = 0
        self.state_duration = 2

    def add_yarn(self):
        self.items.append({"type": "yarn", "x": random.randint(5, self.w - 10), "y": self.h - 7})
        self.think("yarn!!")
        self.state = "playing"
        self.state_timer = 0

    def update(self, dt):
        self.frame += 1
        self.state_timer += dt
        self.thought_timer = max(0, self.thought_timer - dt)

        # Stats decay
        self.hunger = min(100, self.hunger + dt * 0.5)
        self.energy = max(0, min(100, self.energy + (dt * 2 if self.state == "sleeping" else -dt * 0.3)))
        self.happiness = max(0, self.happiness - dt * 0.2)

        # Random thoughts
        if self.thought_timer <= 0 and random.random() < 0.01:
            self.think(random.choice(THOUGHT_BUBBLES))

        # Update hearts
        for heart in self.hearts:
            heart[1] -= dt * 2
            heart[2] -= dt
        self.hearts = [h for h in self.hearts if h[2] > 0]

        # State transitions
        if self.state_timer >= self.state_duration:
            self.pick_state()

        # State behaviors
        if self.state == "walking":
            speed = 0.5
            self.x += self.direction * speed
            if self.x < 2 or self.x > self.w - 12:
                self.direction *= -1

            # Walk to yarn if exists
            if self.items:
                target = self.items[0]
                if abs(self.x - target["x"]) < 2:
                    self.state = "playing"
                    self.state_timer = 0
                    self.state_duration = 3
                    self.items.pop(0)
                    self.happiness = min(100, self.happiness + 20)
                    self.think("*pounce!*")
                elif self.x < target["x"]:
                    self.direction = 1
                else:
                    self.direction = -1

        elif self.state == "jumping":
            phase = self.state_timer / self.state_duration
            self.jump_height = math.sin(phase * math.pi) * 4
        else:
            self.jump_height = max(0, self.jump_height - dt * 10)

    def pick_state(self):
        self.state_timer = 0
        if self.energy < 20:
            self.state = "sleeping"
            self.state_duration = random.uniform(5, 10)
            self.think("so sleepy...")
        elif self.hunger > 70:
            self.state = "sitting"
            self.state_duration = random.uniform(2, 4)
            self.think("hungry...")
        elif random.random() < 0.3:
            self.state = "walking"
            self.state_duration = random.uniform(3, 8)
            self.direction = random.choice([-1, 1])
        elif random.random() < 0.3:
            self.state = "sitting"
            self.state_duration = random.uniform(2, 6)
        elif random.random() < 0.3:
            self.state = "sleeping"
            self.state_duration = random.uniform(4, 8)
            self.think("nap time~")
        elif random.random() < 0.4:
            self.state = "jumping"
            self.state_duration = 0.8
        else:
            self.state = "idle"
            self.state_duration = random.uniform(1, 4)

    def get_sprite(self):
        if self.state == "walking":
            return CAT_WALK_1 if self.frame % 20 < 10 else CAT_WALK_2
        elif self.state == "sleeping":
            return CAT_SLEEP_1 if self.frame % 30 < 15 else CAT_SLEEP_2
        elif self.state == "happy":
            return CAT_HAPPY
        elif self.state == "playing":
            return CAT_PLAY
        elif self.state == "sitting":
            return CAT_SIT
        elif self.state == "jumping":
            return CAT_JUMP
        else:
            return CAT_IDLE


def draw_bar(stdscr, y, x, width, value, max_val, color, label):
    ratio = value / max_val
    filled = int(width * ratio)
    try:
        stdscr.addstr(y, x, f"{label}: ", curses.color_pair(7))
        stdscr.addstr(y, x + len(label) + 2, "█" * filled, curses.color_pair(color))
        stdscr.addstr(y, x + len(label) + 2 + filled, "░" * (width - filled), curses.color_pair(8))
        stdscr.addstr(y, x + len(label) + 2 + width + 1, f"{int(value)}%", curses.color_pair(color))
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
    cat = CatPet(h, w)
    last_time = time.time()

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
        elif key == ord('p') or key == ord('P'):
            cat.pet()
        elif key == ord('f') or key == ord('F'):
            cat.feed()
        elif key == ord('y') or key == ord('Y'):
            cat.add_yarn()
        elif key == ord(' '):
            cat.state = "jumping"
            cat.state_timer = 0
            cat.state_duration = 0.8
            cat.think("wheee!")

        h, w = stdscr.getmaxyx()
        cat.h = h
        cat.w = w
        cat.update(dt)

        stdscr.erase()

        # Title
        title = "🐱 Terminal Cat Pet 🐱"
        try:
            stdscr.addstr(0, max(0, (w - len(title)) // 2), title, curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

        # Stats
        draw_bar(stdscr, 2, 2, 15, cat.happiness, 100, 1 if cat.happiness < 30 else 2, "Happy")
        draw_bar(stdscr, 3, 2, 15, cat.energy, 100, 1 if cat.energy < 20 else 4, "Energy")
        draw_bar(stdscr, 4, 2, 15, 100 - cat.hunger, 100, 1 if cat.hunger > 70 else 3, "Food")

        # Status
        state_display = {
            "idle": "Chilling", "walking": "Walking", "sleeping": "Sleeping 💤",
            "happy": "Happy! ♥", "playing": "Playing!", "sitting": "Sitting",
            "jumping": "Jumping!"
        }
        try:
            stdscr.addstr(2, w - 25, f"State: {state_display.get(cat.state, cat.state)}",
                         curses.color_pair(4))
        except curses.error:
            pass

        # Ground
        ground_y = h - 3
        try:
            stdscr.addstr(ground_y, 0, "─" * (w - 1), curses.color_pair(8))
        except curses.error:
            pass

        # Draw items
        for item in cat.items:
            if item["type"] == "yarn":
                for dy, line in enumerate(YARN):
                    iy = item["y"] + dy
                    ix = item["x"]
                    if 0 <= iy < h and 0 <= ix + len(line) < w:
                        try:
                            stdscr.addstr(iy, ix, line, curses.color_pair(1))
                        except curses.error:
                            pass

        # Draw cat
        sprite = cat.get_sprite()
        cx = int(cat.x)
        cy = int(cat.y - cat.jump_height)

        # Flip sprite if going left
        if cat.direction < 0:
            sprite = [line[::-1].replace('/', 'TEMP').replace('\\', '/').replace('TEMP', '\\')
                     for line in sprite]

        for dy, line in enumerate(sprite):
            py = cy + dy
            if 0 <= py < h - 1 and 0 <= cx < w:
                try:
                    color = curses.color_pair(3) if cat.state == "happy" else curses.color_pair(7)
                    stdscr.addstr(py, cx, line[:w - cx - 1], color)
                except curses.error:
                    pass

        # Shadow under cat when jumping
        if cat.jump_height > 0.5:
            shadow_w = max(1, int(9 - cat.jump_height))
            shadow_x = cx + (9 - shadow_w) // 2
            try:
                stdscr.addstr(int(cat.y) + 4, shadow_x, "·" * shadow_w, curses.color_pair(8))
            except curses.error:
                pass

        # Thought bubble
        if cat.thought_timer > 0 and cat.thought:
            bubble_x = cx + 10
            bubble_y = cy - 2
            if 0 <= bubble_y < h and bubble_x + len(cat.thought) + 4 < w:
                try:
                    stdscr.addstr(bubble_y, bubble_x, "°", curses.color_pair(8))
                    stdscr.addstr(bubble_y - 1, bubble_x + 1, "o", curses.color_pair(8))
                    text = f"( {cat.thought} )"
                    stdscr.addstr(bubble_y - 2, bubble_x + 2, text, curses.color_pair(4))
                except curses.error:
                    pass

        # Floating hearts
        for hx, hy, life in cat.hearts:
            ix, iy = int(hx), int(hy)
            if 0 <= iy < h and 0 <= ix < w:
                try:
                    alpha = min(1.0, life)
                    attr = curses.A_BOLD if alpha > 0.5 else curses.A_DIM
                    stdscr.addstr(iy, ix, HEART, curses.color_pair(1) | attr)
                except curses.error:
                    pass

        # Controls
        try:
            controls = " P:Pet  F:Feed  Y:Yarn  SPACE:Jump  Q:Quit "
            stdscr.addstr(h - 1, max(0, (w - len(controls)) // 2), controls, curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.05)


if __name__ == "__main__":
    curses.wrapper(main)
