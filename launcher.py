#!/usr/bin/env python3
"""🕹️ Terminal Arcade Launcher - Play all 30+ games from one menu!"""
import curses
import os
import sys
import subprocess

APPS = [
    # Games
    ("🐍 Snake", "snake.py", "Classic snake - eat, grow, survive!"),
    ("🎮 Tetris", "tetris.py", "Stack and clear lines with falling blocks"),
    ("🚀 Space Shooter", "space_shooter.py", "Arcade shooter with boss battles"),
    ("🎴 Blackjack", "blackjack.py", "21-point card game with betting"),
    ("⚡ Typing Test", "typing_test.py", "Test your WPM speed and accuracy"),
    ("🎮 2048", "game2048.py", "Merge tiles to reach 2048"),
    ("🎯 Minesweeper", "minesweeper.py", "Clear mines without exploding"),
    ("🏓 Pong", "pong.py", "Classic Pong vs AI opponent"),
    ("🔤 Wordle", "wordle.py", "Guess the 5-letter word"),
    ("🏃 Runner", "runner.py", "Endless obstacle runner"),
    ("🎲 RPG Battle", "rpg_battle.py", "Dice-rolling turn-based combat"),
    ("", "", ""),  # separator
    # Visualizations
    ("🌧️  Matrix Rain", "matrix.py", "The Matrix digital rain effect"),
    ("🌍 Spinning Globe", "globe.py", "Rotating 3D ASCII Earth"),
    ("🌊 Fluid Sim", "fluid.py", "Real-time fluid dynamics"),
    ("🐉 Particles", "particles.py", "Fire, fireworks, rain, snow, galaxy"),
    ("🎵 Music Viz", "music_viz.py", "Audio spectrum visualization"),
    ("🔮 Game of Life", "life.py", "Conway's cellular automaton"),
    ("🐚 Aquarium", "aquarium.py", "Peaceful ASCII fish tank"),
    ("🌲 Forest", "forest.py", "Day/night cycle forest scene"),
    ("🎪 Kaleidoscope", "kaleidoscope.py", "Symmetric color patterns"),
    ("🌀 Fractal", "fractal.py", "Mandelbrot & Julia set explorer"),
    ("🌌 Galaxy", "galaxy.py", "N-body gravitational simulation"),
    ("🧬 DNA Helix", "dna.py", "Rotating double helix animation"),
    ("⌚ Clock", "clock.py", "Big ASCII clock with themes"),
    ("🐱 Cat Pet", "catpet.py", "ASCII cat desktop companion"),
    ("", "", ""),  # separator
    # Tools
    ("🏰 Maze Solver", "maze.py", "Generate and solve mazes with A*"),
    ("🧮 Calculator", "calculator.py", "Scientific calc with graphing"),
    ("🎨 ASCII Art", "ascii_art.py", "Convert images to ASCII art"),
    ("📊 Git Stats", "git_stats.py", "Analyze repos, generate HTML report"),
    ("🎵 Piano", "piano.py", "Play piano with your keyboard"),
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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

    selected = 0
    scroll = 0
    search = ""
    filtered = list(range(len(APPS)))

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        # Header
        header = "╔══════════════════════════════════════════╗"
        title =  "║       🕹️  TERMINAL ARCADE LAUNCHER 🕹️     ║"
        footer = "╚══════════════════════════════════════════╝"
        draw_centered(stdscr, 0, header, curses.color_pair(3))
        draw_centered(stdscr, 1, title, curses.color_pair(3) | curses.A_BOLD)
        draw_centered(stdscr, 2, footer, curses.color_pair(3))

        # Search
        if search:
            draw_centered(stdscr, 3, f"Search: {search}_", curses.color_pair(4))

        # Filter
        if search:
            filtered = [i for i, (name, f, desc) in enumerate(APPS)
                       if name and search.lower() in (name + desc).lower()]
        else:
            filtered = list(range(len(APPS)))

        # Ensure selection is valid
        if filtered:
            # Skip separators
            while selected < len(filtered) and not APPS[filtered[selected]][0]:
                selected += 1
            if selected >= len(filtered):
                selected = 0
                while selected < len(filtered) and not APPS[filtered[selected]][0]:
                    selected += 1

        # Display list
        list_start = 5
        visible = h - 8
        if selected >= scroll + visible:
            scroll = selected - visible + 1
        if selected < scroll:
            scroll = selected

        for vi, fi in enumerate(filtered[scroll:scroll + visible]):
            y = list_start + vi
            name, filename, desc = APPS[fi]

            if not name:  # Separator
                draw_centered(stdscr, y, "─" * 40, curses.color_pair(8))
                continue

            is_selected = (fi == filtered[selected] if filtered else False)

            if is_selected:
                prefix = " ▶ "
                name_attr = curses.color_pair(2) | curses.A_BOLD
                desc_attr = curses.color_pair(4)
            else:
                prefix = "   "
                name_attr = curses.color_pair(7)
                desc_attr = curses.color_pair(8)

            try:
                x = max(2, (w - 60) // 2)
                stdscr.addstr(y, x, prefix, curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(y, x + 3, name, name_attr)
                if w > 50:
                    stdscr.addstr(y, x + 25, desc[:w - x - 28], desc_attr)
            except curses.error:
                pass

        # Footer
        try:
            controls = " ↑/↓:Navigate  ENTER:Launch  /:Search  Q:Quit "
            stdscr.addstr(h - 2, max(0, (w - len(controls)) // 2), controls, curses.color_pair(8))
            count = f" {len([a for a in APPS if a[0]])} apps available "
            stdscr.addstr(h - 1, max(0, (w - len(count)) // 2), count, curses.color_pair(3))
        except curses.error:
            pass

        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord('q'), ord('Q')) and not search:
            break
        elif key == 27:  # ESC
            if search:
                search = ""
            else:
                break
        elif key == curses.KEY_UP or key == ord('k'):
            if filtered:
                selected = max(0, selected - 1)
                while selected > 0 and not APPS[filtered[selected]][0]:
                    selected -= 1
        elif key == curses.KEY_DOWN or key == ord('j'):
            if filtered:
                selected = min(len(filtered) - 1, selected + 1)
                while selected < len(filtered) - 1 and not APPS[filtered[selected]][0]:
                    selected += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            if filtered and APPS[filtered[selected]][0]:
                filename = APPS[filtered[selected]][1]
                filepath = os.path.join(BASE_DIR, filename)
                if os.path.exists(filepath):
                    curses.endwin()
                    subprocess.run([sys.executable, filepath])
                    stdscr = curses.initscr()
                    curses.noecho()
                    curses.cbreak()
                    stdscr.keypad(True)
                    curses.curs_set(0)
        elif key == ord('/'):
            search = ""
            selected = 0
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            search = search[:-1]
            selected = 0
        elif search is not None and 32 <= key <= 126:
            if search or key == ord('/'):
                search += chr(key)
                selected = 0
            elif chr(key) == '/':
                search = ""


if __name__ == "__main__":
    curses.wrapper(main)
