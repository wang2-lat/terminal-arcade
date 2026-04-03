#!/usr/bin/env python3
"""
Rotating 3D ASCII Earth Globe with recognizable continents.
Controls: q=quit, +/-=speed, c=toggle color

Features:
  - Proper 3D sphere with orthographic projection
  - Continent outlines from bitmap world map
  - Directional lighting with shading
  - Color support (blue ocean, green land, white poles)
  - Latitude/longitude grid lines
  - Smooth animation with curses
"""

import curses
import math
import time

# ---------------------------------------------------------------------------
# World map bitmap at ~4-degree resolution.
# 90 columns (lon -180..+176 step 4) x 45 rows (lat +88..-88 step 4).
# '#' = land, ' ' = ocean. Each row is exactly 90 characters.
# ---------------------------------------------------------------------------

_MAP = [
    #         1111111111222222222233333333334444444444555555555566666666667777777777888888888
    #1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
    "                                                                                          ",  # +88
    "                                  ####                                                    ",  # +84
    "                                  #####                                                   ",  # +80
    "            ###                   ##########              ##################################",  # +76
    "           #####                  ###########    ############################################",  # +72
    "          ########        ##      ###########  ############################################",  # +68
    "         ##########      #####    ############ ####  ####################################  ",  # +64
    "        ###########     ########  #############  ######  #################################  ",  # +60
    "        ############   ###########  ################### ##################################  ",  # +56
    "        #############  ############  ########### #####  ###################################",  # +52
    "         ############# #############  ##########  ###  ###################  ###############",  # +48
    "          ############ ###############  ########  ##  #################  # #####           ",  # +44
    "           ########### ###############  ########  ##  #############################       ",  # +40
    "            ########### ##############   ##############  ##########################        ",  # +36
    "            ###########  ###############  ##############  ##########################       ",  # +32
    "             ##########  ###############  ################ ########################        ",  # +28
    "              #########  ##############   ################  ##############   ##            ",  # +24
    "                ############ ######     ######################  ##########   ##            ",  # +20
    "                  #########  ######    ##############   ####   ######  ###   ##            ",  # +16
    "                         ##    ####    ###############  ####   #####   ###   ##            ",  # +12
    "                         ##    ###     ###################     #####   ##    ##            ",  #  +8
    "                          ######       ###################             ########            ",  #  +4
    "                          ##########   #####################           ########   ####     ",  #   0
    "                          ##########   #####################           ########   ####     ",  #  -4
    "                          ##########   #####################            #####      ###     ",  #  -8
    "                          ##########    #####################                ###########   ",  # -12
    "                           #########   #####################                ###########   ",  # -16
    "                            ########    ####################                ##########    ",  # -20
    "                             ########           ########  ##                ##########    ",  # -24
    "                              #######           ########                    ##########    ",  # -28
    "                              ########           ######                     ##########   # ",  # -32
    "                                ######           #####                          ######   # ",  # -36
    "                                  ####                                          #####   ## ",  # -40
    "                                                                                       ## ",  # -44
    "                                                                                       #  ",  # -48
    "                                                                                          ",  # -52
    "                                                                                          ",  # -56
    "                                                                                          ",  # -60
    "                                                                                          ",  # -64
    "                                                                                          ",  # -68
    "                                                                                          ",  # -72
    "                                                                                          ",  # -76
    "                                                                                          ",  # -80
    "                                                                                          ",  # -84
    "                                                                                          ",  # -88
]

MAP_ROWS = len(_MAP)        # 45
MAP_LAT_STEP = 4
MAP_LON_STEP = 4
MAP_LAT_MAX = 88


def is_land(lat, lon):
    """Check if (lat, lon) falls on land in the bitmap."""
    if lat > MAP_LAT_MAX:
        lat = MAP_LAT_MAX
    if lat < -MAP_LAT_MAX:
        lat = -MAP_LAT_MAX
    while lon > 180:
        lon -= 360
    while lon < -180:
        lon += 360

    row = int((MAP_LAT_MAX - lat) / MAP_LAT_STEP + 0.5)
    col = int((lon + 180) / MAP_LON_STEP + 0.5)

    row = max(0, min(MAP_ROWS - 1, row))
    r = _MAP[row]
    col = max(0, min(len(r) - 1, col))
    return r[col] == '#'


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

SHADE_OCEAN = [' ', ' ', '.', '~', '~', '-', '=']
SHADE_LAND  = [' ', ' ', '.', ':', 'o', '#', '@']

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

    # Light direction (upper-right, in front) -- normalized
    lx, ly, lz = 0.6, -0.3, -0.7
    lm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx /= lm
    ly /= lm
    lz /= lm

    # Cached sphere geometry (rebuilt on terminal resize)
    cached_w = cached_h = -1
    sphere_map = None   # list of (screen_y, screen_x, norm_x, norm_y, norm_z)

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

        # Rebuild sphere pixel geometry on terminal resize
        if draw_w != cached_w or draw_h != cached_h:
            cached_w = draw_w
            cached_h = draw_h

            # Terminal chars are ~2x taller than wide
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
                        nz = math.sqrt(1.0 - d2)
                        sphere_map.append((sy, sx, nx, ny, nz))

        cos_a = math.cos(rotation)
        sin_a = math.sin(rotation)

        stdscr.erase()

        for sy, sx, nx, ny, nz in sphere_map:
            # Y-axis rotation
            rx_ = nx * cos_a + nz * sin_a
            rz_ = -nx * sin_a + nz * cos_a

            # Lat/lon from rotated point
            lat = math.degrees(math.asin(max(-1.0, min(1.0, -ny))))
            lon = math.degrees(math.atan2(rx_, rz_))

            # Lighting (in view/screen space)
            dot = nx * lx + ny * ly + nz * lz
            brightness = max(0.0, min(1.0, dot))
            shade = int(brightness * 6.0)
            shade = max(0, min(6, shade))

            land = is_land(lat, lon)
            pole = abs(lat) > 72

            # Grid lines (every 30 degrees)
            on_grid = False
            if shade >= 2:
                lat_m = abs(lat % 30)
                lon_m = abs(lon % 30)
                if lat_m < 3.0 or lat_m > 27.0 or lon_m < 3.0 or lon_m > 27.0:
                    on_grid = True

            # Character selection
            if shade == 0:
                ch = ' '
            elif pole:
                ch = SHADE_LAND[shade]
            elif land:
                ch = SHADE_LAND[shade]
            else:
                ch = SHADE_OCEAN[shade]
                if on_grid and shade >= 3:
                    ch = '.'

            # Color selection
            attr = 0
            if color_on:
                if pole:
                    attr = curses.color_pair(C_POLE)
                    if brightness > 0.6:
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


def main_entry():
    import curses
    curses.wrapper(main)

