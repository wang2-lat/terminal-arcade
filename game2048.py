#!/usr/bin/env python3
"""🎮 Terminal 2048 - The classic number merging puzzle!"""
import curses
import random
import copy
import json
import os

SCORE_FILE = os.path.expanduser("~/.game2048_best.json")

TILE_COLORS = {
    0: (0, 0),
    2: (7, 0),
    4: (7, curses.A_BOLD),
    8: (4, curses.A_BOLD),
    16: (4, curses.A_BOLD),
    32: (1, curses.A_BOLD),
    64: (1, curses.A_BOLD),
    128: (3, curses.A_BOLD),
    256: (3, curses.A_BOLD),
    512: (5, curses.A_BOLD),
    1024: (5, curses.A_BOLD),
    2048: (2, curses.A_BOLD),
}


class Game2048:
    def __init__(self, size=4):
        self.size = size
        self.board = [[0] * size for _ in range(size)]
        self.score = 0
        self.best_score = self._load_best()
        self.won = False
        self.game_over = False
        self.add_tile()
        self.add_tile()

    def _load_best(self):
        try:
            with open(SCORE_FILE) as f:
                return json.load(f).get("best", 0)
        except:
            return 0

    def _save_best(self):
        if self.score > self.best_score:
            self.best_score = self.score
            with open(SCORE_FILE, "w") as f:
                json.dump({"best": self.best_score}, f)

    def add_tile(self):
        empty = [(r, c) for r in range(self.size) for c in range(self.size) if self.board[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.board[r][c] = 4 if random.random() < 0.1 else 2

    def slide_row_left(self, row):
        new = [x for x in row if x != 0]
        merged = []
        score_add = 0
        i = 0
        while i < len(new):
            if i + 1 < len(new) and new[i] == new[i + 1]:
                val = new[i] * 2
                merged.append(val)
                score_add += val
                if val == 2048:
                    self.won = True
                i += 2
            else:
                merged.append(new[i])
                i += 1
        merged += [0] * (self.size - len(merged))
        return merged, score_add

    def move(self, direction):
        old_board = copy.deepcopy(self.board)
        total_score = 0

        if direction == "left":
            for r in range(self.size):
                self.board[r], s = self.slide_row_left(self.board[r])
                total_score += s
        elif direction == "right":
            for r in range(self.size):
                self.board[r], s = self.slide_row_left(self.board[r][::-1])
                self.board[r] = self.board[r][::-1]
                total_score += s
        elif direction == "up":
            for c in range(self.size):
                col = [self.board[r][c] for r in range(self.size)]
                new_col, s = self.slide_row_left(col)
                total_score += s
                for r in range(self.size):
                    self.board[r][c] = new_col[r]
        elif direction == "down":
            for c in range(self.size):
                col = [self.board[r][c] for r in range(self.size)][::-1]
                new_col, s = self.slide_row_left(col)
                new_col = new_col[::-1]
                total_score += s
                for r in range(self.size):
                    self.board[r][c] = new_col[r]

        if self.board != old_board:
            self.score += total_score
            self._save_best()
            self.add_tile()
            if not self._has_moves():
                self.game_over = True
            return True
        return False

    def _has_moves(self):
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == 0:
                    return True
                if c + 1 < self.size and self.board[r][c] == self.board[r][c + 1]:
                    return True
                if r + 1 < self.size and self.board[r][c] == self.board[r + 1][c]:
                    return True
        return False

    def reset(self):
        self.board = [[0] * self.size for _ in range(self.size)]
        self.score = 0
        self.won = False
        self.game_over = False
        self.add_tile()
        self.add_tile()


TILE_WIDTH = 8
TILE_HEIGHT = 3


def draw_tile(stdscr, y, x, value, h, w):
    color_pair, extra_attr = TILE_COLORS.get(value, (7, curses.A_BOLD))
    attr = curses.color_pair(color_pair) | extra_attr

    if value == 0:
        attr = curses.color_pair(8)

    for dy in range(TILE_HEIGHT):
        for dx in range(TILE_WIDTH):
            py, px = y + dy, x + dx
            if 0 <= py < h and 0 <= px < w:
                try:
                    if dy == 0:
                        if dx == 0:
                            stdscr.addstr(py, px, "╔" if dx == 0 else "═", attr)
                        elif dx == TILE_WIDTH - 1:
                            stdscr.addstr(py, px, "╗", attr)
                        else:
                            stdscr.addstr(py, px, "═", attr)
                    elif dy == TILE_HEIGHT - 1:
                        if dx == 0:
                            stdscr.addstr(py, px, "╚", attr)
                        elif dx == TILE_WIDTH - 1:
                            stdscr.addstr(py, px, "╝", attr)
                        else:
                            stdscr.addstr(py, px, "═", attr)
                    elif dy == 1:
                        if dx == 0 or dx == TILE_WIDTH - 1:
                            stdscr.addstr(py, px, "║", attr)
                        elif dx == 1 and value > 0:
                            text = str(value).center(TILE_WIDTH - 2)
                            stdscr.addstr(py, px, text, attr)
                        elif dx == 1 and value == 0:
                            stdscr.addstr(py, px, "      ", curses.color_pair(8) | curses.A_DIM)
                except curses.error:
                    pass


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

    game = Game2048()

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        # Title
        draw_centered(stdscr, 1, "╔═══════════════════════════════════╗", curses.color_pair(3))
        draw_centered(stdscr, 2, "║          2 0 4 8                  ║", curses.color_pair(3) | curses.A_BOLD)
        draw_centered(stdscr, 3, "╚═══════════════════════════════════╝", curses.color_pair(3))

        # Scores
        score_text = f"Score: {game.score}  |  Best: {game.best_score}"
        draw_centered(stdscr, 5, score_text, curses.color_pair(4))

        # Board
        board_w = game.size * TILE_WIDTH + 2
        board_h = game.size * TILE_HEIGHT + 2
        start_x = max(0, (w - board_w) // 2)
        start_y = 7

        # Draw border
        try:
            stdscr.addstr(start_y, start_x, "╔" + "═" * (board_w - 2) + "╗", curses.color_pair(3))
            for dy in range(1, board_h - 1):
                stdscr.addstr(start_y + dy, start_x, "║", curses.color_pair(3))
                stdscr.addstr(start_y + dy, start_x + board_w - 1, "║", curses.color_pair(3))
            stdscr.addstr(start_y + board_h - 1, start_x, "╚" + "═" * (board_w - 2) + "╝", curses.color_pair(3))
        except curses.error:
            pass

        # Draw tiles
        for r in range(game.size):
            for c in range(game.size):
                ty = start_y + 1 + r * TILE_HEIGHT
                tx = start_x + 1 + c * TILE_WIDTH
                draw_tile(stdscr, ty, tx, game.board[r][c], h, w)

        # Game state messages
        if game.won:
            draw_centered(stdscr, start_y + board_h + 1, "🎉 YOU REACHED 2048! Keep going? 🎉",
                         curses.color_pair(2) | curses.A_BOLD)
        elif game.game_over:
            draw_centered(stdscr, start_y + board_h + 1, "💀 GAME OVER! 💀",
                         curses.color_pair(1) | curses.A_BOLD)
            draw_centered(stdscr, start_y + board_h + 2, f"Final Score: {game.score}",
                         curses.color_pair(4))

        # Controls
        controls_y = min(h - 2, start_y + board_h + 4)
        draw_centered(stdscr, controls_y, "Arrow Keys: Move | R: Restart | Q: Quit", curses.color_pair(8))

        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord('r'), ord('R')):
            game.reset()
        elif not game.game_over:
            if key == curses.KEY_UP or key == ord('w'):
                game.move("up")
            elif key == curses.KEY_DOWN or key == ord('s'):
                game.move("down")
            elif key == curses.KEY_LEFT or key == ord('a'):
                game.move("left")
            elif key == curses.KEY_RIGHT or key == ord('d'):
                game.move("right")


if __name__ == "__main__":
    curses.wrapper(main)
