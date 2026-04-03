#!/usr/bin/env python3
"""🧊 Terminal 3D Rotating Cube - Wireframe cube spinning in ASCII"""
import curses
import math
import time

# Cube vertices
VERTICES = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
]

EDGES = [
    (0,1),(1,2),(2,3),(3,0),  # back face
    (4,5),(5,6),(6,7),(7,4),  # front face
    (0,4),(1,5),(2,6),(3,7),  # connecting
]

# Additional shapes
PYRAMID = [
    (0, 1, 0),    # top
    (-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1),  # base
]
PYRAMID_EDGES = [(0,1),(0,2),(0,3),(0,4),(1,2),(2,3),(3,4),(4,1)]

OCTAHEDRON = [
    (0, 1, 0), (0, -1, 0),  # top, bottom
    (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1),
]
OCTA_EDGES = [
    (0,2),(0,3),(0,4),(0,5),
    (1,2),(1,3),(1,4),(1,5),
    (2,4),(4,3),(3,5),(5,2),
]

SHAPES = [
    ("Cube", VERTICES, EDGES),
    ("Pyramid", PYRAMID, PYRAMID_EDGES),
    ("Octahedron", OCTAHEDRON, OCTA_EDGES),
]


def rotate_x(v, a):
    y = v[1] * math.cos(a) - v[2] * math.sin(a)
    z = v[1] * math.sin(a) + v[2] * math.cos(a)
    return (v[0], y, z)


def rotate_y(v, a):
    x = v[0] * math.cos(a) + v[2] * math.sin(a)
    z = -v[0] * math.sin(a) + v[2] * math.cos(a)
    return (x, v[1], z)


def rotate_z(v, a):
    x = v[0] * math.cos(a) - v[1] * math.sin(a)
    y = v[0] * math.sin(a) + v[1] * math.cos(a)
    return (x, y, v[2])


def project(v, cx, cy, scale, dist=5):
    """Perspective projection."""
    z = v[2] + dist
    if z <= 0.1:
        z = 0.1
    x = int(cx + v[0] / z * scale * 2)  # *2 for aspect ratio
    y = int(cy - v[1] / z * scale)
    return x, y, z


def draw_line(stdscr, x0, y0, x1, y1, h, w, char, color):
    """Bresenham's line algorithm."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if 0 <= y0 < h - 1 and 0 <= x0 < w - 1:
            try:
                stdscr.addstr(y0, x0, char, curses.color_pair(color))
            except curses.error:
                pass
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


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

    t = 0
    shape_idx = 0
    speed = 1.0
    auto_rotate = True
    rx, ry, rz = 0, 0, 0
    show_vertices = True
    show_faces = False
    last_time = time.time()
    edge_colors = [1, 2, 3, 4, 5, 6, 7]

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now
        t += dt * speed

        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord('s') or key == ord('S'):
            shape_idx = (shape_idx + 1) % len(SHAPES)
        elif key == ord('+') or key == ord('='):
            speed = min(5, speed + 0.2)
        elif key == ord('-'):
            speed = max(0.1, speed - 0.2)
        elif key == ord('v') or key == ord('V'):
            show_vertices = not show_vertices
        elif key == ord(' '):
            auto_rotate = not auto_rotate

        h, w = stdscr.getmaxyx()
        cx, cy = w // 2, (h - 2) // 2
        scale = min(h, w // 2) * 0.8

        name, vertices, edges = SHAPES[shape_idx]

        if auto_rotate:
            rx = t * 0.7
            ry = t * 1.0
            rz = t * 0.3

        # Transform vertices
        projected = []
        for v in vertices:
            rv = rotate_x(v, rx)
            rv = rotate_y(rv, ry)
            rv = rotate_z(rv, rz)
            px, py, pz = project(rv, cx, cy, scale)
            projected.append((px, py, pz))

        stdscr.erase()

        # Sort edges by average depth for painter's algorithm
        edge_depths = []
        for i, (a, b) in enumerate(edges):
            avg_z = (projected[a][2] + projected[b][2]) / 2
            edge_depths.append((avg_z, i))
        edge_depths.sort(reverse=True)

        # Draw edges
        for depth, ei in edge_depths:
            a, b = edges[ei]
            x0, y0, z0 = projected[a]
            x1, y1, z1 = projected[b]
            avg_z = (z0 + z1) / 2

            color = edge_colors[ei % len(edge_colors)]
            if avg_z > 5.5:
                char = "█"
                attr = curses.A_BOLD
            elif avg_z > 4.5:
                char = "▓"
                attr = 0
            else:
                char = "░"
                attr = curses.A_DIM

            draw_line(stdscr, x0, y0, x1, y1, h, w, char, color)

        # Draw vertices
        if show_vertices:
            for i, (px, py, pz) in enumerate(projected):
                if 0 <= py < h - 1 and 0 <= px < w - 1:
                    try:
                        attr = curses.A_BOLD if pz > 5 else 0
                        stdscr.addstr(py, px, "◉", curses.color_pair(7) | attr)
                    except curses.error:
                        pass

        # Status
        try:
            status = f" 🧊 {name} | Speed:{speed:.1f}x | S:Shape V:Vertices SPACE:Pause +/-:Speed Q:Quit "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.03)


if __name__ == "__main__":
    curses.wrapper(main)
