#!/usr/bin/env python3
"""🎵 Terminal Piano - Play music with your keyboard!"""
import curses
import time
import math
import subprocess
import threading

# Keyboard mapping to notes
KEY_MAP = {
    ord('a'): ('C4', 261.63),
    ord('w'): ('C#4', 277.18),
    ord('s'): ('D4', 293.66),
    ord('e'): ('D#4', 311.13),
    ord('d'): ('E4', 329.63),
    ord('f'): ('F4', 349.23),
    ord('t'): ('F#4', 369.99),
    ord('g'): ('G4', 392.00),
    ord('y'): ('G#4', 415.30),
    ord('h'): ('A4', 440.00),
    ord('u'): ('A#4', 466.16),
    ord('j'): ('B4', 493.88),
    ord('k'): ('C5', 523.25),
    ord('o'): ('C#5', 554.37),
    ord('l'): ('D5', 587.33),
    ord('p'): ('D#5', 622.25),
    ord(';'): ('E5', 659.25),
}

# Visual note for falling animation
class FallingNote:
    def __init__(self, x, color, note_name):
        self.x = x
        self.y = 0
        self.color = color
        self.note_name = note_name
        self.alive = True
        self.speed = 0.5

    def update(self, dt, max_y):
        self.y += self.speed * dt * 20
        if self.y > max_y:
            self.alive = False

    def draw(self, stdscr, h, w):
        iy = int(self.y)
        if 0 <= iy < h and 0 <= self.x < w:
            try:
                stdscr.addstr(iy, self.x, "♪", curses.color_pair(self.color) | curses.A_BOLD)
            except curses.error:
                pass


def play_tone(frequency, duration=0.15):
    """Play a tone using macOS afplay or just visual feedback."""
    try:
        # Generate a simple tone using sox if available
        subprocess.Popen(
            ['play', '-n', '-q', 'synth', str(duration), 'pluck', str(frequency)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass  # No sox installed, visual only


# Piano key layout
WHITE_KEYS = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';']
BLACK_KEYS = ['w', 'e', '', 't', 'y', 'u', '', 'o', 'p', '']
NOTE_NAMES = ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C', 'D', 'E']


def draw_piano(stdscr, piano_y, piano_x, h, w, pressed_keys):
    key_width = 5
    key_height = 8

    # White keys
    for i, key in enumerate(WHITE_KEYS):
        x = piano_x + i * key_width
        is_pressed = ord(key) in pressed_keys if key else False

        color = curses.color_pair(2) | curses.A_BOLD if is_pressed else curses.color_pair(7)
        fill = "█" if is_pressed else "│"

        for dy in range(key_height):
            try:
                if dy == 0:
                    stdscr.addstr(piano_y + dy, x, "┌" + "───" + "┐", color)
                elif dy == key_height - 1:
                    stdscr.addstr(piano_y + dy, x, "└" + "───" + "┘", color)
                elif dy == key_height - 3:
                    note = NOTE_NAMES[i] if i < len(NOTE_NAMES) else ""
                    stdscr.addstr(piano_y + dy, x, f"│ {note} │", color)
                elif dy == key_height - 2:
                    stdscr.addstr(piano_y + dy, x, f"│ {key.upper()} │", curses.color_pair(8))
                else:
                    stdscr.addstr(piano_y + dy, x, f"│   │", color)
            except curses.error:
                pass

    # Black keys
    for i, key in enumerate(BLACK_KEYS):
        if not key:
            continue
        x = piano_x + i * key_width + 3
        is_pressed = ord(key) in pressed_keys

        color = curses.color_pair(1) | curses.A_BOLD if is_pressed else curses.color_pair(8)

        for dy in range(key_height - 3):
            try:
                if dy == 0:
                    stdscr.addstr(piano_y + dy, x, "┌──┐", color)
                elif dy == key_height - 4:
                    stdscr.addstr(piano_y + dy, x, f"└{key.upper()}─┘", color)
                else:
                    ch = "████" if is_pressed else "│██│"
                    stdscr.addstr(piano_y + dy, x, ch, color)
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

    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    falling_notes = []
    pressed_keys = set()
    last_time = time.time()
    played_notes = []  # History

    piano_x = max(0, (w - 50) // 2)
    piano_y = h - 12

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now

        # Collect keys
        new_keys = set()
        while True:
            try:
                k = stdscr.getch()
                if k == -1:
                    break
                new_keys.add(k)
            except:
                break

        if ord('q') in new_keys or ord('Q') in new_keys:
            break

        # Play notes for newly pressed keys
        for k in new_keys:
            if k in KEY_MAP:
                note_name, freq = KEY_MAP[k]
                # Play sound in background
                threading.Thread(target=play_tone, args=(freq,), daemon=True).start()

                # Add falling note
                key_char = chr(k)
                if key_char in WHITE_KEYS:
                    idx = WHITE_KEYS.index(key_char)
                    note_x = piano_x + idx * 5 + 2
                elif key_char in BLACK_KEYS:
                    idx = BLACK_KEYS.index(key_char)
                    note_x = piano_x + idx * 5 + 4
                else:
                    note_x = w // 2

                color = random.choice([1, 2, 3, 4, 5, 6]) if hasattr(random, 'choice') else 3
                import random as _r
                color = _r.choice([1, 2, 3, 4, 5, 6])
                falling_notes.append(FallingNote(note_x, color, note_name))
                played_notes.append(note_name)
                if len(played_notes) > 30:
                    played_notes.pop(0)

        pressed_keys = new_keys

        # Update falling notes
        for note in falling_notes:
            note.update(dt, piano_y - 1)
        falling_notes = [n for n in falling_notes if n.alive]

        # Draw
        stdscr.erase()

        # Title
        title = "🎵 TERMINAL PIANO 🎵"
        try:
            stdscr.addstr(0, max(0, (w - len(title)) // 2), title, curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

        # Falling notes
        for note in falling_notes:
            note.draw(stdscr, h, w)

        # Note history
        if played_notes:
            history = " ".join(played_notes[-20:])
            try:
                stdscr.addstr(2, max(0, (w - len(history)) // 2), history, curses.color_pair(4))
            except curses.error:
                pass

        # Piano
        draw_piano(stdscr, piano_y, piano_x, h, w, pressed_keys)

        # Status
        try:
            status = " White: A S D F G H J K L ;  |  Black: W E T Y U O P  |  Q: Quit "
            stdscr.addstr(h - 1, max(0, (w - len(status)) // 2), status, curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.03)


import random

if __name__ == "__main__":
    curses.wrapper(main)
