#!/usr/bin/env python3
"""🚀 Terminal Space Shooter - ASCII Arcade Action!"""
import curses
import random
import time
import math


class Entity:
    def __init__(self, y, x, shape, color=7):
        self.y = y
        self.x = x
        self.shape = shape
        self.color = color
        self.alive = True
        self.health = 1

    def draw(self, stdscr, h, w):
        if not self.alive:
            return
        for dy, row in enumerate(self.shape):
            for dx, ch in enumerate(row):
                if ch != ' ':
                    py, px = int(self.y) + dy, int(self.x) + dx
                    if 0 <= py < h and 0 <= px < w:
                        try:
                            stdscr.addstr(py, px, ch, curses.color_pair(self.color) | curses.A_BOLD)
                        except curses.error:
                            pass

    @property
    def width(self):
        return max(len(r) for r in self.shape)

    @property
    def height(self):
        return len(self.shape)

    def collides(self, other):
        if not self.alive or not other.alive:
            return False
        return (abs(self.y - other.y) < max(self.height, other.height) and
                abs(self.x - other.x) < max(self.width, other.width))


PLAYER_SHAPE = [
    "  △  ",
    " ╱▽╲ ",
    "╱═══╲",
    "╚═╩═╝",
]

ENEMY_SHAPES = [
    ["╔═╗", "╠▼╣", "╚═╝"],           # Basic
    [" ◥◤ ", "◢███◣", " ◥◤ "],       # Medium
    ["╔═══╗", "║▼▼▼║", "╠═══╣", "╚═══╝"],  # Large
]

BOSS_SHAPE = [
    " ╔═══════╗ ",
    "╔╣▼ ▼ ▼ ▼╠╗",
    "║╠═══════╣║",
    "╚╣ █████ ╠╝",
    " ╚═══════╝ ",
]

EXPLOSION_FRAMES = [
    ["*"],
    [" * ", "***", " * "],
    ["  *  ", " *** ", "*****", " *** ", "  *  "],
    [" · · ", "· · ·", " · · "],
    ["  .  ", " . . ", "  .  "],
]


class Bullet:
    def __init__(self, y, x, dy, dx, ch="│", color=3, damage=1):
        self.y = y
        self.x = x
        self.dy = dy
        self.dx = dx
        self.ch = ch
        self.color = color
        self.alive = True
        self.damage = damage

    def update(self):
        self.y += self.dy
        self.x += self.dx

    def draw(self, stdscr, h, w):
        if not self.alive:
            return
        py, px = int(self.y), int(self.x)
        if 0 <= py < h and 0 <= px < w:
            try:
                stdscr.addstr(py, px, self.ch, curses.color_pair(self.color) | curses.A_BOLD)
            except curses.error:
                pass


class Explosion:
    def __init__(self, y, x, color=4):
        self.y = y
        self.x = x
        self.frame = 0
        self.color = color
        self.alive = True
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        if self.timer > 0.08:
            self.timer = 0
            self.frame += 1
            if self.frame >= len(EXPLOSION_FRAMES):
                self.alive = False

    def draw(self, stdscr, h, w):
        if not self.alive or self.frame >= len(EXPLOSION_FRAMES):
            return
        frame = EXPLOSION_FRAMES[self.frame]
        colors = [4, 5, 5, 8, 8]
        color = colors[min(self.frame, len(colors) - 1)]
        for dy, row in enumerate(frame):
            for dx, ch in enumerate(row):
                if ch != ' ':
                    py = int(self.y) + dy - len(frame) // 2
                    px = int(self.x) + dx - len(row) // 2
                    if 0 <= py < h and 0 <= px < w:
                        try:
                            stdscr.addstr(py, px, ch, curses.color_pair(color) | curses.A_BOLD)
                        except curses.error:
                            pass


class Star:
    def __init__(self, y, x, speed, ch):
        self.y = y
        self.x = x
        self.speed = speed
        self.ch = ch


class Game:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.player = Entity(h - 6, w // 2 - 2, PLAYER_SHAPE, 3)
        self.player.health = 3
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []
        self.stars = []
        self.score = 0
        self.level = 1
        self.wave_timer = 0
        self.wave_count = 0
        self.combo = 0
        self.combo_timer = 0
        self.powerup_timer = 0
        self.fire_mode = 0  # 0=single, 1=double, 2=triple
        self.fire_cooldown = 0
        self.game_over = False
        self.boss = None
        self.boss_timer = 0

        # Init stars
        for _ in range(50):
            self.stars.append(Star(
                random.randint(0, h),
                random.randint(0, w),
                random.uniform(0.2, 1.5),
                random.choice([".", "·", "*", "✦"])
            ))

    def spawn_wave(self):
        wave_type = random.choice(["line", "v", "circle", "random"])
        count = min(3 + self.level, 8)
        enemy_type = min(self.level // 3, 2)

        if wave_type == "line":
            spacing = self.w // (count + 1)
            for i in range(count):
                e = Entity(-3, spacing * (i + 1), ENEMY_SHAPES[enemy_type], 5)
                e.health = 1 + enemy_type
                e.vy = 0.3 + self.level * 0.05
                e.vx = 0
                self.enemies.append(e)
        elif wave_type == "v":
            for i in range(count):
                offset = abs(i - count // 2)
                e = Entity(-3 - offset * 2, self.w // 2 + (i - count // 2) * 6,
                          ENEMY_SHAPES[enemy_type], 5)
                e.health = 1 + enemy_type
                e.vy = 0.4
                e.vx = 0
                self.enemies.append(e)
        else:
            for _ in range(count):
                e = Entity(-3, random.randint(2, self.w - 8),
                          ENEMY_SHAPES[min(random.randint(0, enemy_type), 2)], 5)
                e.health = 1 + random.randint(0, enemy_type)
                e.vy = random.uniform(0.2, 0.5)
                e.vx = random.uniform(-0.3, 0.3)
                self.enemies.append(e)

        self.wave_count += 1
        if self.wave_count % 5 == 0 and not self.boss:
            self.spawn_boss()

    def spawn_boss(self):
        self.boss = Entity(-6, self.w // 2 - 5, BOSS_SHAPE, 1)
        self.boss.health = 20 + self.level * 5
        self.boss.max_health = self.boss.health
        self.boss.vy = 0.2
        self.boss.vx = 0.5
        self.boss.phase = 0
        self.boss_timer = 0

    def player_fire(self):
        if self.fire_cooldown > 0:
            return
        px, py = self.player.x + 2, self.player.y

        if self.fire_mode == 0:
            self.bullets.append(Bullet(py - 1, px, -1.5, 0, "│", 3))
        elif self.fire_mode == 1:
            self.bullets.append(Bullet(py - 1, px - 1, -1.5, 0, "│", 3))
            self.bullets.append(Bullet(py - 1, px + 1, -1.5, 0, "│", 3))
        else:
            self.bullets.append(Bullet(py - 1, px, -1.5, 0, "║", 4, 2))
            self.bullets.append(Bullet(py - 1, px - 2, -1.2, -0.2, "/", 3))
            self.bullets.append(Bullet(py - 1, px + 2, -1.2, 0.2, "\\", 3))

        self.fire_cooldown = 0.1

    def update(self, dt, keys):
        if self.game_over:
            return

        self.fire_cooldown = max(0, self.fire_cooldown - dt)
        self.combo_timer = max(0, self.combo_timer - dt)
        if self.combo_timer <= 0:
            self.combo = 0
        self.powerup_timer = max(0, self.powerup_timer - dt)
        if self.powerup_timer <= 0 and self.fire_mode > 0:
            self.fire_mode = max(0, self.fire_mode - 1)
            self.powerup_timer = 5

        # Player movement
        speed = 1.5
        if ord('a') in keys or curses.KEY_LEFT in keys:
            self.player.x = max(0, self.player.x - speed)
        if ord('d') in keys or curses.KEY_RIGHT in keys:
            self.player.x = min(self.w - 5, self.player.x + speed)
        if ord('w') in keys or curses.KEY_UP in keys:
            self.player.y = max(0, self.player.y - speed)
        if ord('s') in keys or curses.KEY_DOWN in keys:
            self.player.y = min(self.h - 6, self.player.y + speed)
        if ord(' ') in keys:
            self.player_fire()

        # Stars
        for star in self.stars:
            star.y += star.speed
            if star.y > self.h:
                star.y = 0
                star.x = random.randint(0, self.w)

        # Bullets
        for b in self.bullets:
            b.update()
            if b.y < -2 or b.y > self.h + 2 or b.x < -2 or b.x > self.w + 2:
                b.alive = False

        for b in self.enemy_bullets:
            b.update()
            if b.y > self.h + 2:
                b.alive = False

        # Enemies
        self.wave_timer += dt
        if self.wave_timer > max(2, 5 - self.level * 0.3) and len(self.enemies) < 15:
            self.wave_timer = 0
            self.spawn_wave()

        for e in self.enemies:
            e.y += getattr(e, 'vy', 0.3)
            e.x += getattr(e, 'vx', 0)
            if e.y > self.h + 5:
                e.alive = False
            # Random shooting
            if random.random() < 0.005 * self.level:
                self.enemy_bullets.append(Bullet(e.y + e.height, e.x + e.width // 2, 1, 0, "▼", 1))

        # Boss
        if self.boss and self.boss.alive:
            self.boss_timer += dt
            if self.boss.y < 2:
                self.boss.y += self.boss.vy
            else:
                self.boss.x += self.boss.vx
                if self.boss.x < 2 or self.boss.x > self.w - 12:
                    self.boss.vx *= -1

                # Boss attacks
                if random.random() < 0.03:
                    bx = self.boss.x + 5
                    by = self.boss.y + 4
                    # Spread shot
                    for angle in range(-30, 31, 15):
                        rad = math.radians(90 + angle)
                        self.enemy_bullets.append(
                            Bullet(by, bx, math.sin(rad) * 0.8, math.cos(rad) * 0.5, "●", 1)
                        )

        # Collisions: player bullets vs enemies
        for b in self.bullets:
            if not b.alive:
                continue
            for e in self.enemies:
                if not e.alive:
                    continue
                if (abs(b.y - e.y) < e.height + 1 and abs(b.x - e.x) < e.width + 1):
                    b.alive = False
                    e.health -= b.damage
                    if e.health <= 0:
                        e.alive = False
                        self.explosions.append(Explosion(e.y, e.x + e.width // 2))
                        self.combo += 1
                        self.combo_timer = 2
                        multiplier = min(self.combo, 8)
                        self.score += 100 * multiplier
                        if self.score % 2000 < 100:
                            self.fire_mode = min(2, self.fire_mode + 1)
                            self.powerup_timer = 10
                    break

            # Boss collision
            if self.boss and self.boss.alive:
                if (abs(b.y - self.boss.y) < 5 and abs(b.x - self.boss.x) < 11):
                    b.alive = False
                    self.boss.health -= b.damage
                    if self.boss.health <= 0:
                        self.boss.alive = False
                        for _ in range(5):
                            self.explosions.append(Explosion(
                                self.boss.y + random.randint(0, 4),
                                self.boss.x + random.randint(0, 10),
                                random.choice([4, 5, 1])
                            ))
                        self.score += 5000
                        self.level += 1
                        self.boss = None

        # Enemy bullets vs player
        for b in self.enemy_bullets:
            if not b.alive:
                continue
            if (abs(b.y - self.player.y) < 3 and abs(b.x - self.player.x) < 4):
                b.alive = False
                self.player.health -= 1
                self.explosions.append(Explosion(self.player.y, self.player.x + 2, 5))
                if self.player.health <= 0:
                    self.game_over = True

        # Enemy collision with player
        for e in self.enemies:
            if e.alive and e.collides(self.player):
                e.alive = False
                self.player.health -= 1
                self.explosions.append(Explosion(e.y, e.x))
                if self.player.health <= 0:
                    self.game_over = True

        # Update explosions
        for ex in self.explosions:
            ex.update(dt)

        # Cleanup
        self.bullets = [b for b in self.bullets if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        self.explosions = [e for e in self.explosions if e.alive]

    def draw(self, stdscr):
        h, w = self.h, self.w

        # Stars
        for star in self.stars:
            sy, sx = int(star.y), int(star.x)
            if 0 <= sy < h - 1 and 0 <= sx < w - 1:
                try:
                    dim = curses.A_DIM if star.speed < 0.8 else 0
                    stdscr.addstr(sy, sx, star.ch, curses.color_pair(8) | dim)
                except curses.error:
                    pass

        # Enemies
        for e in self.enemies:
            e.draw(stdscr, h, w)

        # Boss
        if self.boss and self.boss.alive:
            self.boss.draw(stdscr, h, w)
            # Boss health bar
            bar_w = 20
            bar_x = int(self.boss.x) - 4
            filled = int(bar_w * self.boss.health / self.boss.max_health)
            try:
                stdscr.addstr(int(self.boss.y) - 1, max(0, bar_x),
                             "█" * filled + "░" * (bar_w - filled),
                             curses.color_pair(1 if filled < bar_w // 3 else 4) | curses.A_BOLD)
            except curses.error:
                pass

        # Bullets
        for b in self.bullets:
            b.draw(stdscr, h, w)
        for b in self.enemy_bullets:
            b.draw(stdscr, h, w)

        # Player
        if self.player.alive and not self.game_over:
            self.player.draw(stdscr, h, w)

        # Explosions
        for ex in self.explosions:
            ex.draw(stdscr, h, w)

        # HUD
        try:
            hud = f" SCORE: {self.score} | LEVEL: {self.level} | "
            hud += "♥ " * self.player.health + "♡ " * (3 - self.player.health)
            if self.combo > 1:
                hud += f"| COMBO x{self.combo} "
            if self.fire_mode > 0:
                guns = ["", "DOUBLE", "TRIPLE"]
                hud += f"| {guns[self.fire_mode]} FIRE "
            stdscr.addstr(0, 0, hud[:w-1], curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)
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

    # Welcome screen
    stdscr.nodelay(False)
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    title = [
        "  ╔══════════════════════════╗  ",
        "  ║   🚀 SPACE SHOOTER 🚀   ║  ",
        "  ╠══════════════════════════╣  ",
        "  ║                          ║  ",
        "  ║   WASD / Arrows: Move    ║  ",
        "  ║   SPACE: Fire            ║  ",
        "  ║   Q: Quit                ║  ",
        "  ║                          ║  ",
        "  ║   Destroy enemies!       ║  ",
        "  ║   Build combos!          ║  ",
        "  ║   Defeat the boss!       ║  ",
        "  ║                          ║  ",
        "  ║   Press ENTER to start   ║  ",
        "  ╚══════════════════════════╝  ",
    ]

    start_y = (h - len(title)) // 2
    for i, line in enumerate(title):
        color = curses.color_pair(4) if i in (0, 2, 13) else curses.color_pair(3) if i == 1 else curses.color_pair(2)
        try:
            stdscr.addstr(start_y + i, (w - len(line)) // 2, line, color | curses.A_BOLD)
        except curses.error:
            pass
    stdscr.refresh()
    stdscr.getch()

    # Game loop
    stdscr.nodelay(True)
    game = Game(h, w)
    last_time = time.time()

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now

        # Collect all pressed keys
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
            stdscr.erase()
            game.draw(stdscr)
            go_text = [
                "╔═══════════════════╗",
                "║    GAME  OVER     ║",
                f"║  Score: {game.score:>8}  ║",
                f"║  Level: {game.level:>8}  ║",
                "╠═══════════════════╣",
                "║  R: Restart       ║",
                "║  Q: Quit          ║",
                "╚═══════════════════╝",
            ]
            gy = h // 2 - 4
            for i, line in enumerate(go_text):
                color = curses.color_pair(1) if i == 1 else curses.color_pair(4)
                try:
                    stdscr.addstr(gy + i, (w - len(line)) // 2, line, color | curses.A_BOLD)
                except curses.error:
                    pass
            stdscr.refresh()

            if ord('r') in keys or ord('R') in keys:
                game = Game(h, w)
            time.sleep(0.05)
            continue

        game.update(dt, keys)

        stdscr.erase()
        game.draw(stdscr)
        stdscr.refresh()

        time.sleep(0.016)


if __name__ == "__main__":
    curses.wrapper(main)
