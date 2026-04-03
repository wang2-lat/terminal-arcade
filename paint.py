#!/usr/bin/env python3
"""🎨 Terminal Paint - Draw ASCII art with your keyboard!"""
import curses
import json
import os

BRUSHES = ['█', '▓', '▒', '░', '●', '○', '◆', '◇', '★', '✦', '♥', '#', '*', '.', '~']
COLORS = [1, 2, 3, 4, 5, 6, 7]
COLOR_NAMES = ["Red", "Green", "Yellow", "Cyan", "Magenta", "Blue", "White"]


class Canvas:
    def __init__(self, h, w):
        self.h = h
        self.w = w
        self.pixels = {}  # (y, x) -> (char, color)
        self.cursor_x = w // 2
        self.cursor_y = h // 2
        self.brush_idx = 0
        self.color_idx = 6  # white
        self.drawing = False
        self.undo_stack = []
        self.redo_stack = []

    @property
    def brush(self):
        return BRUSHES[self.brush_idx]

    @property
    def color(self):
        return COLORS[self.color_idx]

    def put_pixel(self):
        key = (self.cursor_y, self.cursor_x)
        old = self.pixels.get(key)
        self.undo_stack.append((key, old))
        self.redo_stack.clear()
        self.pixels[key] = (self.brush, self.color)

    def erase_pixel(self):
        key = (self.cursor_y, self.cursor_x)
        if key in self.pixels:
            old = self.pixels[key]
            self.undo_stack.append((key, old))
            self.redo_stack.clear()
            del self.pixels[key]

    def undo(self):
        if self.undo_stack:
            key, old = self.undo_stack.pop()
            current = self.pixels.get(key)
            self.redo_stack.append((key, current))
            if old:
                self.pixels[key] = old
            elif key in self.pixels:
                del self.pixels[key]

    def redo(self):
        if self.redo_stack:
            key, val = self.redo_stack.pop()
            current = self.pixels.get(key)
            self.undo_stack.append((key, current))
            if val:
                self.pixels[key] = val
            elif key in self.pixels:
                del self.pixels[key]

    def clear(self):
        self.undo_stack.append(("CLEAR", dict(self.pixels)))
        self.pixels.clear()

    def fill(self, y, x, target_char=None):
        """Flood fill from position."""
        target = self.pixels.get((y, x))
        if target and target == (self.brush, self.color):
            return
        stack = [(y, x)]
        visited = set()
        while stack:
            cy, cx = stack.pop()
            if (cy, cx) in visited:
                continue
            visited.add((cy, cx))
            current = self.pixels.get((cy, cx))
            if current != target:
                continue
            self.pixels[(cy, cx)] = (self.brush, self.color)
            for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < self.h - 2 and 0 <= nx < self.w:
                    stack.append((ny, nx))

    def export_txt(self, filename):
        lines = []
        for y in range(self.h - 2):
            line = ""
            for x in range(self.w):
                if (y, x) in self.pixels:
                    line += self.pixels[(y, x)][0]
                else:
                    line += " "
            lines.append(line.rstrip())
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()
        with open(filename, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        return filename

    def save_json(self, filename):
        data = {
            "w": self.w, "h": self.h,
            "pixels": {f"{y},{x}": [ch, c] for (y, x), (ch, c) in self.pixels.items()}
        }
        with open(filename, 'w') as f:
            json.dump(data, f)
        return filename

    def load_json(self, filename):
        with open(filename) as f:
            data = json.load(f)
        self.pixels.clear()
        for key, (ch, c) in data["pixels"].items():
            y, x = map(int, key.split(','))
            self.pixels[(y, x)] = (ch, c)


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

    h, w = stdscr.getmaxyx()
    canvas = Canvas(h, w)
    message = ""
    msg_timer = 0

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Draw canvas
        for (y, x), (ch, color) in canvas.pixels.items():
            if 0 <= y < h - 2 and 0 <= x < w:
                try:
                    stdscr.addstr(y, x, ch, curses.color_pair(color))
                except curses.error:
                    pass

        # Draw cursor
        cy, cx = canvas.cursor_y, canvas.cursor_x
        if 0 <= cy < h - 2 and 0 <= cx < w:
            try:
                if canvas.drawing:
                    stdscr.addstr(cy, cx, canvas.brush, curses.color_pair(canvas.color) | curses.A_BLINK)
                else:
                    existing = canvas.pixels.get((cy, cx))
                    if existing:
                        stdscr.addstr(cy, cx, existing[0], curses.color_pair(existing[1]) | curses.A_REVERSE)
                    else:
                        stdscr.addstr(cy, cx, "+", curses.color_pair(canvas.color) | curses.A_BLINK)
            except curses.error:
                pass

        # Status bar
        try:
            color_name = COLOR_NAMES[canvas.color_idx]
            status = (f" Brush: {canvas.brush} | Color: {color_name} | "
                     f"Pos: ({cx},{cy}) | Pixels: {len(canvas.pixels)} | "
                     f"{'DRAWING' if canvas.drawing else 'MOVE'} ")
            stdscr.addstr(h - 2, 0, "═" * (w - 1), curses.color_pair(3))
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))

            # Brush preview
            brush_x = w - 20
            if brush_x > 0:
                for i, b in enumerate(BRUSHES):
                    bx = brush_x + i
                    if bx < w - 1:
                        attr = curses.A_REVERSE if i == canvas.brush_idx else 0
                        stdscr.addstr(h - 2, bx, b, curses.color_pair(canvas.color) | attr)
        except curses.error:
            pass

        # Message
        if message and msg_timer > 0:
            draw_centered(stdscr, 0, f" {message} ", curses.color_pair(2) | curses.A_BOLD)
            msg_timer -= 1

        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            break
        elif key == curses.KEY_UP:
            canvas.cursor_y = max(0, canvas.cursor_y - 1)
            if canvas.drawing:
                canvas.put_pixel()
        elif key == curses.KEY_DOWN:
            canvas.cursor_y = min(h - 3, canvas.cursor_y + 1)
            if canvas.drawing:
                canvas.put_pixel()
        elif key == curses.KEY_LEFT:
            canvas.cursor_x = max(0, canvas.cursor_x - 1)
            if canvas.drawing:
                canvas.put_pixel()
        elif key == curses.KEY_RIGHT:
            canvas.cursor_x = min(w - 1, canvas.cursor_x + 1)
            if canvas.drawing:
                canvas.put_pixel()
        elif key == ord(' '):
            canvas.put_pixel()
        elif key == ord('d') or key == ord('D'):
            canvas.drawing = not canvas.drawing
            if canvas.drawing:
                canvas.put_pixel()
        elif key == ord('e') or key == ord('E'):
            canvas.erase_pixel()
        elif key == ord('b') or key == ord('B'):
            canvas.brush_idx = (canvas.brush_idx + 1) % len(BRUSHES)
        elif key == ord('c') or key == ord('C'):
            canvas.color_idx = (canvas.color_idx + 1) % len(COLORS)
        elif key == ord('z') or key == ord('Z'):
            canvas.undo()
        elif key == ord('y') or key == ord('Y'):
            canvas.redo()
        elif key == ord('x') or key == ord('X'):
            canvas.clear()
            message = "Canvas cleared"
            msg_timer = 30
        elif key == ord('s') or key == ord('S'):
            fname = os.path.expanduser("~/fun-projects/drawing.txt")
            canvas.export_txt(fname)
            message = f"Saved to {fname}"
            msg_timer = 60
        elif key == ord('f') or key == ord('F'):
            canvas.fill(canvas.cursor_y, canvas.cursor_x)

    # Auto-save on exit
    if canvas.pixels:
        canvas.export_txt(os.path.expanduser("~/fun-projects/last_drawing.txt"))


if __name__ == "__main__":
    curses.wrapper(main)
