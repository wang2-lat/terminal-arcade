#!/usr/bin/env python3
"""🏰 Maze Generator & A* Pathfinding Visualizer"""
import curses
import random
import time
import heapq

WALL = 1
PATH = 0
VISITED = 2
SOLUTION = 3
START = 4
END = 5
FRONTIER = 6


def generate_maze(h, w):
    """Generate maze using recursive backtracking."""
    maze = [[WALL] * w for _ in range(h)]

    def carve(y, x):
        maze[y][x] = PATH
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        random.shuffle(directions)
        for dy, dx in directions:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and maze[ny][nx] == WALL:
                maze[y + dy // 2][x + dx // 2] = PATH
                carve(ny, nx)

    carve(1, 1)
    return maze


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(maze, start, end, callback=None):
    """A* pathfinding with visualization callback."""
    h, w = len(maze), len(maze[0])
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}
    visited = set()
    step_count = 0

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in visited:
            continue
        visited.add(current)
        step_count += 1

        if current == end:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1], visited, step_count

        if callback and step_count % 2 == 0:
            callback(visited, set(n for _, n in open_set), current)

        for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            ny, nx = current[0] + dy, current[1] + dx
            if 0 <= ny < h and 0 <= nx < w and maze[ny][nx] != WALL:
                neighbor = (ny, nx)
                tentative = g_score[current] + 1
                if tentative < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    f_score[neighbor] = tentative + heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return [], visited, step_count


def draw_maze(stdscr, maze, start, end, visited=None, frontier=None, solution=None, current=None):
    h, w = stdscr.getmaxyx()
    mh, mw = len(maze), len(maze[0])

    visited = visited or set()
    frontier = frontier or set()
    solution = solution or []
    solution_set = set(solution)

    for y in range(min(mh, h - 3)):
        for x in range(min(mw, w - 1)):
            pos = (y, x)
            try:
                if pos == start:
                    stdscr.addstr(y, x, "S", curses.color_pair(2) | curses.A_BOLD)
                elif pos == end:
                    stdscr.addstr(y, x, "E", curses.color_pair(1) | curses.A_BOLD)
                elif pos == current:
                    stdscr.addstr(y, x, "◆", curses.color_pair(4) | curses.A_BOLD)
                elif pos in solution_set:
                    stdscr.addstr(y, x, "●", curses.color_pair(2) | curses.A_BOLD)
                elif pos in frontier:
                    stdscr.addstr(y, x, "◇", curses.color_pair(3))
                elif pos in visited:
                    stdscr.addstr(y, x, "·", curses.color_pair(5))
                elif maze[y][x] == WALL:
                    stdscr.addstr(y, x, "█", curses.color_pair(6))
                else:
                    stdscr.addstr(y, x, " ")
            except curses.error:
                pass


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)      # End / errors
    curses.init_pair(2, curses.COLOR_GREEN, -1)     # Start / solution
    curses.init_pair(3, curses.COLOR_CYAN, -1)      # Frontier
    curses.init_pair(4, curses.COLOR_YELLOW, -1)    # Current
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)   # Visited
    curses.init_pair(6, curses.COLOR_BLUE, -1)      # Walls
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    stdscr.nodelay(False)
    stdscr.keypad(True)

    while True:
        h, w = stdscr.getmaxyx()
        # Make maze dimensions odd for proper generation
        maze_h = ((h - 4) // 2) * 2 + 1
        maze_w = ((w - 2) // 2) * 2 + 1
        maze_h = max(11, min(maze_h, 61))
        maze_w = max(21, min(maze_w, 121))

        # Welcome
        stdscr.clear()
        title = "🏰 MAZE GENERATOR & A* PATHFINDING 🏰"
        try:
            stdscr.addstr(h // 2 - 3, max(0, (w - len(title)) // 2), title, curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(h // 2 - 1, max(0, (w - 30) // 2), f"Maze size: {maze_w}x{maze_h}", curses.color_pair(3))
            stdscr.addstr(h // 2 + 1, max(0, (w - 40) // 2), "Press ENTER to generate and solve!", curses.color_pair(2))
            stdscr.addstr(h // 2 + 2, max(0, (w - 40) // 2), "Press Q to quit", curses.color_pair(8))
        except curses.error:
            pass
        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break

        # Generate maze
        stdscr.clear()
        try:
            stdscr.addstr(h // 2, max(0, (w - 20) // 2), "Generating maze...", curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass
        stdscr.refresh()

        maze = generate_maze(maze_h, maze_w)
        start = (1, 1)
        end = (maze_h - 2, maze_w - 2)
        maze[start[0]][start[1]] = PATH
        maze[end[0]][end[1]] = PATH

        # Show empty maze
        stdscr.clear()
        draw_maze(stdscr, maze, start, end)
        try:
            stdscr.addstr(h - 2, 0, " Press ENTER to start A* pathfinding... ", curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass
        stdscr.refresh()
        stdscr.getch()

        # Animated A* search
        stdscr.nodelay(True)
        speed = 0.01
        step_count = 0
        start_time = time.time()

        def vis_callback(visited, frontier, current):
            nonlocal step_count
            step_count += 1
            stdscr.erase()
            draw_maze(stdscr, maze, start, end, visited, frontier, current=current)
            elapsed = time.time() - start_time
            status = f" A* Search | Visited: {len(visited)} | Frontier: {len(frontier)} | Steps: {step_count} | Time: {elapsed:.2f}s "
            try:
                stdscr.addstr(h - 2, 0, "═" * (w - 1), curses.color_pair(4))
                stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.refresh()
            time.sleep(speed)
            # Check for speed changes
            try:
                k = stdscr.getch()
                if k == ord('+') or k == ord('='):
                    pass  # already fast
                elif k == ord('-'):
                    pass
            except:
                pass

        solution, visited, total_steps = astar(maze, start, end, vis_callback)
        elapsed = time.time() - start_time

        # Animate solution path
        stdscr.nodelay(False)
        if solution:
            for i in range(len(solution)):
                stdscr.erase()
                draw_maze(stdscr, maze, start, end, visited, set(), solution[:i+1])
                status = f" ✓ SOLVED! Path length: {len(solution)} | Visited: {len(visited)} | Time: {elapsed:.2f}s "
                try:
                    stdscr.addstr(h - 2, 0, "═" * (w - 1), curses.color_pair(2))
                    stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(2) | curses.A_BOLD)
                except curses.error:
                    pass
                stdscr.refresh()
                time.sleep(0.02)
        else:
            stdscr.erase()
            draw_maze(stdscr, maze, start, end, visited)
            try:
                stdscr.addstr(h - 2, 0, " ✗ No solution found! ", curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass
            stdscr.refresh()

        # Final display
        try:
            stdscr.addstr(h - 1, w - 35, "Press ENTER: new maze | Q: quit", curses.color_pair(8))
        except curses.error:
            pass
        stdscr.refresh()

        while True:
            key = stdscr.getch()
            if key in (curses.KEY_ENTER, 10, 13):
                break
            elif key in (ord('q'), ord('Q')):
                return


if __name__ == "__main__":
    curses.wrapper(main)


def main_entry():
    import curses
    curses.wrapper(main)

