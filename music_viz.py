#!/usr/bin/env python3
"""🎵 Terminal Music Spectrum Visualizer - Colorful audio-style visualization"""
import curses
import math
import time
import random


class SpectrumGenerator:
    """Generate realistic-looking audio spectrum data."""

    def __init__(self, num_bars):
        self.num_bars = num_bars
        self.values = [0.0] * num_bars
        self.peaks = [0.0] * num_bars
        self.peak_decay = 0.02
        self.smoothing = 0.3
        self.t = 0
        self.beat_phase = 0
        self.beat_bpm = random.choice([110, 120, 128, 140, 160])
        self.beat_energy = 0
        self.song_phase = 0  # 0=buildup, 1=drop, 2=break
        self.song_timer = 0
        self.base_freqs = [random.uniform(0.5, 3.0) for _ in range(num_bars)]

    def generate(self, dt):
        self.t += dt
        self.beat_phase += dt * self.beat_bpm / 60 * math.pi * 2

        # Song structure
        self.song_timer += dt
        if self.song_timer > 8:
            self.song_timer = 0
            self.song_phase = (self.song_phase + 1) % 3
            if self.song_phase == 1:  # Drop
                self.beat_bpm = random.choice([128, 140, 150, 160])

        # Beat energy
        beat = (math.sin(self.beat_phase) + 1) / 2
        kick = max(0, math.sin(self.beat_phase)) ** 4
        snare = max(0, math.sin(self.beat_phase * 0.5 + math.pi)) ** 8

        if self.song_phase == 0:  # Buildup
            self.beat_energy = 0.3 + 0.3 * (self.song_timer / 8)
        elif self.song_phase == 1:  # Drop
            self.beat_energy = 0.8 + 0.2 * kick
        else:  # Break
            self.beat_energy = 0.2 + 0.1 * beat

        for i in range(self.num_bars):
            freq = self.base_freqs[i]
            # Low frequencies respond to kick
            if i < self.num_bars * 0.2:
                target = kick * self.beat_energy * 0.9
            # Mid frequencies
            elif i < self.num_bars * 0.6:
                wave = math.sin(self.t * freq + i * 0.5) * 0.5 + 0.5
                target = wave * self.beat_energy * 0.7
            # High frequencies respond to snare/hats
            else:
                hat = random.random() * 0.5 * beat
                target = (snare * 0.6 + hat) * self.beat_energy

            target += random.gauss(0, 0.02)
            target = max(0, min(1, target))

            # Smooth
            self.values[i] = self.values[i] * self.smoothing + target * (1 - self.smoothing)

            # Peak tracking
            if self.values[i] > self.peaks[i]:
                self.peaks[i] = self.values[i]
            else:
                self.peaks[i] = max(0, self.peaks[i] - self.peak_decay)

        return self.values, self.peaks


VIZ_MODES = ["bars", "mirror", "wave", "circle"]
COLOR_SCHEMES = ["rainbow", "fire", "ice", "neon", "mono"]


def get_bar_color(value, bar_idx, num_bars, scheme, t):
    if scheme == "rainbow":
        hue = (bar_idx / num_bars * 6 + t * 0.5) % 6
        return int(hue) % 7 + 1
    elif scheme == "fire":
        if value > 0.7:
            return 4  # yellow
        elif value > 0.4:
            return 5  # red
        else:
            return 5  # dark red
    elif scheme == "ice":
        if value > 0.6:
            return 7  # white
        elif value > 0.3:
            return 2  # cyan
        else:
            return 1  # blue
    elif scheme == "neon":
        colors = [6, 2, 3, 4, 5]  # magenta, cyan, green, yellow, red
        return colors[bar_idx % len(colors)]
    else:  # mono
        return 3  # green


BAR_CHARS = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]


def draw_bars(stdscr, values, peaks, h, w, scheme, t):
    num_bars = len(values)
    bar_w = max(1, (w - 2) // num_bars)
    max_h = h - 4

    for i, (val, peak) in enumerate(zip(values, peaks)):
        bar_h = int(val * max_h)
        peak_y = int(peak * max_h)
        x = 1 + i * bar_w
        color = get_bar_color(val, i, num_bars, scheme, t)

        # Draw bar
        for dy in range(bar_h):
            y = h - 3 - dy
            if 0 <= y < h - 2:
                ch = "█" * min(bar_w - 1, w - x - 1)
                if ch:
                    try:
                        intensity = curses.A_BOLD if dy > bar_h * 0.7 else 0
                        stdscr.addstr(y, x, ch, curses.color_pair(color) | intensity)
                    except curses.error:
                        pass

        # Draw peak
        peak_row = h - 3 - peak_y
        if 0 <= peak_row < h - 2:
            try:
                stdscr.addstr(peak_row, x, "─" * min(bar_w - 1, w - x - 1),
                             curses.color_pair(7) | curses.A_BOLD)
            except curses.error:
                pass


def draw_mirror(stdscr, values, peaks, h, w, scheme, t):
    num_bars = len(values)
    bar_w = max(1, (w - 2) // num_bars)
    mid_y = (h - 3) // 2
    max_h = mid_y - 1

    for i, val in enumerate(values):
        bar_h = int(val * max_h)
        x = 1 + i * bar_w
        color = get_bar_color(val, i, num_bars, scheme, t)
        ch = "█" * min(bar_w - 1, w - x - 1)
        if not ch:
            continue

        for dy in range(bar_h):
            try:
                # Top half
                y_up = mid_y - dy - 1
                if 0 <= y_up:
                    stdscr.addstr(y_up, x, ch, curses.color_pair(color))
                # Bottom half
                y_down = mid_y + dy + 1
                if y_down < h - 2:
                    stdscr.addstr(y_down, x, ch, curses.color_pair(color))
            except curses.error:
                pass

        # Center line
        try:
            stdscr.addstr(mid_y, x, ch, curses.color_pair(7) | curses.A_DIM)
        except curses.error:
            pass


def draw_wave(stdscr, values, peaks, h, w, scheme, t):
    mid_y = (h - 3) // 2
    amp = (h - 6) // 2

    for x in range(1, w - 1):
        idx = int(x / w * len(values))
        idx = min(idx, len(values) - 1)
        val = values[idx]

        y = int(mid_y - math.sin(x * 0.1 + t * 3) * val * amp)
        y2 = int(mid_y + math.cos(x * 0.08 + t * 2.5) * val * amp * 0.7)

        color = get_bar_color(val, idx, len(values), scheme, t)
        try:
            if 0 <= y < h - 2:
                stdscr.addstr(y, x, "●", curses.color_pair(color) | curses.A_BOLD)
            if 0 <= y2 < h - 2:
                stdscr.addstr(y2, x, "○", curses.color_pair(color))
        except curses.error:
            pass


def draw_circle(stdscr, values, peaks, h, w, scheme, t):
    cx, cy = w // 2, (h - 3) // 2
    base_r = min(cx, cy) * 0.3

    for i, val in enumerate(values):
        angle = (i / len(values)) * math.pi * 2 + t * 0.5
        r = base_r + val * base_r * 1.5

        x = int(cx + math.cos(angle) * r * 2)  # *2 for char aspect ratio
        y = int(cy + math.sin(angle) * r)

        color = get_bar_color(val, i, len(values), scheme, t)

        # Draw line from center to point
        steps = int(r * 1.5)
        for s in range(steps):
            frac = s / max(1, steps)
            lx = int(cx + math.cos(angle) * (base_r + (r - base_r) * frac) * 2)
            ly = int(cy + math.sin(angle) * (base_r + (r - base_r) * frac))
            if 0 <= ly < h - 2 and 0 <= lx < w - 1:
                ch = "█" if frac > 0.8 else "▓" if frac > 0.5 else "░"
                try:
                    stdscr.addstr(ly, lx, ch, curses.color_pair(color))
                except curses.error:
                    pass


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_BLUE, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    stdscr.nodelay(True)
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    num_bars = min(64, (w - 2) // 2)
    spectrum = SpectrumGenerator(num_bars)

    viz_mode = 0
    color_scheme = 0
    t = 0
    last_time = time.time()

    draw_funcs = [draw_bars, draw_mirror, draw_wave, draw_circle]

    while True:
        now = time.time()
        dt = now - last_time
        last_time = now
        t += dt

        try:
            key = stdscr.getch()
        except:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord('v') or key == ord('V'):
            viz_mode = (viz_mode + 1) % len(VIZ_MODES)
        elif key == ord('c') or key == ord('C'):
            color_scheme = (color_scheme + 1) % len(COLOR_SCHEMES)
        elif key == ord('b') or key == ord('B'):
            spectrum.beat_bpm = random.choice([110, 120, 128, 140, 150, 160, 170])

        h, w = stdscr.getmaxyx()
        values, peaks = spectrum.generate(dt)

        stdscr.erase()

        # Draw visualization
        scheme = COLOR_SCHEMES[color_scheme]
        draw_funcs[viz_mode](stdscr, values, peaks, h, w, scheme, t)

        # Status bar
        try:
            bar = f" 🎵 {VIZ_MODES[viz_mode].upper()} | {scheme.upper()} | {spectrum.beat_bpm} BPM | "
            phases = ["BUILDUP", "  DROP ", " BREAK "]
            bar += f"{phases[spectrum.song_phase]} | V:Viz C:Color B:BPM Q:Quit "
            stdscr.addstr(h - 1, 0, bar[:w-1], curses.color_pair(8))

            # Beat indicator
            beat_x = len(bar)
            if beat_x < w - 5:
                beat_char = "♫ " if spectrum.beat_energy > 0.5 else "♪ "
                stdscr.addstr(h - 1, min(beat_x, w - 3), beat_char,
                             curses.color_pair(5 if spectrum.beat_energy > 0.7 else 4) | curses.A_BOLD)
        except curses.error:
            pass

        stdscr.refresh()
        time.sleep(0.03)


if __name__ == "__main__":
    curses.wrapper(main)
