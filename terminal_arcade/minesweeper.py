#!/usr/bin/env python3
"""🎯 Terminal Minesweeper - Classic mine-clearing game!"""
import curses
import random
import time

MINE = -1
FLAG = -2
HIDDEN = -3

# Display characters
CHARS = {
    0: ' ',
    1: '1', 2: '2', 3: '3', 4: '4',
    5: '5', 6: '6', 7: '7', 8: '8',
}
COLORS = {
    1: 6,   # blue
    2: 2,   # green
    3: 1,   # red
    4: 5,   # magenta
    5: 1,   # dark red
    6: 4,   # cyan
    7: 7,   # white
    8: 7,   # white bold
}

DIFFICULTIES = [
    ("Easy", 9, 9, 10),
    ("Medium", 16, 16, 40),
    ("Hard", 16, 30, 99),
]


class Minesweeper:
    def __init__(self, rows, cols, mines):
        self.rows = rows
        self.cols = cols
        self.num_mines = mines
        self.board = [[0] * cols for _ in range(rows)]
        self.revealed = [[False] * cols for _ in range(rows)]
        self.flagged = [[False] * cols for _ in range(rows)]
        self.game_over = False
        self.won = False
        self.first_click = True
        self.flags_placed = 0
        self.cells_revealed = 0
        self.start_time = None

    def place_mines(self, safe_r, safe_c):
        """Place mines, avoiding the first click position and its neighbors."""
        safe = set()
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                safe.add((safe_r + dr, safe_c + dc))

        positions = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if (r, c) not in safe]
        mine_positions = random.sample(positions, min(self.num_mines, len(positions)))

        for r, c in mine_positions:
            self.board[r][c] = MINE

        # Calculate numbers
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == MINE:
                    continue
                count = 0
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and self.board[nr][nc] == MINE:
                            count += 1
                self.board[r][c] = count

    def reveal(self, r, c):
        if self.first_click:
            self.first_click = False
            self.start_time = time.time()
            self.place_mines(r, c)

        if self.flagged[r][c] or self.revealed[r][c]:
            return

        self.revealed[r][c] = True
        self.cells_revealed += 1

        if self.board[r][c] == MINE:
            self.game_over = True
            # Reveal all mines
            for rr in range(self.rows):
                for cc in range(self.cols):
                    if self.board[rr][cc] == MINE:
                        self.revealed[rr][cc] = True
            return

        # Auto-expand zeros
        if self.board[r][c] == 0:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.revealed[nr][nc]:
                        self.reveal(nr, nc)

        # Check win
        total_safe = self.rows * self.cols - self.num_mines
        if self.cells_revealed >= total_safe:
            self.won = True
            self.game_over = True

    def toggle_flag(self, r, c):
        if self.revealed[r][c]:
            return
        if self.flagged[r][c]:
            self.flagged[r][c] = False
            self.flags_placed -= 1
        else:
            self.flagged[r][c] = True
            self.flags_placed += 1

    def chord(self, r, c):
        """Reveal neighbors if correct number of flags around."""
        if not self.revealed[r][c] or self.board[r][c] <= 0:
            return
        flag_count = 0
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and self.flagged[nr][nc]:
                    flag_count += 1
        if flag_count == self.board[r][c]:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                            self.reveal(nr, nc)

    def elapsed(self):
        if self.start_time is None:
            return 0
        if self.game_over:
            return int(time.time() - self.start_time)
        return int(time.time() - self.start_time)


CELL_W = 3


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


def difficulty_select(stdscr):
    h, w = stdscr.getmaxyx()
    selected = 0

    while True:
        stdscr.clear()
        draw_centered(stdscr, 2, "🎯 MINESWEEPER 🎯", curses.color_pair(3) | curses.A_BOLD)
        draw_centered(stdscr, 3, "═" * 30, curses.color_pair(3))

        for i, (name, rows, cols, mines) in enumerate(DIFFICULTIES):
            y = 6 + i * 2
            text = f"  {name}: {cols}x{rows} ({mines} mines)  "
            if i == selected:
                draw_centered(stdscr, y, f"▶ {text} ◀", curses.color_pair(2) | curses.A_BOLD)
            else:
                draw_centered(stdscr, y, text, curses.color_pair(4))

        draw_centered(stdscr, 14, "↑/↓: Select  ENTER: Start  Q: Quit", curses.color_pair(8))
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(DIFFICULTIES)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(DIFFICULTIES)
        elif key in (curses.KEY_ENTER, 10, 13):
            return DIFFICULTIES[selected]
        elif key in (ord('q'), ord('Q')):
            return None


def play_game(stdscr, difficulty):
    name, rows, cols, mines = difficulty
    game = Minesweeper(rows, cols, mines)
    cursor_r, cursor_c = rows // 2, cols // 2

    h, w = stdscr.getmaxyx()

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Header
        elapsed = game.elapsed()
        header = f" 🎯 MINESWEEPER [{name}] | Mines: {mines - game.flags_placed} | Time: {elapsed}s "
        draw_centered(stdscr, 0, header, curses.color_pair(3) | curses.A_BOLD)

        # Board
        board_w = cols * CELL_W + 2
        start_x = max(0, (w - board_w) // 2)
        start_y = 2

        # Top border
        try:
            stdscr.addstr(start_y, start_x, "╔" + "═" * (cols * CELL_W) + "╗", curses.color_pair(3))
        except curses.error:
            pass

        for r in range(rows):
            y = start_y + 1 + r
            try:
                stdscr.addstr(y, start_x, "║", curses.color_pair(3))
            except curses.error:
                pass

            for c in range(cols):
                x = start_x + 1 + c * CELL_W
                is_cursor = (r == cursor_r and c == cursor_c)

                if game.flagged[r][c] and not (game.game_over and game.board[r][c] != MINE):
                    ch = " ⚑ "
                    color = curses.color_pair(1) | curses.A_BOLD
                elif not game.revealed[r][c]:
                    ch = " ■ "
                    color = curses.color_pair(8)
                elif game.board[r][c] == MINE:
                    ch = " ✹ "
                    color = curses.color_pair(1) | curses.A_BOLD
                elif game.board[r][c] == 0:
                    ch = "   "
                    color = curses.color_pair(7)
                else:
                    num = game.board[r][c]
                    ch = f" {num} "
                    color = curses.color_pair(COLORS.get(num, 7))

                if is_cursor:
                    color = color | curses.A_REVERSE

                try:
                    stdscr.addstr(y, x, ch, color)
                except curses.error:
                    pass

            try:
                stdscr.addstr(y, start_x + 1 + cols * CELL_W, "║", curses.color_pair(3))
            except curses.error:
                pass

        # Bottom border
        try:
            stdscr.addstr(start_y + 1 + rows, start_x,
                         "╚" + "═" * (cols * CELL_W) + "╝", curses.color_pair(3))
        except curses.error:
            pass

        # Game over message
        if game.game_over:
            msg_y = start_y + rows + 3
            if game.won:
                draw_centered(stdscr, msg_y, "🎉 YOU WIN! 🎉", curses.color_pair(2) | curses.A_BOLD)
                draw_centered(stdscr, msg_y + 1, f"Time: {elapsed}s", curses.color_pair(4))
            else:
                draw_centered(stdscr, msg_y, "💥 BOOM! Game Over! 💥", curses.color_pair(1) | curses.A_BOLD)
            draw_centered(stdscr, msg_y + 2, "R: Restart  Q: Quit  N: New difficulty", curses.color_pair(8))
        else:
            controls_y = min(h - 1, start_y + rows + 3)
            draw_centered(stdscr, controls_y,
                         "Arrows:Move  ENTER/Space:Reveal  F:Flag  C:Chord  Q:Quit", curses.color_pair(8))

        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            return "quit"
        elif key in (ord('r'), ord('R')):
            return "restart"
        elif key in (ord('n'), ord('N')):
            return "new"

        if game.game_over:
            continue

        if key == curses.KEY_UP or key == ord('w'):
            cursor_r = max(0, cursor_r - 1)
        elif key == curses.KEY_DOWN or key == ord('s'):
            cursor_r = min(rows - 1, cursor_r + 1)
        elif key == curses.KEY_LEFT or key == ord('a'):
            cursor_c = max(0, cursor_c - 1)
        elif key == curses.KEY_RIGHT or key == ord('d'):
            cursor_c = min(cols - 1, cursor_c + 1)
        elif key in (curses.KEY_ENTER, 10, 13, ord(' ')):
            game.reveal(cursor_r, cursor_c)
        elif key in (ord('f'), ord('F')):
            game.toggle_flag(cursor_r, cursor_c)
        elif key in (ord('c'), ord('C')):
            game.chord(cursor_r, cursor_c)


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

    difficulty = None
    while True:
        if difficulty is None:
            difficulty = difficulty_select(stdscr)
            if difficulty is None:
                break

        result = play_game(stdscr, difficulty)
        if result == "quit":
            break
        elif result == "new":
            difficulty = None
        # "restart" loops back with same difficulty


if __name__ == "__main__":
    curses.wrapper(main)


def main_entry():
    import curses
    curses.wrapper(main)

