#!/usr/bin/env python3
"""🌌 Terminal Galaxy - N-body gravitational simulation"""
import curses
import math
import random
import time

G = 0.5  # Gravitational constant (scaled for visual effect)


class Body:
    __slots__ = ['x', 'y', 'vx', 'vy', 'mass', 'color', 'char', 'trail']

    def __init__(self, x, y, vx, vy, mass, color=7, char='·'):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.mass = mass
        self.color = color
        self.char = char
        self.trail = []


def create_galaxy(cx, cy, num_stars, radius, rotation=1):
    """Create a spiral galaxy of orbiting stars."""
    bodies = []
    # Central massive body
    bodies.append(Body(cx, cy, 0, 0, 100, 3, '★'))

    for i in range(num_stars):
        angle = random.uniform(0, math.pi * 2)
        r = random.uniform(3, radius)
        # Spiral offset
        spiral_angle = angle + r * 0.1 * rotation
        x = cx + math.cos(spiral_angle) * r * 2  # *2 for aspect ratio
        y = cy + math.sin(spiral_angle) * r

        # Orbital velocity
        speed = math.sqrt(G * 100 / max(1, r)) * 0.5
        vx = -math.sin(spiral_angle) * speed * rotation * 2
        vy = math.cos(spiral_angle) * speed * rotation

        # Add some randomness
        vx += random.gauss(0, 0.02)
        vy += random.gauss(0, 0.01)

        mass = random.uniform(0.1, 1)
        color = random.choice([7, 4, 3, 6]) if r < radius * 0.5 else random.choice([7, 8, 6])
        char = random.choice(['·', '•', '∗', '*']) if mass < 0.5 else random.choice(['●', '★', '◆'])

        bodies.append(Body(x, y, vx, vy, mass, color, char))

    return bodies


def create_binary_system(cx, cy, num_stars):
    """Two massive bodies orbiting each other with stars."""
    bodies = []
    sep = 15

    # Binary pair
    speed = math.sqrt(G * 50 / sep) * 0.3
    bodies.append(Body(cx - sep, cy, 0, speed, 50, 3, '★'))
    bodies.append(Body(cx + sep, cy, 0, -speed, 50, 1, '★'))

    for _ in range(num_stars):
        angle = random.uniform(0, math.pi * 2)
        r = random.uniform(5, 30)
        x = cx + math.cos(angle) * r * 2
        y = cy + math.sin(angle) * r
        speed = math.sqrt(G * 100 / max(1, r)) * 0.3
        vx = -math.sin(angle) * speed * 2
        vy = math.cos(angle) * speed
        vx += random.gauss(0, 0.03)
        vy += random.gauss(0, 0.015)
        bodies.append(Body(x, y, vx, vy, random.uniform(0.1, 0.5),
                          random.choice([7, 4, 6]), random.choice(['·', '•', '*'])))

    return bodies


def create_collision(cx, cy, num_stars):
    """Two galaxies on collision course."""
    bodies = []
    g1 = create_galaxy(cx - 20, cy - 5, num_stars // 2, 10, 1)
    g2 = create_galaxy(cx + 20, cy + 5, num_stars // 2, 10, -1)

    # Give them velocity toward each other
    for b in g1:
        b.vx += 0.15
        b.vy += 0.03
    for b in g2:
        b.vx -= 0.15
        b.vy -= 0.03
        b.color = random.choice([1, 5]) if b.mass > 10 else b.color

    bodies.extend(g1)
    bodies.extend(g2)
    return bodies


SCENARIOS = [
    ("Spiral Galaxy", lambda h, w: create_galaxy(w//2, h//2, 150, min(h, w)//3)),
    ("Binary System", lambda h, w: create_binary_system(w//2, h//2, 100)),
    ("Galaxy Collision", lambda h, w: create_collision(w//2, h//2, 120)),
]


def update_bodies(bodies, dt, softening=1.0):
    """Update positions and velocities using gravitational forces."""
    n = len(bodies)

    # Only compute forces from massive bodies for performance
    massive = [b for b in bodies if b.mass > 10]

    for i in range(n):
        bi = bodies[i]
        ax, ay = 0, 0

        for bj in massive:
            if bi is bj:
                continue
            dx = bj.x - bi.x
            dy = (bj.y - bi.y) * 2  # Correct for aspect ratio
            dist_sq = dx * dx + dy * dy + softening
            dist = math.sqrt(dist_sq)
            force = G * bj.mass / dist_sq
            ax += force * dx / dist
            ay += force * dy / dist * 0.5  # Correct back

        bi.vx += ax * dt
        bi.vy += ay * dt

    for b in bodies:
        b.x += b.vx * dt * 20
        b.y += b.vy * dt * 20

        # Trail
        b.trail.append((b.x, b.y))
        if len(b.trail) > 8:
            b.trail.pop(0)


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
    scenario_idx = 0
    bodies = SCENARIOS[scenario_idx][1](h - 2, w)

    last_time = time.time()
    time_scale = 1.0
    show_trails = True
    paused = False

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
            paused = not paused
        elif key == ord('s') or key == ord('S'):
            scenario_idx = (scenario_idx + 1) % len(SCENARIOS)
            h, w = stdscr.getmaxyx()
            bodies = SCENARIOS[scenario_idx][1](h - 2, w)
        elif key == ord('t') or key == ord('T'):
            show_trails = not show_trails
        elif key == ord('+') or key == ord('='):
            time_scale = min(5.0, time_scale + 0.2)
        elif key == ord('-'):
            time_scale = max(0.1, time_scale - 0.2)
        elif key == ord('r') or key == ord('R'):
            bodies = SCENARIOS[scenario_idx][1](h - 2, w)

        h, w = stdscr.getmaxyx()

        if not paused:
            update_bodies(bodies, dt * time_scale)

        # Remove escaped bodies
        bodies = [b for b in bodies if -w < b.x < w * 2 and -h < b.y < h * 2]

        stdscr.erase()

        # Draw trails
        if show_trails:
            for b in bodies:
                for i, (tx, ty) in enumerate(b.trail[:-1]):
                    ix, iy = int(tx), int(ty)
                    if 0 <= iy < h - 1 and 0 <= ix < w - 1:
                        try:
                            stdscr.addstr(iy, ix, "·", curses.color_pair(8) | curses.A_DIM)
                        except curses.error:
                            pass

        # Draw bodies
        for b in bodies:
            bx, by = int(b.x), int(b.y)
            if 0 <= by < h - 1 and 0 <= bx < w - 1:
                try:
                    attr = curses.A_BOLD if b.mass > 10 else 0
                    stdscr.addstr(by, bx, b.char, curses.color_pair(b.color) | attr)
                except curses.error:
                    pass

        # Status
        name = SCENARIOS[scenario_idx][0]
        try:
            status = f" 🌌 {name} | Bodies: {len(bodies)} | Speed: {time_scale:.1f}x | {'PAUSED' if paused else 'RUNNING'} | S:Scenario T:Trails R:Reset Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.03)


if __name__ == "__main__":
    curses.wrapper(main)
