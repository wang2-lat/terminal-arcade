#!/usr/bin/env python3
"""
Terminal Tetris — a complete curses-based Tetris game.

Controls:
    Left/Right  Move piece
    Up          Rotate clockwise
    Down        Soft drop (1 row)
    Space       Hard drop
    H           Hold piece
    P           Pause
    Q           Quit
"""

import curses
import random
import time
import copy

# ──────────────────────────────────────────────
# Piece definitions: each is a list of rotations,
# each rotation is a list of (row, col) offsets.
# ──────────────────────────────────────────────

PIECES = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "T": [
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 0), (1, 0), (2, 0), (1, 1)],
        [(1, 0), (1, 1), (1, 2), (0, 1)],
        [(0, 0), (1, 0), (2, 0), (1, -1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, -1)],
    ],
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

# Color index for each piece type (maps to curses color pair id)
PIECE_COLORS = {
    "I": 1,  # Cyan
    "O": 2,  # Yellow
    "T": 3,  # Magenta
    "S": 4,  # Green
    "Z": 5,  # Red
    "J": 6,  # Blue
    "L": 7,  # White (orange not available in basic curses)
}

PIECE_NAMES = list(PIECES.keys())

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

CELL_WIDTH = 2  # Each cell is 2 chars wide for a square look

SCORE_TABLE = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}


def init_colors():
    """Set up curses color pairs."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_CYAN)       # I
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_YELLOW)   # O
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA) # T
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_GREEN)     # S
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_RED)         # Z
    curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLUE)       # J
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_WHITE)     # L
    # Ghost piece color: dim
    curses.init_pair(8, curses.COLOR_WHITE, -1)
    # Border color
    curses.init_pair(9, curses.COLOR_WHITE, -1)
    # Flash animation color
    curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # Title color
    curses.init_pair(11, curses.COLOR_CYAN, -1)
    # Score highlight
    curses.init_pair(12, curses.COLOR_YELLOW, -1)


class Tetris:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.paused = False

        self.bag = []
        self.current_piece = None
        self.current_type = None
        self.current_rotation = 0
        self.current_row = 0
        self.current_col = 0

        self.next_type = None
        self.hold_type = None
        self.hold_used = False  # Can only hold once per piece

        self._fill_bag()
        self._spawn_piece()
        self.next_type = self._pick_from_bag()

    # ── Bag randomizer (7-bag) ──────────────────

    def _fill_bag(self):
        new_bag = list(PIECE_NAMES)
        random.shuffle(new_bag)
        self.bag.extend(new_bag)

    def _pick_from_bag(self):
        if len(self.bag) < 2:
            self._fill_bag()
        return self.bag.pop(0)

    # ── Piece spawning ──────────────────────────

    def _spawn_piece(self, piece_type=None):
        if piece_type is None:
            if self.next_type is not None:
                piece_type = self.next_type
            else:
                piece_type = self._pick_from_bag()
            self.next_type = self._pick_from_bag()

        self.current_type = piece_type
        self.current_rotation = 0
        self.current_piece = PIECES[piece_type][0]
        self.hold_used = False

        # Center horizontally
        min_c = min(c for _, c in self.current_piece)
        max_c = max(c for _, c in self.current_piece)
        piece_w = max_c - min_c + 1
        self.current_col = (BOARD_WIDTH - piece_w) // 2 - min_c
        self.current_row = 0

        # If spawn position is blocked, game over
        if not self._valid_position(self.current_piece, self.current_row, self.current_col):
            self.game_over = True

    # ── Collision detection ─────────────────────

    def _valid_position(self, piece, row, col):
        for dr, dc in piece:
            r = row + dr
            c = col + dc
            if c < 0 or c >= BOARD_WIDTH:
                return False
            if r >= BOARD_HEIGHT:
                return False
            if r < 0:
                continue  # Allow above board
            if self.board[r][c] != 0:
                return False
        return True

    # ── Movement ────────────────────────────────

    def move_left(self):
        if self._valid_position(self.current_piece, self.current_row, self.current_col - 1):
            self.current_col -= 1

    def move_right(self):
        if self._valid_position(self.current_piece, self.current_row, self.current_col + 1):
            self.current_col += 1

    def move_down(self):
        """Soft drop. Returns True if piece locked."""
        if self._valid_position(self.current_piece, self.current_row + 1, self.current_col):
            self.current_row += 1
            return False
        else:
            self._lock_piece()
            return True

    def hard_drop(self):
        """Instantly drop piece to lowest valid position."""
        drop_rows = 0
        while self._valid_position(self.current_piece, self.current_row + 1, self.current_col):
            self.current_row += 1
            drop_rows += 1
        self.score += drop_rows * 2
        self._lock_piece()

    def rotate(self):
        """Rotate clockwise with wall kicks."""
        new_rot = (self.current_rotation + 1) % 4
        new_piece = PIECES[self.current_type][new_rot]

        # Try basic rotation
        if self._valid_position(new_piece, self.current_row, self.current_col):
            self.current_rotation = new_rot
            self.current_piece = new_piece
            return

        # Wall kick offsets to try
        kicks = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1), (0, -2), (0, 2)]
        for dc, dr in kicks:
            if self._valid_position(new_piece, self.current_row + dr, self.current_col + dc):
                self.current_rotation = new_rot
                self.current_piece = new_piece
                self.current_col += dc
                self.current_row += dr
                return

    def hold_piece(self):
        """Hold current piece, swap with held piece."""
        if self.hold_used:
            return
        self.hold_used = True
        if self.hold_type is None:
            self.hold_type = self.current_type
            self._spawn_piece()
        else:
            old_hold = self.hold_type
            self.hold_type = self.current_type
            self._spawn_piece(piece_type=old_hold)

    # ── Ghost piece ─────────────────────────────

    def ghost_row(self):
        """Return the row where the piece would land."""
        r = self.current_row
        while self._valid_position(self.current_piece, r + 1, self.current_col):
            r += 1
        return r

    # ── Lock and clear ──────────────────────────

    def _lock_piece(self):
        color = PIECE_COLORS[self.current_type]
        for dr, dc in self.current_piece:
            r = self.current_row + dr
            c = self.current_col + dc
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                self.board[r][c] = color

        cleared = self._find_full_lines()
        if cleared:
            self._animate_clear(cleared)
            self._clear_lines(cleared)
            n = len(cleared)
            self.lines_cleared += n
            self.score += SCORE_TABLE.get(n, 800) * self.level
            self.level = self.lines_cleared // 10 + 1

        self._spawn_piece()

    def _find_full_lines(self):
        full = []
        for r in range(BOARD_HEIGHT):
            if all(self.board[r][c] != 0 for c in range(BOARD_WIDTH)):
                full.append(r)
        return full

    def _animate_clear(self, rows):
        """Flash the cleared lines."""
        board_y, board_x = self._board_origin()
        for flash in range(3):
            for r in rows:
                y = board_y + r + 1
                x = board_x + 1
                if flash % 2 == 0:
                    self.stdscr.addstr(y, x, " " * (BOARD_WIDTH * CELL_WIDTH),
                                       curses.color_pair(10) | curses.A_BOLD)
                else:
                    for c in range(BOARD_WIDTH):
                        color = self.board[r][c]
                        if color:
                            self.stdscr.addstr(y, x + c * CELL_WIDTH, "[]",
                                               curses.color_pair(color))
                        else:
                            self.stdscr.addstr(y, x + c * CELL_WIDTH, "  ")
            self.stdscr.refresh()
            time.sleep(0.08)

    def _clear_lines(self, rows):
        for r in sorted(rows):
            del self.board[r]
            self.board.insert(0, [0] * BOARD_WIDTH)

    # ── Gravity speed ───────────────────────────

    def drop_interval(self):
        """Seconds between automatic drops. Speeds up with level."""
        base = 0.8
        return max(0.05, base - (self.level - 1) * 0.06)

    # ── Board origin (for centering) ────────────

    def _board_origin(self):
        """Top-left corner of the board border in screen coordinates."""
        max_y, max_x = self.stdscr.getmaxyx()
        board_h = BOARD_HEIGHT + 2  # +2 for top/bottom borders
        board_w = BOARD_WIDTH * CELL_WIDTH + 2  # +2 for side borders
        origin_y = max(0, (max_y - board_h) // 2)
        origin_x = max(0, (max_x - board_w - 20) // 2)  # offset left for side panel
        return origin_y, origin_x

    # ── Drawing ─────────────────────────────────

    def draw(self):
        self.stdscr.erase()
        max_y, max_x = self.stdscr.getmaxyx()

        if max_y < BOARD_HEIGHT + 4 or max_x < BOARD_WIDTH * CELL_WIDTH + 30:
            self.stdscr.addstr(0, 0, "Terminal too small! Resize to at least 50x26.")
            self.stdscr.refresh()
            return

        board_y, board_x = self._board_origin()
        self._draw_board(board_y, board_x)
        self._draw_current_piece(board_y, board_x)
        self._draw_ghost(board_y, board_x)
        self._draw_side_panel(board_y, board_x + BOARD_WIDTH * CELL_WIDTH + 4)
        self.stdscr.refresh()

    def _draw_board(self, oy, ox):
        """Draw the board border and locked cells."""
        bw = BOARD_WIDTH * CELL_WIDTH + 2
        border_attr = curses.color_pair(9) | curses.A_DIM

        # Top border
        self.stdscr.addstr(oy, ox, "+" + "-" * (bw - 2) + "+", border_attr)
        # Bottom border
        self.stdscr.addstr(oy + BOARD_HEIGHT + 1, ox, "+" + "-" * (bw - 2) + "+", border_attr)

        for r in range(BOARD_HEIGHT):
            y = oy + r + 1
            self.stdscr.addstr(y, ox, "|", border_attr)
            for c in range(BOARD_WIDTH):
                color = self.board[r][c]
                x = ox + 1 + c * CELL_WIDTH
                if color:
                    self.stdscr.addstr(y, x, "[]", curses.color_pair(color))
                else:
                    self.stdscr.addstr(y, x, " .", curses.A_DIM)
            self.stdscr.addstr(y, ox + bw - 1, "|", border_attr)

    def _draw_current_piece(self, oy, ox):
        if self.current_piece is None:
            return
        color = PIECE_COLORS[self.current_type]
        for dr, dc in self.current_piece:
            r = self.current_row + dr
            c = self.current_col + dc
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                y = oy + r + 1
                x = ox + 1 + c * CELL_WIDTH
                self.stdscr.addstr(y, x, "[]", curses.color_pair(color) | curses.A_BOLD)

    def _draw_ghost(self, oy, ox):
        if self.current_piece is None:
            return
        gr = self.ghost_row()
        if gr == self.current_row:
            return
        for dr, dc in self.current_piece:
            r = gr + dr
            c = self.current_col + dc
            if 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH:
                y = oy + r + 1
                x = ox + 1 + c * CELL_WIDTH
                # Only draw ghost if cell is empty and not occupied by current piece
                occupied = False
                for dr2, dc2 in self.current_piece:
                    if self.current_row + dr2 == r and self.current_col + dc2 == c:
                        occupied = True
                        break
                if not occupied and self.board[r][c] == 0:
                    self.stdscr.addstr(y, x, "[]", curses.color_pair(8) | curses.A_DIM)

    def _draw_side_panel(self, oy, ox):
        """Draw score, next piece, hold piece."""
        attr_label = curses.A_BOLD
        attr_value = curses.color_pair(12) | curses.A_BOLD

        # Score
        self.stdscr.addstr(oy, ox, "SCORE", attr_label)
        self.stdscr.addstr(oy + 1, ox, f"{self.score:>8}", attr_value)

        # Level
        self.stdscr.addstr(oy + 3, ox, "LEVEL", attr_label)
        self.stdscr.addstr(oy + 4, ox, f"{self.level:>8}", attr_value)

        # Lines
        self.stdscr.addstr(oy + 6, ox, "LINES", attr_label)
        self.stdscr.addstr(oy + 7, ox, f"{self.lines_cleared:>8}", attr_value)

        # Next piece
        self.stdscr.addstr(oy + 9, ox, "NEXT", attr_label)
        if self.next_type:
            self._draw_mini_piece(oy + 10, ox + 1, self.next_type)

        # Hold piece
        self.stdscr.addstr(oy + 15, ox, "HOLD", attr_label)
        if self.hold_type:
            self._draw_mini_piece(oy + 16, ox + 1, self.hold_type)
        else:
            self.stdscr.addstr(oy + 16, ox + 1, "  --  ", curses.A_DIM)

        # Controls
        cy = oy + 21
        try:
            self.stdscr.addstr(cy, ox, "CONTROLS", curses.A_DIM)
            controls = [
                ("<-/->", "Move"),
                ("  Up ", "Rotate"),
                ("Down ", "Soft Drop"),
                ("Space", "Hard Drop"),
                ("  H  ", "Hold"),
                ("  P  ", "Pause"),
                ("  Q  ", "Quit"),
            ]
            for i, (key, desc) in enumerate(controls):
                if cy + 1 + i < self.stdscr.getmaxyx()[0] - 1:
                    self.stdscr.addstr(cy + 1 + i, ox, f"{key} {desc}", curses.A_DIM)
        except curses.error:
            pass

    def _draw_mini_piece(self, y, x, piece_type):
        """Draw a small preview of a piece."""
        shape = PIECES[piece_type][0]
        color = PIECE_COLORS[piece_type]

        # Clear area
        for row in range(4):
            try:
                self.stdscr.addstr(y + row, x, "        ", curses.A_DIM)
            except curses.error:
                pass

        for dr, dc in shape:
            try:
                self.stdscr.addstr(y + dr, x + dc * CELL_WIDTH, "[]", curses.color_pair(color))
            except curses.error:
                pass


def welcome_screen(stdscr):
    """Show welcome screen, wait for Enter to start."""
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    title = [
        " _____ _____ _____ ____  ___ ____  ",
        "|_   _| ____|_   _|  _ \\|_ _/ ___| ",
        "  | | |  _|   | | | |_) || |\\___ \\ ",
        "  | | | |___  | | |  _ < | | ___) |",
        "  |_| |_____| |_| |_| \\_\\___|____/ ",
    ]

    start_y = max(0, max_y // 2 - 8)

    for i, line in enumerate(title):
        x = max(0, (max_x - len(line)) // 2)
        try:
            stdscr.addstr(start_y + i, x, line, curses.color_pair(11) | curses.A_BOLD)
        except curses.error:
            pass

    info_lines = [
        "",
        "Terminal Tetris",
        "",
        "Controls:",
        "  Arrow Keys   Move & Rotate",
        "  Space        Hard Drop",
        "  H            Hold Piece",
        "  P            Pause",
        "  Q            Quit",
        "",
        "Press ENTER to start!",
    ]

    for i, line in enumerate(info_lines):
        y = start_y + len(title) + i
        x = max(0, (max_x - len(line)) // 2)
        attr = curses.A_BOLD if "ENTER" in line else curses.A_NORMAL
        try:
            stdscr.addstr(y, x, line, attr)
        except curses.error:
            pass

    stdscr.refresh()

    # Wait for Enter
    while True:
        key = stdscr.getch()
        if key in (10, 13, curses.KEY_ENTER):
            break
        if key in (ord('q'), ord('Q')):
            return False
    return True


def game_over_screen(stdscr, score, level, lines):
    """Show game over screen. Return True to restart, False to quit."""
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    cy = max_y // 2 - 5

    game_over_text = "GAME OVER"
    x = max(0, (max_x - len(game_over_text)) // 2)
    try:
        stdscr.addstr(cy, x, game_over_text, curses.color_pair(5) | curses.A_BOLD)
    except curses.error:
        pass

    stats = [
        f"Score: {score}",
        f"Level: {level}",
        f"Lines: {lines}",
        "",
        "Press ENTER to play again",
        "Press Q to quit",
    ]

    for i, line in enumerate(stats):
        y = cy + 2 + i
        x = max(0, (max_x - len(line)) // 2)
        attr = curses.color_pair(12) | curses.A_BOLD if "Score" in line else curses.A_NORMAL
        try:
            stdscr.addstr(y, x, line, attr)
        except curses.error:
            pass

    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in (10, 13, curses.KEY_ENTER):
            return True
        if key in (ord('q'), ord('Q')):
            return False


def run_game(stdscr):
    """Main game loop."""
    curses.curs_set(0)
    init_colors()
    stdscr.nodelay(True)
    stdscr.timeout(16)  # ~60 fps polling

    if not welcome_screen(stdscr):
        return

    while True:
        stdscr.nodelay(True)
        stdscr.timeout(16)

        game = Tetris(stdscr)
        last_drop = time.monotonic()
        last_key_time = {}
        key_repeat_delay = 0.12  # seconds before key repeat starts
        key_repeat_rate = 0.04   # seconds between repeated keys

        while not game.game_over:
            now = time.monotonic()

            # Handle input
            key = stdscr.getch()

            if key == ord('q') or key == ord('Q'):
                return

            if key == ord('p') or key == ord('P'):
                game.paused = not game.paused
                if game.paused:
                    max_y, max_x = stdscr.getmaxyx()
                    msg = "PAUSED - Press P to resume"
                    x = max(0, (max_x - len(msg)) // 2)
                    y = max_y // 2
                    stdscr.addstr(y, x, msg, curses.A_BOLD | curses.A_REVERSE)
                    stdscr.refresh()
                continue

            if game.paused:
                continue

            if key == curses.KEY_LEFT:
                game.move_left()
                last_key_time[curses.KEY_LEFT] = now
            elif key == curses.KEY_RIGHT:
                game.move_right()
                last_key_time[curses.KEY_RIGHT] = now
            elif key == curses.KEY_UP:
                game.rotate()
            elif key == curses.KEY_DOWN:
                game.move_down()
                game.score += 1  # soft drop bonus
                last_drop = now
            elif key == ord(' '):
                game.hard_drop()
                last_drop = now
            elif key == ord('h') or key == ord('H'):
                game.hold_piece()

            # Auto-gravity
            if now - last_drop >= game.drop_interval():
                game.move_down()
                last_drop = now

            game.draw()

        # Game over
        stdscr.nodelay(False)
        stdscr.timeout(-1)
        if not game_over_screen(stdscr, game.score, game.level, game.lines_cleared):
            break


def main(stdscr):
    run_game(stdscr)


if __name__ == "__main__":
    curses.wrapper(main)


def main_entry():
    import curses
    curses.wrapper(main)

