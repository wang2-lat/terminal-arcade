#!/usr/bin/env python3
"""🔤 Terminal Wordle - Guess the 5-letter word!"""
import curses
import random
import time
import json
import os

# Common 5-letter words
WORDS = [
    "about","above","abuse","actor","acute","admit","adopt","adult","after","again",
    "agent","agree","ahead","alarm","album","alert","alien","align","alive","allow",
    "alone","along","alter","among","angel","anger","angle","angry","anime","ankle",
    "apart","apple","apply","arena","argue","arise","aside","asset","audio","avoid",
    "award","aware","awful","basic","beach","begin","being","below","bench","birth",
    "black","blade","blame","blank","blast","blaze","bleed","blend","bless","blind",
    "block","blood","bloom","blown","board","bonus","boost","bound","brain","brand",
    "brave","bread","break","breed","brick","bride","brief","bring","broad","broke",
    "brown","brush","buddy","build","built","burst","buyer","cabin","candy","cargo",
    "carry","catch","cause","chain","chair","chaos","charm","chart","chase","cheap",
    "check","chest","chief","child","china","chunk","civic","claim","clash","class",
    "clean","clear","climb","cling","clock","clone","close","cloud","coach","coast",
    "color","comet","count","court","cover","crack","craft","crane","crash","crazy",
    "cream","crime","crisp","cross","crowd","crown","crude","crush","curve","cycle",
    "daily","dance","death","debug","delay","dense","depth","derby","devil","diary",
    "dirty","disco","dodge","doubt","dough","draft","drain","drama","drank","drawn",
    "dream","dress","dried","drift","drill","drink","drive","drone","drown","dying",
    "eager","early","earth","eight","elect","elite","email","empty","enemy","enjoy",
    "enter","equal","error","essay","event","every","exact","exile","exist","extra",
    "faint","faith","false","fault","feast","fiber","field","fifth","fifty","fight",
    "final","first","fixed","flame","flash","flesh","float","flood","floor","flour",
    "fluid","flush","focus","force","forge","forth","forum","found","frame","frank",
    "fraud","fresh","front","frost","fruit","fully","funny","ghost","giant","given",
    "glass","globe","gloom","glory","glove","going","grace","grade","grain","grand",
    "grant","graph","grasp","grass","grave","great","green","greet","grief","grill",
    "grind","grip","gross","group","grove","grown","guard","guess","guest","guide",
    "guilt","given","happy","harsh","heart","heavy","hence","honey","honor","horse",
    "hotel","house","human","humor","hurry","ideal","image","imply","index","indie",
    "inner","input","irony","issue","ivory","jewel","joint","judge","juice","knife",
    "knock","known","label","labor","large","laser","later","laugh","layer","learn",
    "least","leave","legal","level","light","limit","linen","lived","local","logic",
    "login","loose","lover","lower","lucky","lunch","magic","major","maker","manor",
    "march","match","maybe","mayor","media","mercy","metal","meter","might","minor",
    "minus","model","money","month","moral","mount","mouse","mouth","movie","music",
    "naive","naked","nerve","never","noble","noise","north","noted","novel","nurse",
    "ocean","offer","often","olive","opera","orbit","order","organ","other","ought",
    "outer","owned","owner","oxide","ozone","paint","panel","panic","paper","party",
    "pasta","patch","pause","peace","pearl","penny","phase","phone","photo","piano",
    "piece","pilot","pitch","pixel","pizza","place","plain","plane","plant","plate",
    "plaza","plead","plumb","plus","point","polar","pound","power","press","price",
    "pride","prime","prince","print","prior","prize","probe","proof","proud","prove",
    "psalm","pulse","punch","pupil","queen","query","quest","quick","quiet","quite",
    "quota","quote","radar","radio","raise","rally","ranch","range","rapid","ratio",
    "reach","react","ready","realm","rebel","refer","reign","relax","reply","rider",
    "rifle","right","rigid","rival","river","robin","robot","rocky","roman","rough",
    "round","route","royal","rugby","ruler","rural","saint","salad","sauce","scale",
    "scene","scope","score","sense","serve","setup","seven","shade","shake","shall",
    "shame","shape","share","sharp","shelf","shell","shift","shine","shirt","shock",
    "shoot","shore","short","shout","sight","sigma","since","sixth","sixty","skill",
    "skull","slave","sleep","slice","slide","slope","small","smart","smell","smile",
    "smoke","snake","solar","solid","solve","sorry","south","space","spare","speak",
    "speed","spend","spine","spite","split","spoke","sport","spray","squad","stack",
    "staff","stage","stain","stake","stale","stall","stamp","stand","stark","start",
    "state","stays","steal","steam","steel","steep","steer","stern","stick","still",
    "stock","stone","stood","store","storm","story","stove","strip","stuck","stuff",
    "style","sugar","suite","super","surge","swamp","swear","sweep","sweet","swift",
    "swing","sword","syrup","table","taste","teach","tears","tempo","tends","terms",
    "theme","thick","thing","think","third","those","three","threw","throw","thumb",
    "tiger","tight","timer","tired","title","today","token","total","touch","tough",
    "towel","tower","toxic","trace","track","trade","trail","train","trait","trash",
    "treat","trend","trial","tribe","trick","tried","troop","truck","truly","trump",
    "trunk","trust","truth","tumor","twice","twist","ultra","uncle","under","union",
    "unite","unity","until","upper","upset","urban","usage","usual","valid","value",
    "valve","vault","venue","verse","video","vigor","vinyl","viral","virus","visit",
    "vital","vivid","vocal","voice","voter","wagon","waste","watch","water","weave",
    "weird","whale","wheat","wheel","where","which","while","white","whole","whose",
    "width","wings","witch","woman","world","worry","worse","worst","worth","would",
    "wound","wrath","write","wrong","wrote","yacht","yield","young","youth","zones",
]

SCORE_FILE = os.path.expanduser("~/.wordle_stats.json")

# States
CORRECT = 2    # Green
PRESENT = 3    # Yellow
ABSENT = 8     # Gray


def load_stats():
    try:
        with open(SCORE_FILE) as f:
            return json.load(f)
    except:
        return {"played": 0, "won": 0, "streak": 0, "max_streak": 0, "distribution": {str(i): 0 for i in range(1, 7)}}


def save_stats(stats):
    with open(SCORE_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def check_guess(guess, answer):
    """Return list of (char, state) for each position."""
    result = [ABSENT] * 5
    answer_chars = list(answer)

    # First pass: correct positions
    for i in range(5):
        if guess[i] == answer[i]:
            result[i] = CORRECT
            answer_chars[i] = None

    # Second pass: present but wrong position
    for i in range(5):
        if result[i] == CORRECT:
            continue
        if guess[i] in answer_chars:
            result[i] = PRESENT
            answer_chars[answer_chars.index(guess[i])] = None

    return result


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


def draw_tile(stdscr, y, x, char, state):
    """Draw a single letter tile."""
    if state == CORRECT:
        color = curses.color_pair(2) | curses.A_BOLD  # Green
    elif state == PRESENT:
        color = curses.color_pair(3) | curses.A_BOLD  # Yellow
    elif state == ABSENT:
        color = curses.color_pair(8)  # Gray
    else:
        color = curses.color_pair(7)  # White (empty/current)

    try:
        stdscr.addstr(y, x, "┌───┐", color)
        stdscr.addstr(y + 1, x, f"│ {char.upper()} │", color)
        stdscr.addstr(y + 2, x, "└───┘", color)
    except curses.error:
        pass


def draw_keyboard(stdscr, y, x, key_states):
    """Draw the on-screen keyboard with color hints."""
    rows = [
        list("qwertyuiop"),
        list("asdfghjkl"),
        list("zxcvbnm"),
    ]

    for ri, row in enumerate(rows):
        rx = x + ri * 2  # Offset each row
        for ci, ch in enumerate(row):
            kx = rx + ci * 4
            state = key_states.get(ch, 0)
            if state == CORRECT:
                color = curses.color_pair(2) | curses.A_BOLD
            elif state == PRESENT:
                color = curses.color_pair(3) | curses.A_BOLD
            elif state == ABSENT:
                color = curses.color_pair(8)
            else:
                color = curses.color_pair(7)

            try:
                stdscr.addstr(y + ri, kx, f"[{ch.upper()}]", color)
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
    stats = load_stats()

    while True:
        h, w = stdscr.getmaxyx()
        answer = random.choice(WORDS)
        guesses = []  # List of (word, results)
        current = ""
        message = ""
        game_over = False
        won = False
        key_states = {}  # letter -> best state

        while True:
            stdscr.clear()

            # Title
            draw_centered(stdscr, 0, "╔══════════════════════╗", curses.color_pair(3))
            draw_centered(stdscr, 1, "║   🔤 WORDLE 🔤       ║", curses.color_pair(3) | curses.A_BOLD)
            draw_centered(stdscr, 2, "╚══════════════════════╝", curses.color_pair(3))

            # Grid
            grid_x = max(0, (w - 29) // 2)
            grid_y = 4

            for row in range(6):
                y = grid_y + row * 3
                if row < len(guesses):
                    word, results = guesses[row]
                    for col in range(5):
                        draw_tile(stdscr, y, grid_x + col * 6, word[col], results[col])
                elif row == len(guesses) and not game_over:
                    # Current input
                    for col in range(5):
                        ch = current[col] if col < len(current) else " "
                        draw_tile(stdscr, y, grid_x + col * 6, ch, 0)
                else:
                    for col in range(5):
                        draw_tile(stdscr, y, grid_x + col * 6, " ", 0)

            # Message
            if message:
                msg_y = grid_y + 19
                color = curses.color_pair(2) if won else curses.color_pair(1) if game_over else curses.color_pair(4)
                draw_centered(stdscr, msg_y, message, color | curses.A_BOLD)

            # Keyboard
            kb_y = grid_y + 21
            kb_x = max(0, (w - 44) // 2)
            draw_keyboard(stdscr, kb_y, kb_x, key_states)

            # Stats
            try:
                stat_str = f"Played: {stats['played']} | Won: {stats['won']} | Streak: {stats['streak']}"
                draw_centered(stdscr, kb_y + 4, stat_str, curses.color_pair(8))
            except curses.error:
                pass

            if game_over:
                draw_centered(stdscr, h - 2, "ENTER: New game  Q: Quit", curses.color_pair(8))
            else:
                draw_centered(stdscr, h - 2, "Type a 5-letter word, ENTER to submit, BACKSPACE to delete", curses.color_pair(8))

            stdscr.refresh()

            key = stdscr.getch()

            if key in (ord('q'), ord('Q')) and game_over:
                save_stats(stats)
                return

            if game_over:
                if key in (curses.KEY_ENTER, 10, 13):
                    break  # New game
                continue

            if key in (curses.KEY_BACKSPACE, 127, 8):
                current = current[:-1]
                message = ""
            elif key in (curses.KEY_ENTER, 10, 13):
                if len(current) != 5:
                    message = "Need 5 letters!"
                elif current.lower() not in WORDS:
                    message = "Not in word list!"
                else:
                    word = current.lower()
                    results = check_guess(word, answer)
                    guesses.append((word, results))

                    # Update keyboard states
                    for i, ch in enumerate(word):
                        current_state = key_states.get(ch, 0)
                        if results[i] == CORRECT:
                            key_states[ch] = CORRECT
                        elif results[i] == PRESENT and current_state != CORRECT:
                            key_states[ch] = PRESENT
                        elif current_state == 0:
                            key_states[ch] = ABSENT

                    current = ""

                    if word == answer:
                        won = True
                        game_over = True
                        message = f"🎉 Brilliant! Got it in {len(guesses)}! 🎉"
                        stats["played"] += 1
                        stats["won"] += 1
                        stats["streak"] += 1
                        stats["max_streak"] = max(stats["max_streak"], stats["streak"])
                        stats["distribution"][str(len(guesses))] = stats["distribution"].get(str(len(guesses)), 0) + 1
                    elif len(guesses) >= 6:
                        game_over = True
                        message = f"The word was: {answer.upper()}"
                        stats["played"] += 1
                        stats["streak"] = 0
            elif 97 <= key <= 122 or 65 <= key <= 90:  # a-z or A-Z
                if len(current) < 5:
                    current += chr(key).lower()
                    message = ""

        save_stats(stats)


if __name__ == "__main__":
    curses.wrapper(main)
