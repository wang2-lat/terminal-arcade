#!/usr/bin/env python3
"""
Rotating 3D ASCII Earth Globe with recognizable continents.
Controls: q=quit, +/-=speed, c=toggle color

Features:
  - Proper 3D sphere with orthographic projection
  - Continent outlines from bitmap world map
  - Directional lighting with depth shading
  - Color support (blue ocean, green land, white poles)
  - Latitude/longitude grid lines
  - Smooth animation with curses (~24 fps target)
"""

import curses
import math
import time
import zlib
import base64

# ---------------------------------------------------------------------------
# World map: 90x45 bitmap. Compressed via zlib+base64.
# 90 cols = lon -180..+176 (step 4), 45 rows = lat +88..-88 (step 4).
# Decoded as flat bytes: grid[row * 90 + col] == 1 means land.
# ---------------------------------------------------------------------------

_MAP_B64 = (
    "eNrtlsEOxCAIROH/f7qHzVpRwJlWt3HTubSp+DRlUESek360DVlPxSOOoCATrEoE"
    "U+FKyA0vK5rRNWQhsUOyyRxP7meOyNAyQyMFDmzpPSF1aeJtl1ySk1YGSa7STZM"
    "Fc3dazeU1J+scskOAqdKXRf6nKLIhBN/rHTQLzSILS25pI/LXak+Tq1zGZ745Dy/d"
    "U9F5F1nqLrmPX0b2qwAm57uGKuYPybKOzPRTYDeHkvX35MqkZJPZPOeRsalL+vFt"
    "ya9ebaYDf5AFKA=="
)
_MAP_W, _MAP_H = 90, 45
_MAP_LAT_STEP, _MAP_LON_STEP = 4, 4
_MAP_LAT_MAX = 88

# Decode at import time
_MAP_DATA = zlib.decompress(base64.b64decode(_MAP_B64))


def is_land(lat, lon):
    """Check if (lat, lon) falls on land in the world bitmap."""
    if lat > _MAP_LAT_MAX:
        lat = _MAP_LAT_MAX
    elif lat < -_MAP_LAT_MAX:
        lat = -_MAP_LAT_MAX
    if lon > 180:
        lon -= 360 * ((lon + 180) // 360)
    elif lon < -180:
        lon += 360 * ((-lon + 180) // 360)

    row = int((_MAP_LAT_MAX - lat) / _MAP_LAT_STEP + 0.5)
    col = int((lon + 180) / _MAP_LON_STEP + 0.5)

    if row < 0:
        row = 0
    elif row >= _MAP_H:
        row = _MAP_H - 1
    if col < 0:
        col = 0
    elif col >= _MAP_W:
        col = _MAP_W - 1

    return _MAP_DATA[row * _MAP_W + col] == 1


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

# Shading chars from dark (index 0) to bright (index 6)
SHADE_OCEAN = (' ', ' ', '.', '~', '~', '-', '=')
SHADE_LAND  = (' ', ' ', '.', ':', 'o', '#', '@')

# Color pair IDs
C_OCEAN      = 1
C_LAND       = 2
C_POLE       = 3
C_GRID       = 4
C_OCEAN_DARK = 5
C_LAND_DARK  = 6
C_BAR        = 7


def setup_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_OCEAN,      curses.COLOR_CYAN,   -1)
    curses.init_pair(C_LAND,       curses.COLOR_GREEN,  -1)
    curses.init_pair(C_POLE,       curses.COLOR_WHITE,  -1)
    curses.init_pair(C_GRID,       curses.COLOR_BLUE,   -1)
    curses.init_pair(C_OCEAN_DARK, curses.COLOR_BLUE,   -1)
    curses.init_pair(C_LAND_DARK,  curses.COLOR_YELLOW, -1)
    curses.init_pair(C_BAR,        curses.COLOR_WHITE,  -1)


def render_globe(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    setup_colors()

    rotation = 0.0
    speed = 0.04          # radians per frame
    color_on = True
    target_fps = 24
    frame_dt = 1.0 / target_fps

    # Light direction (upper-right, in front of sphere) -- normalized
    lx, ly, lz = 0.6, -0.3, -0.7
    lm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx /= lm
    ly /= lm
    lz /= lm

    # Sphere pixel geometry (rebuilt on terminal resize)
    cached_w = cached_h = -1
    sphere_map = None  # [(screen_y, screen_x, norm_x, norm_y, norm_z), ...]

    # Precompute degrees conversion factor
    _RAD2DEG = 180.0 / math.pi
    _asin = math.asin
    _atan2 = math.atan2
    _sqrt = math.sqrt
    _cos = math.cos
    _sin = math.sin

    while True:
        t0 = time.monotonic()

        try:
            max_y, max_x = stdscr.getmaxyx()
        except Exception:
            break

        draw_h = max_y - 1  # reserve last row for status bar
        draw_w = max_x

        if draw_h < 6 or draw_w < 12:
            stdscr.erase()
            try:
                stdscr.addstr(0, 0, "Terminal too small")
            except curses.error:
                pass
            stdscr.refresh()
            time.sleep(0.2)
            if stdscr.getch() == ord('q'):
                return
            continue

        # Rebuild sphere pixel map on terminal resize
        if draw_w != cached_w or draw_h != cached_h:
            cached_w = draw_w
            cached_h = draw_h

            # Terminal chars are roughly 2x taller than wide
            char_aspect = 2.1
            ry = draw_h / 2.0 - 1.0
            rx = ry * char_aspect
            if rx > draw_w / 2.0 - 2:
                rx = draw_w / 2.0 - 2
                ry = rx / char_aspect

            cx = draw_w / 2.0
            cy = draw_h / 2.0

            sphere_map = []
            for sy in range(draw_h):
                for sx in range(draw_w):
                    nx = (sx - cx) / rx
                    ny = (sy - cy) / ry
                    d2 = nx * nx + ny * ny
                    if d2 <= 1.0:
                        nz = _sqrt(1.0 - d2)
                        sphere_map.append((sy, sx, nx, ny, nz))

        cos_a = _cos(rotation)
        sin_a = _sin(rotation)

        stdscr.erase()

        for sy, sx, nx, ny, nz in sphere_map:
            # Rotate around Y axis
            rx_ = nx * cos_a + nz * sin_a
            rz_ = -nx * sin_a + nz * cos_a

            # Convert to geographic coordinates
            clamped_ny = ny if -1.0 <= ny <= 1.0 else max(-1.0, min(1.0, ny))
            lat = -_asin(clamped_ny) * _RAD2DEG
            lon = _atan2(rx_, rz_) * _RAD2DEG

            # Directional lighting (computed in view space)
            dot = nx * lx + ny * ly + nz * lz
            if dot < 0.0:
                shade = 0
            else:
                if dot > 1.0:
                    dot = 1.0
                shade = int(dot * 6.0)
                if shade > 6:
                    shade = 6

            land = is_land(lat, lon)
            pole = abs(lat) > 72

            # Grid lines every 30 degrees
            on_grid = False
            if shade >= 2:
                lat_m = abs(lat % 30)
                lon_m = abs(lon % 30)
                if lat_m < 3.0 or lat_m > 27.0 or lon_m < 3.0 or lon_m > 27.0:
                    on_grid = True

            # Character
            if shade == 0:
                ch = ' '
            elif land or pole:
                ch = SHADE_LAND[shade]
            else:
                ch = SHADE_OCEAN[shade]
                if on_grid and shade >= 3:
                    ch = '.'

            # Color attribute
            attr = 0
            if color_on:
                if pole:
                    attr = curses.color_pair(C_POLE)
                    if dot > 0.6:
                        attr |= curses.A_BOLD
                elif land:
                    if shade <= 2:
                        attr = curses.color_pair(C_LAND_DARK)
                    else:
                        attr = curses.color_pair(C_LAND)
                        if shade >= 5:
                            attr |= curses.A_BOLD
                else:
                    if on_grid and shade >= 3:
                        attr = curses.color_pair(C_GRID)
                    elif shade <= 2:
                        attr = curses.color_pair(C_OCEAN_DARK)
                    else:
                        attr = curses.color_pair(C_OCEAN)

            try:
                stdscr.addch(sy, sx, ch, attr)
            except curses.error:
                pass

        # Status bar
        elapsed = time.monotonic() - t0
        fps_now = 1.0 / max(elapsed, 0.001)
        bar = (
            f"  Earth Globe | Speed {speed:.3f} | FPS {fps_now:3.0f}"
            f" | Color {'ON' if color_on else 'OFF'}"
            f" | q:quit  +/-:speed  c:color"
        )
        try:
            a = (curses.color_pair(C_BAR) | curses.A_BOLD) if color_on else curses.A_BOLD
            stdscr.addnstr(max_y - 1, 0, bar.ljust(max_x - 1), max_x - 1, a)
        except curses.error:
            pass

        stdscr.refresh()
        rotation += speed

        # Input handling
        k = stdscr.getch()
        while k != -1:
            if k in (ord('q'), ord('Q')):
                return
            elif k in (ord('+'), ord('=')):
                speed = min(speed + 0.01, 0.30)
            elif k in (ord('-'), ord('_')):
                speed = max(speed - 0.01, 0.005)
            elif k in (ord('c'), ord('C')):
                color_on = not color_on
            k = stdscr.getch()

        # Frame limiter
        t_frame = time.monotonic() - t0
        if t_frame < frame_dt:
            time.sleep(frame_dt - t_frame)


def main(stdscr):
    render_globe(stdscr)


if __name__ == "__main__":
    curses.wrapper(main)
