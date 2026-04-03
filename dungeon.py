#!/usr/bin/env python3
"""Roguelike Dungeon Crawler — terminal-based with curses, BSP generation, fog of war."""

import curses
import random
import math
import sys
import time

# ---------------------------------------------------------------------------
# Tile constants
# ---------------------------------------------------------------------------
WALL = "#"
FLOOR = "."
CORRIDOR = ","
STAIRS = ">"
EMPTY = " "

# ---------------------------------------------------------------------------
# Color pair IDs
# ---------------------------------------------------------------------------
C_DEFAULT = 0
C_WALL = 1
C_FLOOR = 2
C_PLAYER = 3
C_RAT = 4
C_GOBLIN = 5
C_SKELETON = 6
C_DRAGON = 7
C_POTION = 8
C_GOLD = 9
C_WEAPON = 10
C_ARMOR = 11
C_STAIRS = 12
C_FOG = 13
C_MSG = 14
C_TITLE = 15
C_UI = 16
C_MINIMAP_WALL = 17
C_MINIMAP_ROOM = 18
C_MINIMAP_PLAYER = 19
C_DEAD = 20
C_SUBTITLE = 21

# ---------------------------------------------------------------------------
# Monster templates  (name, char, hp, atk, def, xp, color_pair)
# ---------------------------------------------------------------------------
MONSTER_TEMPLATES = {
    "Rat":      {"ch": "r", "hp": 8,  "atk": 2, "dfn": 0, "xp": 5,  "col": C_RAT,      "min_level": 1},
    "Goblin":   {"ch": "g", "hp": 15, "atk": 4, "dfn": 1, "xp": 12, "col": C_GOBLIN,   "min_level": 1},
    "Skeleton": {"ch": "S", "hp": 25, "atk": 6, "dfn": 3, "xp": 25, "col": C_SKELETON, "min_level": 2},
    "Dragon":   {"ch": "D", "hp": 60, "atk": 12,"dfn": 6, "xp": 100,"col": C_DRAGON,   "min_level": 4},
}

# ---------------------------------------------------------------------------
# Item templates  (name, char, color_pair, effect_key, effect_range)
# ---------------------------------------------------------------------------
ITEM_TEMPLATES = [
    {"name": "Health Potion", "ch": "h", "col": C_POTION, "effect": "hp",  "range": (10, 25)},
    {"name": "Gold Pile",     "ch": "$", "col": C_GOLD,   "effect": "gold","range": (5, 30)},
    {"name": "Weapon",        "ch": "w", "col": C_WEAPON, "effect": "atk", "range": (1, 3)},
    {"name": "Armor",         "ch": "a", "col": C_ARMOR,  "effect": "def", "range": (1, 3)},
]

# ---------------------------------------------------------------------------
# BSP dungeon generation
# ---------------------------------------------------------------------------
class BSPNode:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.left = None
        self.right = None
        self.room = None

    def split(self, depth=0, max_depth=5):
        if depth >= max_depth:
            return
        if self.w < 12 and self.h < 12:
            return

        horizontal = random.random() < 0.5
        if self.w / self.h >= 1.25:
            horizontal = False
        elif self.h / self.w >= 1.25:
            horizontal = True

        if horizontal:
            if self.h < 12:
                return
            split_pos = random.randint(5, self.h - 5)
            self.left = BSPNode(self.x, self.y, self.w, split_pos)
            self.right = BSPNode(self.x, self.y + split_pos, self.w, self.h - split_pos)
        else:
            if self.w < 12:
                return
            split_pos = random.randint(5, self.w - 5)
            self.left = BSPNode(self.x, self.y, split_pos, self.h)
            self.right = BSPNode(self.x + split_pos, self.y, self.w - split_pos, self.h)

        self.left.split(depth + 1, max_depth)
        self.right.split(depth + 1, max_depth)

    def create_rooms(self):
        if self.left or self.right:
            if self.left:
                self.left.create_rooms()
            if self.right:
                self.right.create_rooms()
        else:
            rw = random.randint(4, max(4, self.w - 2))
            rh = random.randint(4, max(4, self.h - 2))
            rx = self.x + random.randint(1, max(1, self.w - rw - 1))
            ry = self.y + random.randint(1, max(1, self.h - rh - 1))
            self.room = (rx, ry, rw, rh)

    def get_rooms(self):
        rooms = []
        if self.room:
            rooms.append(self.room)
        if self.left:
            rooms.extend(self.left.get_rooms())
        if self.right:
            rooms.extend(self.right.get_rooms())
        return rooms

    def get_center(self):
        if self.room:
            rx, ry, rw, rh = self.room
            return (rx + rw // 2, ry + rh // 2)
        if self.left:
            return self.left.get_center()
        if self.right:
            return self.right.get_center()
        return (self.x + self.w // 2, self.y + self.h // 2)

    def connect(self, grid):
        if self.left and self.right:
            lc = self.left.get_center()
            rc = self.right.get_center()
            _carve_corridor(grid, lc, rc)
            self.left.connect(grid)
            self.right.connect(grid)


def _carve_corridor(grid, p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    h = len(grid)
    w = len(grid[0])

    if random.random() < 0.5:
        # horizontal first
        sx, ex = min(x1, x2), max(x1, x2)
        for x in range(sx, ex + 1):
            if 0 <= y1 < h and 0 <= x < w:
                if grid[y1][x] == WALL:
                    grid[y1][x] = CORRIDOR
        sy, ey = min(y1, y2), max(y1, y2)
        for y in range(sy, ey + 1):
            if 0 <= y < h and 0 <= x2 < w:
                if grid[y][x2] == WALL:
                    grid[y][x2] = CORRIDOR
    else:
        # vertical first
        sy, ey = min(y1, y2), max(y1, y2)
        for y in range(sy, ey + 1):
            if 0 <= y < h and 0 <= x1 < w:
                if grid[y][x1] == WALL:
                    grid[y][x1] = CORRIDOR
        sx, ex = min(x1, x2), max(x1, x2)
        for x in range(sx, ex + 1):
            if 0 <= y2 < h and 0 <= x < w:
                if grid[y2][x] == WALL:
                    grid[y2][x] = CORRIDOR


def generate_dungeon(width, height):
    grid = [[WALL for _ in range(width)] for _ in range(height)]
    root = BSPNode(0, 0, width, height)
    root.split(max_depth=5)
    root.create_rooms()
    rooms = root.get_rooms()

    for rx, ry, rw, rh in rooms:
        for y in range(ry, min(ry + rh, height)):
            for x in range(rx, min(rx + rw, width)):
                grid[y][x] = FLOOR

    root.connect(grid)
    return grid, rooms


# ---------------------------------------------------------------------------
# Game entities
# ---------------------------------------------------------------------------
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 30
        self.max_hp = 30
        self.atk = 5
        self.dfn = 1
        self.level = 1
        self.xp = 0
        self.xp_next = 20
        self.gold = 0
        self.dungeon_level = 1
        self.kills = 0
        self.turns = 0

    def xp_to_level(self):
        return self.xp_next - self.xp

    def gain_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_next:
            self.level += 1
            self.xp -= self.xp_next
            self.xp_next = int(self.xp_next * 1.5)
            self.max_hp += 5
            self.hp = min(self.hp + 10, self.max_hp)
            self.atk += 1
            self.dfn += 1
            leveled = True
        return leveled


class Monster:
    def __init__(self, x, y, template_name):
        t = MONSTER_TEMPLATES[template_name]
        self.x = x
        self.y = y
        self.name = template_name
        self.ch = t["ch"]
        self.hp = t["hp"]
        self.max_hp = t["hp"]
        self.atk = t["atk"]
        self.dfn = t["dfn"]
        self.xp = t["xp"]
        self.col = t["col"]
        self.alive = True

    def scale(self, dungeon_level):
        bonus = dungeon_level - 1
        self.hp += bonus * 3
        self.max_hp = self.hp
        self.atk += bonus
        self.dfn += bonus
        self.xp += bonus * 3


class Item:
    def __init__(self, x, y, template):
        self.x = x
        self.y = y
        self.name = template["name"]
        self.ch = template["ch"]
        self.col = template["col"]
        self.effect = template["effect"]
        self.value = random.randint(*template["range"])
        self.picked = False


# ---------------------------------------------------------------------------
# Dungeon level state
# ---------------------------------------------------------------------------
class DungeonLevel:
    def __init__(self, width, height, level_num):
        self.width = width
        self.height = height
        self.level_num = level_num
        self.grid, self.rooms = generate_dungeon(width, height)
        self.monsters = []
        self.items = []
        self.stairs_pos = None
        self.revealed = [[False] * width for _ in range(height)]
        self.visible = [[False] * width for _ in range(height)]

        self._place_stairs()
        self._spawn_monsters()
        self._spawn_items()

    def _floor_tiles(self):
        tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] in (FLOOR, CORRIDOR):
                    tiles.append((x, y))
        return tiles

    def _place_stairs(self):
        if not self.rooms:
            return
        # stairs in the last room
        rx, ry, rw, rh = self.rooms[-1]
        self.stairs_pos = (rx + rw // 2, ry + rh // 2)

    def _spawn_monsters(self):
        floor_tiles = self._floor_tiles()
        random.shuffle(floor_tiles)
        count = min(len(floor_tiles) // 15, 8 + self.level_num * 3)

        eligible = [name for name, t in MONSTER_TEMPLATES.items()
                    if t["min_level"] <= self.level_num]

        # guarantee a dragon on level 5+
        has_dragon = self.level_num >= 5

        for i in range(count):
            if i >= len(floor_tiles):
                break
            x, y = floor_tiles[i]
            if has_dragon and i == 0:
                name = "Dragon"
                has_dragon = False
            else:
                weights = []
                for n in eligible:
                    t = MONSTER_TEMPLATES[n]
                    w = max(1, 10 - abs(t["min_level"] - self.level_num) * 3)
                    if n == "Dragon" and self.level_num < 4:
                        w = 0
                    weights.append(w)
                if sum(weights) == 0:
                    weights = [1] * len(eligible)
                name = random.choices(eligible, weights=weights, k=1)[0]
            m = Monster(x, y, name)
            m.scale(self.level_num)
            self.monsters.append(m)

    def _spawn_items(self):
        floor_tiles = self._floor_tiles()
        random.shuffle(floor_tiles)
        count = min(len(floor_tiles) // 10, 6 + self.level_num * 2)
        idx = 0
        for i in range(count):
            if idx >= len(floor_tiles):
                break
            x, y = floor_tiles[idx]
            idx += 1
            # avoid placing on stairs
            if self.stairs_pos and (x, y) == self.stairs_pos:
                if idx < len(floor_tiles):
                    x, y = floor_tiles[idx]
                    idx += 1
                else:
                    continue
            tmpl = random.choice(ITEM_TEMPLATES)
            self.items.append(Item(x, y, tmpl))

    def update_visibility(self, px, py, radius=7):
        # reset current visibility
        for row in self.visible:
            for i in range(len(row)):
                row[i] = False
        # cast rays
        for angle_step in range(360):
            angle = math.radians(angle_step)
            dx = math.cos(angle)
            dy = math.sin(angle)
            cx, cy = float(px), float(py)
            for _ in range(radius):
                ix, iy = int(round(cx)), int(round(cy))
                if 0 <= ix < self.width and 0 <= iy < self.height:
                    self.visible[iy][ix] = True
                    self.revealed[iy][ix] = True
                    if self.grid[iy][ix] == WALL:
                        break
                else:
                    break
                cx += dx
                cy += dy

    def monster_at(self, x, y):
        for m in self.monsters:
            if m.alive and m.x == x and m.y == y:
                return m
        return None

    def item_at(self, x, y):
        for it in self.items:
            if not it.picked and it.x == x and it.y == y:
                return it
        return None

    def is_passable(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x] != WALL
        return False


# ---------------------------------------------------------------------------
# Combat helpers
# ---------------------------------------------------------------------------
def dice(n, sides):
    return sum(random.randint(1, sides) for _ in range(n))


def attack_damage(attacker_atk, defender_dfn):
    raw = dice(1, 6) + attacker_atk
    reduction = defender_dfn // 2
    return max(1, raw - reduction)


# ---------------------------------------------------------------------------
# Main game class
# ---------------------------------------------------------------------------
class Game:
    MAP_W = 60
    MAP_H = 40
    SIDEBAR_W = 24
    MSG_LOG_H = 5
    MINIMAP_W = 16
    MINIMAP_H = 10
    VIEW_RADIUS = 7

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.player = None
        self.dungeon = None
        self.messages = []
        self.game_over = False
        self.death_cause = ""
        self.camera_x = 0
        self.camera_y = 0

    def init_colors(self):
        curses.start_color()
        curses.use_default_colors()

        curses.init_pair(C_WALL,    curses.COLOR_WHITE,   -1)
        curses.init_pair(C_FLOOR,   curses.COLOR_WHITE,   -1)
        curses.init_pair(C_PLAYER,  curses.COLOR_WHITE,   -1)
        curses.init_pair(C_RAT,     curses.COLOR_GREEN,   -1)
        curses.init_pair(C_GOBLIN,  curses.COLOR_GREEN,   -1)
        curses.init_pair(C_SKELETON,curses.COLOR_MAGENTA, -1)
        curses.init_pair(C_DRAGON,  curses.COLOR_RED,     -1)
        curses.init_pair(C_POTION,  curses.COLOR_RED,     -1)
        curses.init_pair(C_GOLD,    curses.COLOR_YELLOW,  -1)
        curses.init_pair(C_WEAPON,  curses.COLOR_CYAN,    -1)
        curses.init_pair(C_ARMOR,   curses.COLOR_BLUE,    -1)
        curses.init_pair(C_STAIRS,  curses.COLOR_YELLOW,  -1)
        curses.init_pair(C_FOG,     curses.COLOR_WHITE,   -1)
        curses.init_pair(C_MSG,     curses.COLOR_WHITE,   -1)
        curses.init_pair(C_TITLE,   curses.COLOR_RED,     -1)
        curses.init_pair(C_UI,      curses.COLOR_CYAN,    -1)
        curses.init_pair(C_MINIMAP_WALL,   curses.COLOR_WHITE,   -1)
        curses.init_pair(C_MINIMAP_ROOM,   curses.COLOR_YELLOW,  -1)
        curses.init_pair(C_MINIMAP_PLAYER, curses.COLOR_GREEN,   -1)
        curses.init_pair(C_DEAD,    curses.COLOR_RED,     -1)
        curses.init_pair(C_SUBTITLE,curses.COLOR_CYAN,    -1)

    def add_msg(self, text):
        self.messages.append(text)
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]

    def new_game(self):
        self.player = Player(0, 0)
        self.game_over = False
        self.messages = []
        self._new_dungeon_level()
        self.add_msg("You descend into the dungeon. Good luck!")

    def _new_dungeon_level(self):
        self.dungeon = DungeonLevel(self.MAP_W, self.MAP_H, self.player.dungeon_level)
        # place player in first room
        if self.dungeon.rooms:
            rx, ry, rw, rh = self.dungeon.rooms[0]
            self.player.x = rx + rw // 2
            self.player.y = ry + rh // 2
            # make sure no monster overlaps player start
            for m in self.dungeon.monsters:
                if m.x == self.player.x and m.y == self.player.y:
                    m.alive = False
        self.dungeon.update_visibility(self.player.x, self.player.y, self.VIEW_RADIUS)

    def process_input(self, key):
        if self.game_over:
            if key in (ord("r"), ord("R")):
                self.new_game()
            elif key in (ord("q"), ord("Q"), 27):
                self.running = False
            return

        dx, dy = 0, 0
        if key in (ord("w"), ord("W"), curses.KEY_UP):
            dy = -1
        elif key in (ord("s"), ord("S"), curses.KEY_DOWN):
            dy = 1
        elif key in (ord("a"), ord("A"), curses.KEY_LEFT):
            dx = -1
        elif key in (ord("d"), ord("D"), curses.KEY_RIGHT):
            dx = 1
        elif key in (ord("."), ord(" ")):
            pass  # wait a turn
        elif key in (ord("q"), ord("Q"), 27):
            self.running = False
            return
        else:
            return  # unknown key, don't advance turn

        nx, ny = self.player.x + dx, self.player.y + dy

        # check for monster at target
        target_monster = self.dungeon.monster_at(nx, ny)
        if target_monster:
            self._player_attack(target_monster)
        elif self.dungeon.is_passable(nx, ny):
            self.player.x = nx
            self.player.y = ny

            # check stairs
            if self.dungeon.stairs_pos and (nx, ny) == self.dungeon.stairs_pos:
                self.player.dungeon_level += 1
                self.add_msg(f"You descend to dungeon level {self.player.dungeon_level}!")
                self._new_dungeon_level()
                return

            # check items
            item = self.dungeon.item_at(nx, ny)
            if item:
                self._pickup_item(item)

        self.player.turns += 1
        self._move_monsters()
        self.dungeon.update_visibility(self.player.x, self.player.y, self.VIEW_RADIUS)

    def _player_attack(self, monster):
        dmg = attack_damage(self.player.atk, monster.dfn)
        monster.hp -= dmg
        self.add_msg(f"You hit {monster.name} for {dmg} damage!")
        if monster.hp <= 0:
            monster.alive = False
            self.player.kills += 1
            leveled = self.player.gain_xp(monster.xp)
            self.add_msg(f"{monster.name} defeated! +{monster.xp} XP")
            if leveled:
                self.add_msg(f"*** LEVEL UP! You are now level {self.player.level}! ***")

    def _pickup_item(self, item):
        item.picked = True
        if item.effect == "hp":
            heal = min(item.value, self.player.max_hp - self.player.hp)
            self.player.hp += heal
            self.add_msg(f"Picked up {item.name}! +{heal} HP")
        elif item.effect == "gold":
            self.player.gold += item.value
            self.add_msg(f"Picked up {item.value} gold!")
        elif item.effect == "atk":
            self.player.atk += item.value
            self.add_msg(f"Found a weapon! ATK +{item.value}")
        elif item.effect == "def":
            self.player.dfn += item.value
            self.add_msg(f"Found armor! DEF +{item.value}")

    def _move_monsters(self):
        p = self.player
        for m in self.dungeon.monsters:
            if not m.alive:
                continue
            dist = abs(m.x - p.x) + abs(m.y - p.y)
            if dist > 12:
                continue  # too far to chase

            # simple pathfinding: move toward player
            best_dx, best_dy = 0, 0
            best_dist = dist

            for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = m.x + ddx, m.y + ddy
                if not self.dungeon.is_passable(nx, ny):
                    continue
                if self.dungeon.monster_at(nx, ny):
                    continue
                if nx == p.x and ny == p.y:
                    # attack player
                    self._monster_attack(m)
                    best_dx, best_dy = 0, 0  # don't move after attacking
                    break
                new_dist = abs(nx - p.x) + abs(ny - p.y)
                if new_dist < best_dist:
                    best_dist = new_dist
                    best_dx, best_dy = ddx, ddy
            else:
                if best_dx != 0 or best_dy != 0:
                    m.x += best_dx
                    m.y += best_dy

    def _monster_attack(self, monster):
        dmg = attack_damage(monster.atk, self.player.dfn)
        self.player.hp -= dmg
        self.add_msg(f"{monster.name} hits you for {dmg} damage!")
        if self.player.hp <= 0:
            self.player.hp = 0
            self.game_over = True
            self.death_cause = f"Killed by a {monster.name}"
            self.add_msg("*** YOU HAVE DIED ***")

    # -----------------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------------
    def draw(self):
        self.stdscr.erase()
        max_y, max_x = self.stdscr.getmaxyx()

        if self.game_over:
            self._draw_death_screen(max_y, max_x)
            self.stdscr.refresh()
            return

        # viewport dimensions
        view_w = max(10, max_x - self.SIDEBAR_W - 1)
        view_h = max(5, max_y - self.MSG_LOG_H - 1)

        # camera centered on player
        self.camera_x = self.player.x - view_w // 2
        self.camera_y = self.player.y - view_h // 2
        self.camera_x = max(0, min(self.camera_x, self.MAP_W - view_w))
        self.camera_y = max(0, min(self.camera_y, self.MAP_H - view_h))

        self._draw_map(view_w, view_h)
        self._draw_sidebar(view_w, max_y)
        self._draw_messages(view_h, view_w, max_y)
        self._draw_minimap(view_w, view_h)

        self.stdscr.refresh()

    def _draw_map(self, view_w, view_h):
        d = self.dungeon
        p = self.player

        for vy in range(view_h):
            wy = vy + self.camera_y
            for vx in range(view_w):
                wx = vx + self.camera_x
                if wx < 0 or wx >= d.width or wy < 0 or wy >= d.height:
                    continue

                if d.visible[wy][wx]:
                    # fully visible
                    if wx == p.x and wy == p.y:
                        self._put(vy, vx, "@", C_PLAYER, bold=True)
                    elif d.monster_at(wx, wy):
                        m = d.monster_at(wx, wy)
                        self._put(vy, vx, m.ch, m.col, bold=True)
                    elif d.item_at(wx, wy):
                        it = d.item_at(wx, wy)
                        self._put(vy, vx, it.ch, it.col, bold=True)
                    elif d.stairs_pos and (wx, wy) == d.stairs_pos:
                        self._put(vy, vx, ">", C_STAIRS, bold=True)
                    elif d.grid[wy][wx] == WALL:
                        self._put(vy, vx, "#", C_WALL, dim=True)
                    elif d.grid[wy][wx] in (FLOOR, CORRIDOR):
                        self._put(vy, vx, "\u00b7", C_FLOOR, dim=True)
                elif d.revealed[wy][wx]:
                    # previously seen - dim
                    if d.grid[wy][wx] == WALL:
                        self._put(vy, vx, "#", C_FOG, dim=True)
                    elif d.grid[wy][wx] in (FLOOR, CORRIDOR):
                        self._put(vy, vx, "\u00b7", C_FOG, dim=True)
                    elif d.stairs_pos and (wx, wy) == d.stairs_pos:
                        self._put(vy, vx, ">", C_FOG, dim=True)

    def _draw_sidebar(self, offset_x, max_y):
        sx = offset_x + 1
        p = self.player
        d = self.dungeon

        lines = [
            ("DUNGEON CRAWLER", C_TITLE, True),
            ("", 0, False),
            (f"  Dungeon: B{p.dungeon_level}", C_UI, False),
            ("", 0, False),
            (f"  HP:  {p.hp}/{p.max_hp}", C_POTION, False),
            (f"  ATK: {p.atk}", C_WEAPON, False),
            (f"  DEF: {p.dfn}", C_ARMOR, False),
            ("", 0, False),
            (f"  Lv:  {p.level}", C_UI, False),
            (f"  XP:  {p.xp}/{p.xp_next}", C_UI, False),
            (f"  Gold: {p.gold}", C_GOLD, False),
            ("", 0, False),
            (f"  Kills: {p.kills}", C_MSG, False),
            (f"  Turns: {p.turns}", C_MSG, False),
            ("", 0, False),
            ("  [WASD] Move", C_FOG, False),
            ("  [.] Wait", C_FOG, False),
            ("  [Q] Quit", C_FOG, False),
        ]

        # draw HP bar
        hp_bar_row = -1
        for i, (text, col, bold) in enumerate(lines):
            if i >= max_y:
                break
            if text:
                attr = curses.color_pair(col)
                if bold:
                    attr |= curses.A_BOLD
                try:
                    self.stdscr.addstr(i, sx, text, attr)
                except curses.error:
                    pass
            if "HP:" in text:
                hp_bar_row = i

        # draw HP bar graphic
        if hp_bar_row >= 0 and hp_bar_row + 1 < max_y:
            bar_w = 16
            filled = int(bar_w * p.hp / max(1, p.max_hp))
            bar = "[" + "#" * filled + "-" * (bar_w - filled) + "]"
            col = C_POTION if p.hp > p.max_hp * 0.3 else C_DRAGON
            try:
                self.stdscr.addstr(hp_bar_row + 1, sx + 2, bar, curses.color_pair(col))
            except curses.error:
                pass

    def _draw_messages(self, start_y, view_w, max_y):
        y = start_y + 1
        if y >= max_y:
            return
        # separator line
        sep = "-" * min(view_w, 60)
        try:
            self.stdscr.addstr(y, 0, sep, curses.color_pair(C_FOG) | curses.A_DIM)
        except curses.error:
            pass

        visible_msgs = self.messages[-(self.MSG_LOG_H):]
        for i, msg in enumerate(visible_msgs):
            row = y + 1 + i
            if row >= max_y:
                break
            try:
                self.stdscr.addstr(row, 1, msg[:view_w - 2], curses.color_pair(C_MSG))
            except curses.error:
                pass

    def _draw_minimap(self, view_w, view_h):
        # draw in top-right of the map viewport
        mm_x = max(0, view_w - self.MINIMAP_W - 1)
        mm_y = 0
        d = self.dungeon
        p = self.player

        scale_x = d.width / self.MINIMAP_W
        scale_y = d.height / self.MINIMAP_H

        for my in range(self.MINIMAP_H):
            for mx in range(self.MINIMAP_W):
                wx = int(mx * scale_x)
                wy = int(my * scale_y)
                if wx >= d.width or wy >= d.height:
                    continue
                # player position on minimap
                pmx = int(p.x / scale_x)
                pmy = int(p.y / scale_y)
                if mx == pmx and my == pmy:
                    self._put(mm_y + my, mm_x + mx, "@", C_MINIMAP_PLAYER, bold=True)
                elif d.revealed[wy][wx]:
                    if d.grid[wy][wx] == WALL:
                        self._put(mm_y + my, mm_x + mx, "#", C_MINIMAP_WALL, dim=True)
                    else:
                        self._put(mm_y + my, mm_x + mx, ".", C_MINIMAP_ROOM, dim=True)

    def _draw_death_screen(self, max_y, max_x):
        p = self.player
        lines = [
            "",
            "   ____    _    __  __ _____    _____     _______ ____  ",
            "  / ___|  / \\  |  \\/  | ____|  / _ \\ \\   / / ____|  _ \\ ",
            " | |  _  / _ \\ | |\\/| |  _|   | | | \\ \\ / /|  _| | |_) |",
            " | |_| |/ ___ \\| |  | | |___  | |_| |\\ V / | |___|  _ < ",
            "  \\____/_/   \\_\\_|  |_|_____|  \\___/  \\_/  |_____|_| \\_\\",
            "",
            f"  {self.death_cause}",
            "",
            f"  Dungeon Level: B{p.dungeon_level}",
            f"  Character Level: {p.level}",
            f"  Kills: {p.kills}",
            f"  Gold: {p.gold}",
            f"  Turns Survived: {p.turns}",
            "",
            "  Press [R] to restart or [Q] to quit",
        ]

        start_y = max(0, (max_y - len(lines)) // 2)
        for i, line in enumerate(lines):
            row = start_y + i
            if row >= max_y:
                break
            col = C_DEAD if i < 7 else C_UI
            if "Press" in line:
                col = C_SUBTITLE
            attr = curses.color_pair(col)
            if i < 7:
                attr |= curses.A_BOLD
            try:
                cx = max(0, (max_x - len(line)) // 2)
                self.stdscr.addstr(row, cx, line, attr)
            except curses.error:
                pass

    def _put(self, y, x, ch, color_pair, bold=False, dim=False):
        try:
            attr = curses.color_pair(color_pair)
            if bold:
                attr |= curses.A_BOLD
            if dim:
                attr |= curses.A_DIM
            self.stdscr.addch(y, x, ch, attr)
        except curses.error:
            pass

    # -----------------------------------------------------------------------
    # Welcome screen
    # -----------------------------------------------------------------------
    def show_welcome(self):
        self.stdscr.erase()
        max_y, max_x = self.stdscr.getmaxyx()

        title = [
            " ____  _   _ _   _  ____ _____ ___  _   _ ",
            "|  _ \\| | | | \\ | |/ ___| ____/ _ \\| \\ | |",
            "| | | | | | |  \\| | |  _|  _|| | | |  \\| |",
            "| |_| | |_| | |\\  | |_| | |__| |_| | |\\  |",
            "|____/ \\___/|_| \\_|\\____|_____\\___/|_| \\_|",
            "",
            "        C  R  A  W  L  E  R",
        ]

        controls = [
            "",
            "   CONTROLS",
            "   ---------",
            "   WASD / Arrow Keys  -  Move",
            "   . or Space         -  Wait a turn",
            "   Q / Esc            -  Quit",
            "",
            "   LEGEND",
            "   ---------",
            "   @  Player     >  Stairs down",
            "   r  Rat        g  Goblin",
            "   S  Skeleton   D  Dragon",
            "   h  Potion     $  Gold",
            "   w  Weapon     a  Armor",
            "",
            "   Bump into monsters to attack!",
            "   Find the stairs > to go deeper.",
            "",
            "       Press any key to begin...",
        ]

        all_lines = title + controls
        start_y = max(0, (max_y - len(all_lines)) // 2)

        for i, line in enumerate(all_lines):
            row = start_y + i
            if row >= max_y:
                break
            cx = max(0, (max_x - len(line)) // 2)
            if i < len(title):
                if i < 5:
                    attr = curses.color_pair(C_TITLE) | curses.A_BOLD
                else:
                    attr = curses.color_pair(C_SUBTITLE) | curses.A_BOLD
            elif "Press" in line:
                attr = curses.color_pair(C_GOLD) | curses.A_BOLD
            elif "CONTROLS" in line or "LEGEND" in line:
                attr = curses.color_pair(C_UI) | curses.A_BOLD
            elif "---" in line:
                attr = curses.color_pair(C_FOG) | curses.A_DIM
            else:
                attr = curses.color_pair(C_MSG)
            try:
                self.stdscr.addstr(row, cx, line, attr)
            except curses.error:
                pass

        self.stdscr.refresh()
        self.stdscr.nodelay(False)
        self.stdscr.getch()

    # -----------------------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------------------
    def run(self):
        curses.curs_set(0)
        self.init_colors()
        self.stdscr.nodelay(False)
        self.stdscr.keypad(True)

        self.show_welcome()
        self.new_game()

        while self.running:
            self.draw()
            key = self.stdscr.getch()
            if key == curses.KEY_RESIZE:
                continue
            self.process_input(key)


def main(stdscr):
    game = Game(stdscr)
    game.run()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
