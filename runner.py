#!/usr/bin/env python3
"""🏃 Terminal Runner - Endless obstacle runner game!"""
import curses
import random
import time
import math

PLAYER_FRAMES = {
    "run1": [" O ", "/|\\", "/ \\"],
    "run2": [" O ", "/|\\", " |>"],
    "jump": [" O ", "\\|/", " ^ "],
    "duck": ["   ", "_O_", "/|\\"],
    "dead": [" x ", "/|\\", "/ \\"],
}

OBSTACLES = {
    "cactus_small": [" | ", "/|\\", " | "],
    "cactus_large": [" |/ ", "/|\\ ", " || ", " || "],
    "rock": ["___", "/  \\", "\\__/"],
    "bird_1": [" >", "=-", " >"],
    "bird_2": [" >", "-=", " >"],
}

GROUND_CHARS = ["_", "=", "─", "═"]


class Runner:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.ground_y = h - 6
        self.player_x = 10
        self.player_y = self.ground_y - 3
        self.jumping = False
        self.ducking = False
        self.jump_velocity = 0
        self.jump_power = -1.8
        self.gravity = 0.12
        self.frame = 0
        self.speed = 0.5
        self.score = 0
        self.high_score = 0
        self.obstacles = []
        self.particles = []
        self.stars = [(random.randint(0, w), random.randint(0, h // 2), random.choice([".", "·", "*"])) for _ in range(30)]
        self.clouds = [[random.randint(0, w), random.randint(2, h // 3)] for _ in range(5)]
        self.game_over = False
        self.spawn_timer = 0
        self.distance = 0
        self.night_mode = False

    def jump(self):
        if not self.jumping and not self.ducking:
            self.jumping = True
            self.jump_velocity = self.jump_power

    def duck_start(self):
        if not self.jumping:
            self.ducking = True

    def duck_end(self):
        self.ducking = False

    def update(self, dt):
        if self.game_over:
            return

        self.frame += 1
        self.distance += self.speed * dt * 60
        self.score = int(self.distance)
        self.speed = min(2.0, 0.5 + self.distance * 0.0001)

        # Switch day/night
        if int(self.distance) % 2000 < 1000:
            self.night_mode = False
        else:
            self.night_mode = True

        # Jump physics
        if self.jumping:
            self.player_y += self.jump_velocity
            self.jump_velocity += self.gravity
            if self.player_y >= self.ground_y - 3:
                self.player_y = self.ground_y - 3
                self.jumping = False
                self.jump_velocity = 0
                # Dust particles
                for _ in range(3):
                    self.particles.append({
                        "x": self.player_x + random.uniform(-1, 3),
                        "y": self.ground_y,
                        "vx": random.uniform(-0.3, 0.3),
                        "vy": random.uniform(-0.3, -0.1),
                        "life": random.uniform(0.3, 0.8),
                        "char": random.choice([".", "·", "*"]),
                    })

        # Spawn obstacles
        self.spawn_timer -= dt * self.speed * 60
        if self.spawn_timer <= 0:
            self.spawn_timer = random.uniform(30, 60)
            obs_type = random.choice(list(OBSTACLES.keys()))
            is_flying = obs_type.startswith("bird")
            y = self.ground_y - 5 if is_flying else self.ground_y - len(OBSTACLES[obs_type])
            self.obstacles.append({
                "type": obs_type,
                "x": self.w + 5,
                "y": y,
                "flying": is_flying,
            })

        # Move obstacles
        for obs in self.obstacles:
            obs["x"] -= self.speed * dt * 60
            if obs["flying"]:
                obs["y"] += math.sin(self.frame * 0.1) * 0.1

        # Remove offscreen
        self.obstacles = [o for o in self.obstacles if o["x"] > -10]

        # Collision detection
        player_box = (self.player_x, int(self.player_y), self.player_x + 3,
                      int(self.player_y) + (2 if self.ducking else 3))

        for obs in self.obstacles:
            shape = OBSTACLES[obs["type"]]
            obs_box = (int(obs["x"]), int(obs["y"]),
                      int(obs["x"]) + max(len(line) for line in shape), int(obs["y"]) + len(shape))

            if (player_box[0] < obs_box[2] and player_box[2] > obs_box[0] and
                player_box[1] < obs_box[3] and player_box[3] > obs_box[1]):
                self.game_over = True
                self.high_score = max(self.high_score, self.score)
                # Death particles
                for _ in range(15):
                    self.particles.append({
                        "x": self.player_x + 1.5,
                        "y": self.player_y + 1.5,
                        "vx": random.uniform(-1, 1),
                        "vy": random.uniform(-1, 0.5),
                        "life": random.uniform(0.5, 1.5),
                        "char": random.choice(["*", "✦", "♦", "●"]),
                    })
                break

        # Update particles
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.05
            p["life"] -= dt * 2
        self.particles = [p for p in self.particles if p["life"] > 0]

        # Move clouds
        for cloud in self.clouds:
            cloud[0] -= self.speed * dt * 10
            if cloud[0] < -10:
                cloud[0] = self.w + random.randint(5, 20)
                cloud[1] = random.randint(2, self.h // 3)

    def draw(self, stdscr):
        h, w = self.h, self.w

        # Stars (night)
        if self.night_mode:
            for sx, sy, sch in self.stars:
                if 0 <= sy < h and 0 <= sx < w:
                    try:
                        stdscr.addstr(sy, sx, sch, curses.color_pair(7) | curses.A_DIM)
                    except curses.error:
                        pass

        # Clouds
        for cx, cy in self.clouds:
            ix = int(cx)
            if 0 <= cy < h and 0 <= ix < w - 5:
                try:
                    color = curses.color_pair(8) if self.night_mode else curses.color_pair(7)
                    stdscr.addstr(int(cy), ix, "☁", color)
                except curses.error:
                    pass

        # Ground
        for x in range(w - 1):
            shifted = (x + int(self.distance)) % 20
            ch = "═" if shifted < 18 else "╬"
            try:
                stdscr.addstr(self.ground_y + 1, x, ch, curses.color_pair(3 if not self.night_mode else 8))
            except curses.error:
                pass

        # Obstacles
        for obs in self.obstacles:
            shape = OBSTACLES[obs["type"]]
            # Animate birds
            if obs["flying"] and obs["type"].startswith("bird"):
                shape = OBSTACLES["bird_1" if self.frame % 10 < 5 else "bird_2"]
            ox, oy = int(obs["x"]), int(obs["y"])
            for dy, line in enumerate(shape):
                for dx, ch in enumerate(line):
                    px, py = ox + dx, oy + dy
                    if ch != ' ' and 0 <= py < h and 0 <= px < w:
                        try:
                            color = curses.color_pair(1) if obs["flying"] else curses.color_pair(2)
                            stdscr.addstr(py, px, ch, color)
                        except curses.error:
                            pass

        # Player
        if self.game_over:
            sprite = PLAYER_FRAMES["dead"]
        elif self.jumping:
            sprite = PLAYER_FRAMES["jump"]
        elif self.ducking:
            sprite = PLAYER_FRAMES["duck"]
        else:
            sprite = PLAYER_FRAMES["run1" if self.frame % 10 < 5 else "run2"]

        py = int(self.player_y)
        for dy, line in enumerate(sprite):
            for dx, ch in enumerate(line):
                px = self.player_x + dx
                if ch != ' ' and 0 <= py + dy < h and 0 <= px < w:
                    try:
                        stdscr.addstr(py + dy, px, ch, curses.color_pair(4) | curses.A_BOLD)
                    except curses.error:
                        pass

        # Particles
        for p in self.particles:
            ix, iy = int(p["x"]), int(p["y"])
            if 0 <= iy < h and 0 <= ix < w:
                try:
                    attr = curses.A_BOLD if p["life"] > 0.5 else curses.A_DIM
                    stdscr.addstr(iy, ix, p["char"], curses.color_pair(3) | attr)
                except curses.error:
                    pass

        # HUD
        try:
            hud = f" Score: {self.score}  |  High: {self.high_score}  |  Speed: {self.speed:.1f}x "
            stdscr.addstr(0, 0, hud, curses.color_pair(3) | curses.A_BOLD)
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

    # Welcome
    stdscr.nodelay(False)
    stdscr.clear()
    title = [
        "╔══════════════════════════╗",
        "║   🏃 TERMINAL RUNNER 🏃  ║",
        "╠══════════════════════════╣",
        "║   SPACE/↑: Jump          ║",
        "║   ↓: Duck                ║",
        "║   Avoid obstacles!       ║",
        "║                          ║",
        "║   Press ENTER to start   ║",
        "╚══════════════════════════╝",
    ]
    for i, line in enumerate(title):
        color = curses.color_pair(3) if i in (0, 2, 8) else curses.color_pair(4)
        try:
            stdscr.addstr(h // 2 - 5 + i, max(0, (w - len(line)) // 2), line, color)
        except curses.error:
            pass
    stdscr.refresh()
    stdscr.getch()
    stdscr.nodelay(True)

    game = Runner(h, w)
    last_time = time.time()
    high_score = 0

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now

        keys = set()
        while True:
            try:
                k = stdscr.getch()
                if k == -1:
                    break
                keys.add(k)
            except:
                break

        if ord('q') in keys or ord('Q') in keys:
            break

        if game.game_over:
            if ord(' ') in keys or curses.KEY_ENTER in keys or 10 in keys:
                high_score = max(high_score, game.score)
                game = Runner(h, w)
                game.high_score = high_score
                continue

            stdscr.erase()
            game.draw(stdscr)
            try:
                stdscr.addstr(h // 2 - 1, max(0, (w - 20) // 2), "  GAME OVER!  ",
                             curses.color_pair(1) | curses.A_BOLD)
                stdscr.addstr(h // 2 + 1, max(0, (w - 25) // 2), "SPACE: Restart  Q: Quit",
                             curses.color_pair(8))
            except curses.error:
                pass
            stdscr.refresh()
            time.sleep(0.05)
            continue

        if ord(' ') in keys or curses.KEY_UP in keys:
            game.jump()
        if curses.KEY_DOWN in keys:
            game.duck_start()
        else:
            game.duck_end()

        game.update(dt)

        stdscr.erase()
        game.draw(stdscr)
        stdscr.refresh()
        time.sleep(0.016)


if __name__ == "__main__":
    curses.wrapper(main)
