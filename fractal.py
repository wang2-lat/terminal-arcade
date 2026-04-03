#!/usr/bin/env python3
"""🌀 Terminal Fractal Explorer - Mandelbrot & Julia sets in ASCII"""
import curses
import time
import math

CHAR_SETS = {
    "ascii": " .:-=+*#%@█",
    "blocks": " ░▒▓█",
    "dots": " ·•●◉█",
    "fancy": " ·∙•◦○◎●◉█",
}


def mandelbrot(c_real, c_imag, max_iter):
    z_real, z_imag = 0, 0
    for i in range(max_iter):
        if z_real * z_real + z_imag * z_imag > 4:
            return i
        z_real, z_imag = z_real * z_real - z_imag * z_imag + c_real, 2 * z_real * z_imag + c_imag
    return max_iter


def julia(z_real, z_imag, c_real, c_imag, max_iter):
    for i in range(max_iter):
        if z_real * z_real + z_imag * z_imag > 4:
            return i
        z_real, z_imag = z_real * z_real - z_imag * z_imag + c_real, 2 * z_real * z_imag + c_imag
    return max_iter


def get_color(iterations, max_iter):
    if iterations >= max_iter:
        return 0, 0  # Inside set - black
    ratio = iterations / max_iter
    # Color cycling
    hue = ratio * 6
    color_idx = int(hue) % 7 + 1
    bold = curses.A_BOLD if ratio > 0.3 else 0
    return color_idx, bold


JULIA_PARAMS = [
    (-0.7, 0.27015, "Classic Julia"),
    (-0.4, 0.6, "Dendrite"),
    (0.285, 0.01, "Spiral"),
    (-0.8, 0.156, "Sea Horse"),
    (-0.75, 0.11, "Rabbit"),
    (0.355, 0.355, "Siegel Disk"),
    (-0.1, 0.651, "Flower"),
]

INTERESTING_LOCATIONS = [
    (-0.5, 0, 3.0, "Full View"),
    (-0.745, 0.186, 0.01, "Seahorse Valley"),
    (-0.16, 1.0405, 0.026, "Satellite"),
    (-1.25066, 0.02012, 0.0001, "Deep Zoom"),
    (0.001643721971153, 0.822467633298876, 0.0000001, "Ultra Deep"),
    (-0.77568377, 0.13646737, 0.000004, "Mini Mandelbrot"),
]


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
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

    stdscr.keypad(True)

    # State
    mode = "mandelbrot"  # or "julia"
    center_x = -0.5
    center_y = 0
    zoom = 3.0
    max_iter = 50
    charset_name = "ascii"
    julia_idx = 0
    location_idx = 0
    needs_render = True
    color_mode = True
    auto_zoom = False
    auto_target_x = -0.745
    auto_target_y = 0.186

    while True:
        h, w = stdscr.getmaxyx()

        if needs_render:
            stdscr.erase()
            chars = CHAR_SETS[charset_name]
            render_h = h - 2
            render_w = w - 1
            aspect = 2.0  # Terminal chars are ~2x tall as wide

            for sy in range(render_h):
                for sx in range(render_w):
                    # Map screen to complex plane
                    real = center_x + (sx - render_w / 2) / render_w * zoom * aspect
                    imag = center_y + (sy - render_h / 2) / render_h * zoom

                    if mode == "mandelbrot":
                        iterations = mandelbrot(real, imag, max_iter)
                    else:
                        jr, ji = JULIA_PARAMS[julia_idx][0], JULIA_PARAMS[julia_idx][1]
                        iterations = julia(real, imag, jr, ji, max_iter)

                    if iterations >= max_iter:
                        continue  # Skip inside-set points

                    char_idx = int(iterations / max_iter * (len(chars) - 1))
                    char_idx = max(0, min(len(chars) - 1, char_idx))
                    ch = chars[char_idx]

                    if color_mode:
                        color, bold = get_color(iterations, max_iter)
                        attr = curses.color_pair(color) | bold
                    else:
                        attr = curses.color_pair(7)

                    try:
                        stdscr.addstr(sy, sx, ch, attr)
                    except curses.error:
                        pass

            # Status bar
            if mode == "mandelbrot":
                info = f"Mandelbrot | Center: ({center_x:.6f}, {center_y:.6f}) | Zoom: {3/zoom:.1f}x"
            else:
                jname = JULIA_PARAMS[julia_idx][2]
                info = f"Julia [{jname}] | c=({JULIA_PARAMS[julia_idx][0]}, {JULIA_PARAMS[julia_idx][1]})"

            status = f" 🌀 {info} | Iter:{max_iter} | {charset_name} "
            try:
                stdscr.addstr(h - 2, 0, "═" * (w - 1), curses.color_pair(3))
                stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
            except curses.error:
                pass

            controls = "Arrows:Pan Z/X:Zoom I/O:Iter M:Mode J:Julia L:Location C:Chars K:Color Q:Quit"
            try:
                stdscr.addstr(h - 1, max(0, w - len(controls) - 1), controls[:w-1], curses.color_pair(8))
            except curses.error:
                pass

            stdscr.refresh()
            needs_render = False

        if auto_zoom:
            zoom *= 0.97
            center_x += (auto_target_x - center_x) * 0.02
            center_y += (auto_target_y - center_y) * 0.02
            max_iter = min(200, int(50 + 30 * math.log10(3 / zoom + 1)))
            needs_render = True
            time.sleep(0.03)
            try:
                key = stdscr.getch()
                if key != -1:
                    auto_zoom = False
                    continue
            except:
                pass
            continue

        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            break
        elif key == curses.KEY_LEFT:
            center_x -= zoom * 0.1
            needs_render = True
        elif key == curses.KEY_RIGHT:
            center_x += zoom * 0.1
            needs_render = True
        elif key == curses.KEY_UP:
            center_y -= zoom * 0.1
            needs_render = True
        elif key == curses.KEY_DOWN:
            center_y += zoom * 0.1
            needs_render = True
        elif key in (ord('z'), ord('Z')):
            zoom *= 0.7
            max_iter = min(200, max_iter + 5)
            needs_render = True
        elif key in (ord('x'), ord('X')):
            zoom *= 1.4
            max_iter = max(20, max_iter - 5)
            needs_render = True
        elif key in (ord('i'), ord('I')):
            max_iter = min(500, max_iter + 10)
            needs_render = True
        elif key in (ord('o'), ord('O')):
            max_iter = max(10, max_iter - 10)
            needs_render = True
        elif key in (ord('m'), ord('M')):
            mode = "julia" if mode == "mandelbrot" else "mandelbrot"
            if mode == "mandelbrot":
                center_x, center_y, zoom = -0.5, 0, 3.0
            else:
                center_x, center_y, zoom = 0, 0, 3.0
            max_iter = 50
            needs_render = True
        elif key in (ord('j'), ord('J')):
            julia_idx = (julia_idx + 1) % len(JULIA_PARAMS)
            needs_render = True
        elif key in (ord('l'), ord('L')):
            location_idx = (location_idx + 1) % len(INTERESTING_LOCATIONS)
            loc = INTERESTING_LOCATIONS[location_idx]
            center_x, center_y, zoom = loc[0], loc[1], loc[2]
            max_iter = min(200, int(50 + 30 * math.log10(3 / zoom + 1)))
            mode = "mandelbrot"
            needs_render = True
        elif key in (ord('c'), ord('C')):
            names = list(CHAR_SETS.keys())
            idx = names.index(charset_name)
            charset_name = names[(idx + 1) % len(names)]
            needs_render = True
        elif key in (ord('k'), ord('K')):
            color_mode = not color_mode
            needs_render = True
        elif key in (ord('a'), ord('A')):
            auto_zoom = True
            loc = INTERESTING_LOCATIONS[location_idx]
            auto_target_x, auto_target_y = loc[0], loc[1]
        elif key == ord('r') or key == ord('R'):
            center_x, center_y, zoom = -0.5, 0, 3.0
            max_iter = 50
            needs_render = True

        time.sleep(0.02)


if __name__ == "__main__":
    curses.wrapper(main)
