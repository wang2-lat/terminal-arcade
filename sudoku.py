#!/usr/bin/env python3
"""🔢 Terminal Sudoku - Classic 9x9 puzzle with generation and hints"""
import curses
import random
import time
import copy


def is_valid(board, row, col, num):
    for x in range(9):
        if board[row][x] == num or board[x][col] == num:
            return False
    box_r, box_c = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_r, box_r + 3):
        for c in range(box_c, box_c + 3):
            if board[r][c] == num:
                return False
    return True


def solve(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if is_valid(board, r, c, num):
                        board[r][c] = num
                        if solve(board):
                            return True
                        board[r][c] = 0
                return False
    return True


def generate_puzzle(difficulty):
    board = [[0] * 9 for _ in range(9)]
    solve(board)
    solution = copy.deepcopy(board)

    # Remove cells based on difficulty
    cells_to_remove = {0: 30, 1: 40, 2: 50, 3: 55}[difficulty]
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)

    for r, c in positions[:cells_to_remove]:
        board[r][c] = 0

    return board, solution


CELL_W = 4
CELL_H = 2
DIFFICULTIES = ["Easy", "Medium", "Hard", "Expert"]


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

    # Difficulty selection
    h, w = stdscr.getmaxyx()
    diff = 1
    while True:
        stdscr.clear()
        draw_centered(stdscr, h//2-5, "🔢 SUDOKU 🔢", curses.color_pair(3) | curses.A_BOLD)
        for i, name in enumerate(DIFFICULTIES):
            attr = curses.color_pair(2) | curses.A_BOLD if i == diff else curses.color_pair(7)
            prefix = "▶ " if i == diff else "  "
            draw_centered(stdscr, h//2-2+i, f"{prefix}{name}", attr)
        draw_centered(stdscr, h//2+3, "↑/↓: Select  ENTER: Start  Q: Quit", curses.color_pair(8))
        stdscr.refresh()
        k = stdscr.getch()
        if k == curses.KEY_UP: diff = max(0, diff-1)
        elif k == curses.KEY_DOWN: diff = min(3, diff+1)
        elif k in (10, 13, curses.KEY_ENTER): break
        elif k in (ord('q'), ord('Q')): return

    # Generate
    stdscr.clear()
    draw_centered(stdscr, h//2, "Generating puzzle...", curses.color_pair(3))
    stdscr.refresh()

    board, solution = generate_puzzle(diff)
    original = copy.deepcopy(board)
    cur_r, cur_c = 0, 0
    start_time = time.time()
    hints_used = 0
    mistakes = 0
    won = False
    message = ""

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        # Title
        elapsed = int(time.time() - start_time)
        mins, secs = elapsed // 60, elapsed % 60
        draw_centered(stdscr, 0, f"🔢 SUDOKU [{DIFFICULTIES[diff]}] — {mins:02d}:{secs:02d}",
                     curses.color_pair(3) | curses.A_BOLD)

        # Board
        grid_w = 9 * CELL_W + 4
        grid_h = 9 * CELL_H + 4
        sx = max(1, (w - grid_w) // 2)
        sy = 2

        # Draw grid
        for r in range(10):
            y = sy + r * CELL_H
            thick = r % 3 == 0
            line_ch = "═" if thick else "─"
            try:
                for x in range(grid_w):
                    color = curses.color_pair(3) if thick else curses.color_pair(8)
                    stdscr.addstr(y, sx + x, line_ch, color)
                # Intersections
                for c in range(10):
                    cx = sx + c * CELL_W
                    c_thick = c % 3 == 0
                    if thick and c_thick:
                        stdscr.addstr(y, cx, "╬", curses.color_pair(3))
                    elif thick:
                        stdscr.addstr(y, cx, "╪", curses.color_pair(3))
                    elif c_thick:
                        stdscr.addstr(y, cx, "╫", curses.color_pair(8))
                    else:
                        stdscr.addstr(y, cx, "┼", curses.color_pair(8))
            except curses.error:
                pass

        # Vertical lines
        for r in range(9):
            y = sy + r * CELL_H + 1
            for c in range(10):
                cx = sx + c * CELL_W
                thick = c % 3 == 0
                try:
                    ch = "║" if thick else "│"
                    color = curses.color_pair(3) if thick else curses.color_pair(8)
                    stdscr.addstr(y, cx, ch, color)
                except curses.error:
                    pass

        # Numbers
        for r in range(9):
            for c in range(9):
                y = sy + r * CELL_H + 1
                x = sx + c * CELL_W + 1
                val = board[r][c]
                is_cursor = (r == cur_r and c == cur_c)
                is_original = original[r][c] != 0
                is_wrong = val != 0 and val != solution[r][c]

                if val != 0:
                    ch = f" {val} "
                    if is_wrong:
                        color = curses.color_pair(1) | curses.A_BOLD
                    elif is_original:
                        color = curses.color_pair(7) | curses.A_BOLD
                    else:
                        color = curses.color_pair(2)
                else:
                    ch = "   "
                    color = curses.color_pair(8)

                if is_cursor:
                    color = color | curses.A_REVERSE

                try:
                    stdscr.addstr(y, x, ch, color)
                except curses.error:
                    pass

        # Side info
        info_x = sx + grid_w + 3
        if info_x + 15 < w:
            try:
                stdscr.addstr(sy, info_x, "Stats:", curses.color_pair(3) | curses.A_BOLD)
                stdscr.addstr(sy+1, info_x, f"Hints: {hints_used}", curses.color_pair(4))
                stdscr.addstr(sy+2, info_x, f"Errors: {mistakes}", curses.color_pair(1))
                filled = sum(1 for r in range(9) for c in range(9) if board[r][c] != 0)
                stdscr.addstr(sy+3, info_x, f"Filled: {filled}/81", curses.color_pair(2))

                stdscr.addstr(sy+5, info_x, "Controls:", curses.color_pair(3) | curses.A_BOLD)
                stdscr.addstr(sy+6, info_x, "Arrows: Move", curses.color_pair(8))
                stdscr.addstr(sy+7, info_x, "1-9: Place", curses.color_pair(8))
                stdscr.addstr(sy+8, info_x, "0/Del: Clear", curses.color_pair(8))
                stdscr.addstr(sy+9, info_x, "H: Hint", curses.color_pair(8))
                stdscr.addstr(sy+10, info_x, "Q: Quit", curses.color_pair(8))
            except curses.error:
                pass

        # Message
        if message:
            draw_centered(stdscr, h-3, message, curses.color_pair(2) | curses.A_BOLD)

        if won:
            draw_centered(stdscr, h-4, f"🎉 COMPLETED in {mins}:{secs:02d}! 🎉",
                         curses.color_pair(2) | curses.A_BOLD)
            draw_centered(stdscr, h-2, "N: New game  Q: Quit", curses.color_pair(8))
        else:
            draw_centered(stdscr, h-1, "1-9:Place  0:Clear  H:Hint  N:New  Q:Quit", curses.color_pair(8))

        stdscr.refresh()

        key = stdscr.getch()
        message = ""

        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord('n'), ord('N')):
            board, solution = generate_puzzle(diff)
            original = copy.deepcopy(board)
            cur_r, cur_c = 0, 0
            start_time = time.time()
            hints_used = mistakes = 0
            won = False
        elif won:
            continue
        elif key == curses.KEY_UP:
            cur_r = max(0, cur_r - 1)
        elif key == curses.KEY_DOWN:
            cur_r = min(8, cur_r + 1)
        elif key == curses.KEY_LEFT:
            cur_c = max(0, cur_c - 1)
        elif key == curses.KEY_RIGHT:
            cur_c = min(8, cur_c + 1)
        elif ord('1') <= key <= ord('9'):
            if original[cur_r][cur_c] == 0:
                num = key - ord('0')
                board[cur_r][cur_c] = num
                if num != solution[cur_r][cur_c]:
                    mistakes += 1
                # Check win
                if board == solution:
                    won = True
        elif key in (ord('0'), curses.KEY_BACKSPACE, curses.KEY_DC, 127):
            if original[cur_r][cur_c] == 0:
                board[cur_r][cur_c] = 0
        elif key in (ord('h'), ord('H')):
            if original[cur_r][cur_c] == 0 and board[cur_r][cur_c] != solution[cur_r][cur_c]:
                board[cur_r][cur_c] = solution[cur_r][cur_c]
                hints_used += 1
                message = f"Hint: {solution[cur_r][cur_c]}"
                if board == solution:
                    won = True


if __name__ == "__main__":
    curses.wrapper(main)
