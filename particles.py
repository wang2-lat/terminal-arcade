#!/usr/bin/env python3
"""🐉 Terminal Particle System - Fire, Fireworks, Starfield & More!"""
import curses
import math
import random
import time


class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'char', 'color', 'gravity']

    def __init__(self, x, y, vx, vy, life, char='*', color=4, gravity=0.05):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.char = char
        self.color = color
        self.gravity = gravity

    def update(self, dt):
        self.x += self.vx * dt * 30
        self.y += self.vy * dt * 30
        self.vy += self.gravity * dt * 30
        self.life -= dt
        return self.life > 0


class ParticleSystem:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.particles = []
        self.max_particles = 2000

    def emit(self, particle):
        if len(self.particles) < self.max_particles:
            self.particles.append(particle)

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, stdscr):
        for p in self.particles:
            px, py = int(p.x), int(p.y)
            if 0 <= py < self.h - 1 and 0 <= px < self.w - 1:
                # Fade based on remaining life
                ratio = p.life / p.max_life
                if ratio > 0.7:
                    attr = curses.A_BOLD
                elif ratio > 0.3:
                    attr = 0
                else:
                    attr = curses.A_DIM

                try:
                    stdscr.addstr(py, px, p.char, curses.color_pair(p.color) | attr)
                except curses.error:
                    pass


def emit_fire(ps, cx, cy):
    """Emit fire particles from a source point."""
    for _ in range(5):
        spread = random.gauss(0, 1.5)
        ps.emit(Particle(
            cx + spread, cy,
            spread * 0.05,
            random.uniform(-0.3, -0.1),
            random.uniform(0.5, 2.0),
            random.choice(['█', '▓', '▒', '░', '∗', '·']),
            random.choice([5, 5, 4, 4, 4, 1]),  # red, yellow
            gravity=-0.02
        ))


def emit_firework(ps, cx, cy, color=None):
    """Emit a firework explosion."""
    if color is None:
        color = random.choice([1, 2, 3, 4, 5, 6])
    num = random.randint(40, 80)
    for _ in range(num):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(0.1, 0.5)
        ps.emit(Particle(
            cx, cy,
            math.cos(angle) * speed * 2,  # wider horizontally
            math.sin(angle) * speed,
            random.uniform(1.0, 3.0),
            random.choice(['✦', '✧', '*', '●', '◆', '♦']),
            color,
            gravity=0.01
        ))
    # Crackle
    for _ in range(20):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(0.05, 0.15)
        ps.emit(Particle(
            cx, cy,
            math.cos(angle) * speed * 2,
            math.sin(angle) * speed,
            random.uniform(0.3, 0.8),
            '·',
            7,
            gravity=0.005
        ))


def emit_rain(ps, w):
    """Emit rain drops from top."""
    for _ in range(3):
        ps.emit(Particle(
            random.uniform(0, w), 0,
            random.uniform(-0.02, 0.02),
            random.uniform(0.3, 0.6),
            random.uniform(2, 5),
            random.choice(['│', '|', '╎', ':']),
            6,  # blue
            gravity=0.01
        ))


def emit_snow(ps, w):
    """Emit snowflakes from top."""
    for _ in range(2):
        ps.emit(Particle(
            random.uniform(0, w), 0,
            random.uniform(-0.05, 0.05),
            random.uniform(0.05, 0.15),
            random.uniform(5, 12),
            random.choice(['❄', '❆', '✻', '*', '·']),
            7,  # white
            gravity=0
        ))


def emit_matrix(ps, w):
    """Matrix-style falling characters."""
    if random.random() < 0.3:
        x = random.randint(0, w - 1)
        trail_len = random.randint(5, 15)
        for i in range(trail_len):
            ps.emit(Particle(
                x, -i,
                0,
                random.uniform(0.15, 0.4),
                random.uniform(2, 6) + i * 0.3,
                random.choice(list("01アイウエオカキクケコサシスセソ")),
                3 if i == 0 else 3,  # green
                gravity=0
            ))


def emit_galaxy(ps, cx, cy, t):
    """Emit spiral galaxy particles."""
    for arm in range(2):
        base_angle = arm * math.pi + t * 0.5
        for i in range(3):
            angle = base_angle + i * 0.3 + random.gauss(0, 0.2)
            r = 3 + i * 2 + random.gauss(0, 1)
            x = cx + math.cos(angle) * r * 2
            y = cy + math.sin(angle) * r
            ps.emit(Particle(
                x, y,
                -math.sin(angle) * 0.02,
                math.cos(angle) * 0.01,
                random.uniform(1, 3),
                random.choice(['✦', '·', '*', '○']),
                random.choice([7, 2, 4, 6]),
                gravity=0
            ))


MODES = ["🔥 FIRE", "🎆 FIREWORKS", "🌧️ RAIN", "❄️ SNOW", "💚 MATRIX", "🌌 GALAXY"]


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    ps = ParticleSystem(h, w)
    mode = 0
    t = 0
    last_time = time.time()
    firework_timer = 0

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
        elif key == ord('m') or key == ord('M'):
            mode = (mode + 1) % len(MODES)
            ps.particles.clear()
        elif key == ord(' '):
            # Manual firework at random position
            emit_firework(ps, random.randint(10, w - 10), random.randint(3, h // 2))

        h, w = stdscr.getmaxyx()
        ps.h = h
        ps.w = w

        cx, cy = w // 2, h // 2

        # Emit based on mode
        if mode == 0:  # Fire
            fire_y = h - 5
            for fx in range(cx - 8, cx + 8, 2):
                emit_fire(ps, fx, fire_y)
            # Extra embers
            if random.random() < 0.3:
                ps.emit(Particle(
                    cx + random.gauss(0, 3), fire_y - random.randint(0, 5),
                    random.gauss(0, 0.1), random.uniform(-0.4, -0.2),
                    random.uniform(2, 4), '✦', 4, gravity=-0.005
                ))

        elif mode == 1:  # Fireworks
            firework_timer += dt
            if firework_timer > random.uniform(0.3, 1.5):
                firework_timer = 0
                emit_firework(ps,
                    random.randint(10, w - 10),
                    random.randint(3, h * 2 // 3))

        elif mode == 2:  # Rain
            emit_rain(ps, w)
            # Lightning
            if random.random() < 0.002:
                for _ in range(50):
                    ps.emit(Particle(
                        random.randint(0, w), random.randint(0, h),
                        0, 0, 0.1, '█', 7, gravity=0
                    ))

        elif mode == 3:  # Snow
            emit_snow(ps, w)
            # Wind gusts
            if random.random() < 0.01:
                for p in ps.particles:
                    p.vx += random.gauss(0, 0.03)

        elif mode == 4:  # Matrix
            emit_matrix(ps, w)

        elif mode == 5:  # Galaxy
            emit_galaxy(ps, cx, cy, t)

        ps.update(dt)

        stdscr.erase()
        ps.draw(stdscr)

        # Status
        try:
            status = f" {MODES[mode]} | Particles: {len(ps.particles)} | M:Mode SPACE:Firework Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.025)


if __name__ == "__main__":
    curses.wrapper(main)
