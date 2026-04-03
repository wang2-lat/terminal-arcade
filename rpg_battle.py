#!/usr/bin/env python3
"""🎲 Terminal RPG Battle - Dice-rolling turn-based combat!"""
import curses
import random
import time
import math

MONSTERS = [
    {"name": "Goblin", "hp": 30, "atk": 4, "def": 2, "spd": 6, "xp": 20,
     "art": ["  ╭─╮  ", " (°_°) ", "  /|\\  ", "  / \\  "], "color": 2},
    {"name": "Skeleton", "hp": 40, "atk": 6, "def": 3, "spd": 4, "xp": 35,
     "art": ["  ╔═╗  ", "  ☠️   ", " ╔╩═╗  ", " ║ ║║  "], "color": 7},
    {"name": "Orc", "hp": 60, "atk": 8, "def": 5, "spd": 3, "xp": 50,
     "art": [" ╔═══╗ ", " ║>.<║ ", " ╠═══╣ ", " ╚╦═╦╝ "], "color": 2},
    {"name": "Dark Mage", "hp": 35, "atk": 12, "def": 2, "spd": 7, "xp": 60,
     "art": ["  /\\   ", " /  \\  ", "│(◉◉)│", " \\  /  "], "color": 5},
    {"name": "Dragon", "hp": 100, "atk": 15, "def": 8, "spd": 5, "xp": 100,
     "art": ["  /\\_/\\ ", " / 0 0 \\", "( =▼= )", " >===< "], "color": 1},
]

SKILLS = [
    {"name": "Attack", "type": "damage", "dice": "2d6", "cost": 0, "desc": "Basic sword attack"},
    {"name": "Power Strike", "type": "damage", "dice": "3d6+2", "cost": 3, "desc": "Heavy blow"},
    {"name": "Heal", "type": "heal", "dice": "2d6+3", "cost": 4, "desc": "Restore HP"},
    {"name": "Fireball", "type": "damage", "dice": "4d6", "cost": 6, "desc": "Magical fire"},
    {"name": "Shield", "type": "buff_def", "dice": "1d4+2", "cost": 3, "desc": "+DEF for 3 turns"},
    {"name": "Rage", "type": "buff_atk", "dice": "1d4+2", "cost": 3, "desc": "+ATK for 3 turns"},
]

ITEMS = [
    {"name": "Health Potion", "type": "heal", "value": 25, "count": 3},
    {"name": "Mana Potion", "type": "mana", "value": 10, "count": 2},
    {"name": "Bomb", "type": "damage", "value": 20, "count": 1},
]


def roll_dice(dice_str):
    """Parse and roll dice notation like '2d6+3'."""
    parts = dice_str.replace('+', ' +').replace('-', ' -').split()
    total = 0
    rolls = []
    for part in parts:
        if 'd' in part:
            num, sides = part.split('d')
            num = int(num) if num else 1
            sides = int(sides)
            for _ in range(num):
                r = random.randint(1, sides)
                rolls.append(r)
                total += r
        else:
            total += int(part)
    return total, rolls


def draw_dice_animation(stdscr, y, x, final_rolls, color=3):
    """Animate dice rolling."""
    h, w = stdscr.getmaxyx()
    for frame in range(8):
        for i, _ in enumerate(final_rolls):
            dx = x + i * 5
            if dx + 4 < w and y + 2 < h:
                val = random.randint(1, 6) if frame < 6 else final_rolls[i]
                try:
                    stdscr.addstr(y, dx, "┌───┐", curses.color_pair(color))
                    stdscr.addstr(y + 1, dx, f"│ {val} │", curses.color_pair(color) | curses.A_BOLD)
                    stdscr.addstr(y + 2, dx, "└───┘", curses.color_pair(color))
                except curses.error:
                    pass
        stdscr.refresh()
        time.sleep(0.08)


def draw_hp_bar(stdscr, y, x, current, maximum, width, color, label=""):
    ratio = max(0, current / maximum)
    filled = int(width * ratio)
    bar_color = 2 if ratio > 0.5 else 3 if ratio > 0.25 else 1
    try:
        if label:
            stdscr.addstr(y, x, label, curses.color_pair(color))
        bar_x = x + len(label)
        stdscr.addstr(y, bar_x, "█" * filled, curses.color_pair(bar_color) | curses.A_BOLD)
        stdscr.addstr(y, bar_x + filled, "░" * (width - filled), curses.color_pair(8))
        stdscr.addstr(y, bar_x + width + 1, f"{current}/{maximum}", curses.color_pair(color))
    except curses.error:
        pass


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


class Player:
    def __init__(self):
        self.name = "Hero"
        self.hp = 80
        self.max_hp = 80
        self.mp = 15
        self.max_mp = 15
        self.atk = 6
        self.defense = 4
        self.spd = 5
        self.level = 1
        self.xp = 0
        self.xp_next = 50
        self.gold = 0
        self.buffs = {}  # {stat: (amount, turns)}
        self.items = [dict(i) for i in ITEMS]

    def get_stat(self, stat):
        base = getattr(self, stat)
        if stat in self.buffs:
            base += self.buffs[stat][0]
        return base

    def apply_buff(self, stat, amount, turns):
        self.buffs[stat] = (amount, turns)

    def tick_buffs(self):
        expired = []
        for stat in self.buffs:
            amount, turns = self.buffs[stat]
            if turns <= 1:
                expired.append(stat)
            else:
                self.buffs[stat] = (amount, turns - 1)
        for stat in expired:
            del self.buffs[stat]

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level += 1
            self.max_hp += 10
            self.hp = self.max_hp
            self.max_mp += 3
            self.mp = self.max_mp
            self.atk += 2
            self.defense += 1
            self.xp_next = int(self.xp_next * 1.5)
            return True
        return False


def battle(stdscr, player, monster_data):
    h, w = stdscr.getmaxyx()
    monster_hp = monster_data["hp"]
    monster_max_hp = monster_data["hp"]
    turn = 0
    log = []

    def add_log(msg):
        log.append(msg)
        if len(log) > 6:
            log.pop(0)

    while player.hp > 0 and monster_hp > 0:
        turn += 1
        stdscr.clear()

        # Draw monster
        monster_y = 3
        draw_centered(stdscr, 1, f"═══ {monster_data['name']} ═══",
                     curses.color_pair(monster_data['color']) | curses.A_BOLD)
        for i, line in enumerate(monster_data["art"]):
            draw_centered(stdscr, monster_y + i, line,
                         curses.color_pair(monster_data['color']))
        draw_hp_bar(stdscr, monster_y + len(monster_data["art"]) + 1,
                   (w - 30) // 2, monster_hp, monster_max_hp, 20, monster_data['color'], "HP: ")

        # Draw player
        player_y = h // 2 + 1
        draw_hp_bar(stdscr, player_y, 4, player.hp, player.max_hp, 20, 2, "HP: ")
        draw_hp_bar(stdscr, player_y + 1, 4, player.mp, player.max_mp, 20, 6, "MP: ")
        try:
            stdscr.addstr(player_y + 2, 4,
                         f"ATK:{player.get_stat('atk')} DEF:{player.get_stat('defense')} LV:{player.level}",
                         curses.color_pair(4))
            if player.buffs:
                buff_str = " Buffs: " + ", ".join(f"+{v[0]}{k[:3]}({v[1]}t)" for k, v in player.buffs.items())
                stdscr.addstr(player_y + 3, 4, buff_str, curses.color_pair(5))
        except curses.error:
            pass

        # Battle log
        log_y = player_y + 5
        for i, msg in enumerate(log):
            try:
                stdscr.addstr(log_y + i, 4, msg[:w-8], curses.color_pair(8))
            except curses.error:
                pass

        # Menu
        menu_y = h - 8
        try:
            stdscr.addstr(menu_y, 4, "─" * (w - 8), curses.color_pair(3))
        except curses.error:
            pass

        # Show skills
        for i, skill in enumerate(SKILLS):
            can_use = player.mp >= skill["cost"]
            color = curses.color_pair(2 if can_use else 8)
            try:
                stdscr.addstr(menu_y + 1 + i // 3, 4 + (i % 3) * 25,
                             f"{i+1}:{skill['name']}({skill['cost']}MP)", color)
            except curses.error:
                pass

        # Items
        try:
            item_str = "  Items: "
            for i, item in enumerate(player.items):
                if item["count"] > 0:
                    item_str += f"[{chr(65+i)}]{item['name']}x{item['count']} "
            stdscr.addstr(menu_y + 3, 4, item_str, curses.color_pair(3))
            stdscr.addstr(menu_y + 4, 4, "  R:Run  Q:Quit", curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()

        # Player input
        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            return "quit"
        elif key in (ord('r'), ord('R')):
            if random.random() < 0.5:
                add_log("Escaped successfully!")
                stdscr.refresh()
                time.sleep(1)
                return "run"
            else:
                add_log("Failed to escape!")

        # Skills
        skill = None
        if ord('1') <= key <= ord('6'):
            idx = key - ord('1')
            if idx < len(SKILLS):
                skill = SKILLS[idx]
                if player.mp < skill["cost"]:
                    add_log("Not enough MP!")
                    skill = None

        # Items
        if ord('a') <= key <= ord('c'):
            idx = key - ord('a')
            if idx < len(player.items) and player.items[idx]["count"] > 0:
                item = player.items[idx]
                item["count"] -= 1
                if item["type"] == "heal":
                    healed = min(item["value"], player.max_hp - player.hp)
                    player.hp += healed
                    add_log(f"Used {item['name']}! Healed {healed} HP")
                elif item["type"] == "mana":
                    restored = min(item["value"], player.max_mp - player.mp)
                    player.mp += restored
                    add_log(f"Used {item['name']}! Restored {restored} MP")
                elif item["type"] == "damage":
                    monster_hp -= item["value"]
                    add_log(f"Used {item['name']}! Dealt {item['value']} damage!")
                continue

        if skill:
            player.mp -= skill["cost"]
            total, rolls = roll_dice(skill["dice"])

            # Dice animation
            dice_y = h // 2 - 2
            draw_dice_animation(stdscr, dice_y, (w - len(rolls) * 5) // 2, rolls)

            if skill["type"] == "damage":
                damage = max(1, total + player.get_stat('atk') - monster_data["def"])
                monster_hp -= damage
                add_log(f"{skill['name']}! Rolled {rolls}={total} → {damage} damage!")
            elif skill["type"] == "heal":
                healed = min(total, player.max_hp - player.hp)
                player.hp += healed
                add_log(f"Heal! Rolled {rolls}={total} → +{healed} HP!")
            elif skill["type"] == "buff_def":
                player.apply_buff("defense", total, 3)
                add_log(f"Shield! +{total} DEF for 3 turns!")
            elif skill["type"] == "buff_atk":
                player.apply_buff("atk", total, 3)
                add_log(f"Rage! +{total} ATK for 3 turns!")

            time.sleep(0.3)

        # Monster turn
        if monster_hp > 0:
            m_total, m_rolls = roll_dice("1d6")
            m_damage = max(1, m_total + monster_data["atk"] - player.get_stat('defense'))
            player.hp -= m_damage
            add_log(f"{monster_data['name']} attacks! {m_damage} damage!")
            player.tick_buffs()

    if player.hp <= 0:
        return "defeat"
    else:
        return "victory"


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

    # Welcome
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    title = [
        "╔══════════════════════════════╗",
        "║     🎲 DICE QUEST RPG 🎲     ║",
        "╠══════════════════════════════╣",
        "║                              ║",
        "║  Battle monsters!            ║",
        "║  Roll dice for attacks!      ║",
        "║  Level up and grow stronger! ║",
        "║                              ║",
        "║  Press ENTER to begin...     ║",
        "╚══════════════════════════════╝",
    ]
    for i, line in enumerate(title):
        color = curses.color_pair(3) if i in (0, 2, 9) else curses.color_pair(4)
        draw_centered(stdscr, h // 2 - 5 + i, line, color)
    stdscr.refresh()
    stdscr.getch()

    player = Player()
    battles_won = 0

    while player.hp > 0:
        # Pick monster (harder as you progress)
        max_idx = min(len(MONSTERS) - 1, battles_won // 2)
        monster_data = dict(random.choice(MONSTERS[:max_idx + 1]))
        # Scale monster
        monster_data["hp"] = int(monster_data["hp"] * (1 + battles_won * 0.15))
        monster_data["atk"] = int(monster_data["atk"] * (1 + battles_won * 0.1))

        result = battle(stdscr, player, monster_data)

        if result == "quit":
            break
        elif result == "victory":
            battles_won += 1
            gold = random.randint(10, 30) + battles_won * 5
            player.gold += gold
            leveled = player.gain_xp(monster_data["xp"])

            stdscr.clear()
            draw_centered(stdscr, h // 2 - 3, "⚔️  VICTORY!  ⚔️", curses.color_pair(2) | curses.A_BOLD)
            draw_centered(stdscr, h // 2 - 1, f"+{monster_data['xp']} XP  +{gold} Gold", curses.color_pair(3))
            if leveled:
                draw_centered(stdscr, h // 2 + 1, f"🎉 LEVEL UP! Now Level {player.level}! 🎉",
                             curses.color_pair(4) | curses.A_BOLD)
            draw_centered(stdscr, h // 2 + 3, f"Battles Won: {battles_won} | Gold: {player.gold}",
                         curses.color_pair(5))
            draw_centered(stdscr, h // 2 + 5, "Press ENTER to continue...", curses.color_pair(8))
            stdscr.refresh()
            stdscr.getch()

            # Heal between battles
            player.hp = min(player.max_hp, player.hp + player.max_hp // 4)
            player.mp = min(player.max_mp, player.mp + 3)
            # Restock items occasionally
            if battles_won % 3 == 0:
                for item in player.items:
                    item["count"] = min(item["count"] + 1, 5)
        elif result == "defeat":
            stdscr.clear()
            draw_centered(stdscr, h // 2 - 2, "💀 DEFEATED 💀", curses.color_pair(1) | curses.A_BOLD)
            draw_centered(stdscr, h // 2, f"You survived {battles_won} battles!", curses.color_pair(3))
            draw_centered(stdscr, h // 2 + 1, f"Level {player.level} | Gold: {player.gold}", curses.color_pair(4))
            draw_centered(stdscr, h // 2 + 3, "Press any key...", curses.color_pair(8))
            stdscr.refresh()
            stdscr.getch()
            break
        elif result == "run":
            continue


if __name__ == "__main__":
    curses.wrapper(main)
