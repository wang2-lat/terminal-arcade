#!/usr/bin/env python3
"""⚡ Terminal Typing Speed Test - Test your WPM with style!"""
import curses
import time
import random
import json
import os

SENTENCES = [
    "The quick brown fox jumps over the lazy dog near the riverbank.",
    "Pack my box with five dozen liquor jugs and ship them today.",
    "How vexingly quick daft zebras jump over the sleeping wolf.",
    "The five boxing wizards jump quickly through the morning fog.",
    "Sphinx of black quartz judge my vow to protect the realm.",
    "Two driven jocks help fax my big quiz on quantum physics.",
    "The job requires extra pluck and zeal from every young wage earner.",
    "Crazy Frederick bought many very exquisite opal jewels from the market.",
    "We promptly judged antique ivory buckles for the next prize ceremony.",
    "All questions asked by five watched experts amaze the judge greatly.",
    "Jack amazed a few girls by dropping the antique onyx vase on the floor.",
    "My grandfather picks up quartz and valuable onyx jewels from the beach.",
    "The explorer was frozen in his big kayak just after making quail pie.",
    "While making deep excavations we found some quaint bronze jewelry.",
    "A mad boxer shot a quick gloved jab to the jaw of his dizzy opponent.",
    "Jived fox nymph grabs quick waltz during the late evening show.",
    "Glib jocks quiz nymph to vex dwarf in the enchanted forest today.",
    "Jackdaws love my big sphinx of quartz perched on the old tower.",
    "The quick onyx goblin jumps over the lazy dwarf sleeping by the fire.",
    "Farmer Jack realized that big yellow quilts were expensive to import.",
    "Cozy lummox gives smart squid who asks for job pen and paper.",
    "A quivering Texas zombie fought republic linked jewelry with grace.",
    "Bright vixens jump dozy fowl quack at the beautiful morning sunrise.",
    "Waltz bad nymph for quick jigs vex the sleeping dragon in his cave.",
    "Quick zephyrs blow vexing daft Jim as he walks through autumn leaves.",
    "Programming is the art of telling another human what one wants the computer to do.",
    "Any fool can write code that a computer can understand but good programmers write code humans can understand.",
    "First solve the problem then write the code to make it work perfectly.",
    "Code is like humor and when you have to explain it then it is bad.",
    "Experience is the name everyone gives to their mistakes in software development.",
]

LEADERBOARD_FILE = os.path.expanduser("~/.typing_test_scores.json")


def load_scores():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE) as f:
            return json.load(f)
    return []


def save_score(wpm, accuracy, sentence_count):
    scores = load_scores()
    scores.append({
        "wpm": round(wpm, 1),
        "accuracy": round(accuracy, 1),
        "sentences": sentence_count,
        "date": time.strftime("%Y-%m-%d %H:%M"),
    })
    scores.sort(key=lambda x: x["wpm"], reverse=True)
    scores = scores[:20]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(scores, f, indent=2)
    return scores


def draw_centered(win, y, text, attr=0):
    h, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        win.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


def draw_progress_bar(win, y, x, width, progress, color):
    filled = int(width * progress)
    try:
        win.addstr(y, x, "█" * filled, color)
        win.addstr(y, x + filled, "░" * (width - filled), curses.color_pair(8))
    except curses.error:
        pass


def welcome_screen(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = [
        "╔══════════════════════════════════════╗",
        "║     ⚡ TYPING SPEED TEST ⚡          ║",
        "╠══════════════════════════════════════╣",
        "║                                      ║",
        "║   Test your typing speed and          ║",
        "║   accuracy with random sentences!     ║",
        "║                                      ║",
        "║   🎯 Type each sentence exactly       ║",
        "║   ⏱️  WPM calculated in real-time      ║",
        "║   📊 Scores saved to leaderboard      ║",
        "║                                      ║",
        "╠══════════════════════════════════════╣",
        "║   Press ENTER to start                ║",
        "║   Press L for leaderboard             ║",
        "║   Press Q to quit                     ║",
        "╚══════════════════════════════════════╝",
    ]

    start_y = max(0, (h - len(title)) // 2)
    for i, line in enumerate(title):
        if i in (0, 11, 15):
            draw_centered(stdscr, start_y + i, line, curses.color_pair(3))
        elif i == 1:
            draw_centered(stdscr, start_y + i, line, curses.color_pair(2) | curses.A_BOLD)
        elif i in (12, 13, 14):
            draw_centered(stdscr, start_y + i, line, curses.color_pair(5))
        else:
            draw_centered(stdscr, start_y + i, line, curses.color_pair(3))

    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (curses.KEY_ENTER, 10, 13):
            return "play"
        elif key in (ord('l'), ord('L')):
            return "leaderboard"
        elif key in (ord('q'), ord('Q')):
            return "quit"


def show_leaderboard(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    scores = load_scores()

    draw_centered(stdscr, 1, "📊 LEADERBOARD - TOP 20 📊", curses.color_pair(2) | curses.A_BOLD)
    draw_centered(stdscr, 2, "═" * 50, curses.color_pair(3))

    header = f"{'Rank':<6}{'WPM':<10}{'Accuracy':<12}{'Sentences':<12}{'Date'}"
    draw_centered(stdscr, 4, header, curses.color_pair(5) | curses.A_BOLD)
    draw_centered(stdscr, 5, "─" * 55, curses.color_pair(8))

    if not scores:
        draw_centered(stdscr, 8, "No scores yet! Press ENTER to start typing.", curses.color_pair(4))
    else:
        for i, s in enumerate(scores[:min(15, h - 8)]):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f" {i+1}"
            line = f"{medal:<6}{s['wpm']:<10}{s['accuracy']}%{'':<7}{s['sentences']:<12}{s['date']}"
            color = curses.color_pair(2) if i < 3 else curses.color_pair(1)
            draw_centered(stdscr, 6 + i, line, color)

    draw_centered(stdscr, h - 2, "Press any key to go back", curses.color_pair(8))
    stdscr.refresh()
    stdscr.getch()


def run_test(stdscr):
    h, w = stdscr.getmaxyx()
    sentences = random.sample(SENTENCES, min(5, len(SENTENCES)))

    total_chars = 0
    correct_chars = 0
    total_time = 0
    sentence_count = 0

    for sent_idx, target in enumerate(sentences):
        stdscr.clear()
        typed = ""
        started = False
        start_time = 0

        while True:
            stdscr.clear()

            # Header
            draw_centered(stdscr, 0, f"━━━ Sentence {sent_idx + 1}/{len(sentences)} ━━━",
                         curses.color_pair(3) | curses.A_BOLD)

            # Stats bar
            if total_time > 0:
                overall_wpm = (total_chars / 5) / (total_time / 60)
                overall_acc = (correct_chars / max(1, total_chars)) * 100
            else:
                overall_wpm = 0
                overall_acc = 100

            stats = f"WPM: {overall_wpm:.0f}  |  Accuracy: {overall_acc:.0f}%  |  Completed: {sentence_count}/{len(sentences)}"
            draw_centered(stdscr, 2, stats, curses.color_pair(5))

            # Progress bar
            progress = sent_idx / len(sentences)
            bar_w = min(40, w - 20)
            bar_x = max(0, (w - bar_w) // 2)
            draw_progress_bar(stdscr, 3, bar_x, bar_w, progress, curses.color_pair(2))

            # Current WPM for this sentence
            if started and time.time() - start_time > 0.5:
                current_wpm = (len(typed) / 5) / ((time.time() - start_time) / 60)
                wpm_text = f"Current: {current_wpm:.0f} WPM"
                color = curses.color_pair(2) if current_wpm > 60 else curses.color_pair(4) if current_wpm > 30 else curses.color_pair(1)
                draw_centered(stdscr, 5, wpm_text, color | curses.A_BOLD)

            # Target sentence
            target_y = 8
            draw_centered(stdscr, target_y - 1, "Type this:", curses.color_pair(8))

            # Render target with color coding
            start_x = max(0, (w - len(target)) // 2)
            for i, ch in enumerate(target):
                try:
                    if i < len(typed):
                        if typed[i] == ch:
                            stdscr.addstr(target_y, start_x + i, ch, curses.color_pair(2) | curses.A_BOLD)
                        else:
                            stdscr.addstr(target_y, start_x + i, ch, curses.color_pair(1) | curses.A_BOLD | curses.A_UNDERLINE)
                    else:
                        stdscr.addstr(target_y, start_x + i, ch, curses.color_pair(8))
                except curses.error:
                    pass

            # Typed text
            typed_y = target_y + 2
            draw_centered(stdscr, typed_y - 1, "Your input:", curses.color_pair(8))
            typed_x = max(0, (w - len(target)) // 2)
            for i, ch in enumerate(typed):
                try:
                    if i < len(target) and ch == target[i]:
                        stdscr.addstr(typed_y, typed_x + i, ch, curses.color_pair(2))
                    else:
                        stdscr.addstr(typed_y, typed_x + i, ch, curses.color_pair(1) | curses.A_BOLD)
                except curses.error:
                    pass

            # Cursor
            cursor_pos = typed_x + len(typed)
            if cursor_pos < w:
                try:
                    stdscr.addstr(typed_y, cursor_pos, "▎", curses.color_pair(5) | curses.A_BLINK)
                except curses.error:
                    pass

            # Instructions
            draw_centered(stdscr, h - 2, "ESC to quit  |  Backspace to correct", curses.color_pair(8))

            stdscr.refresh()

            key = stdscr.getch()

            if key == 27:  # ESC
                return total_chars, correct_chars, total_time, sentence_count
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if typed:
                    typed = typed[:-1]
            elif key in (curses.KEY_ENTER, 10, 13):
                if len(typed) >= len(target) * 0.8:  # At least 80% typed
                    elapsed = time.time() - start_time if started else 0
                    total_time += elapsed
                    total_chars += len(target)
                    for i in range(min(len(typed), len(target))):
                        if typed[i] == target[i]:
                            correct_chars += 1
                    sentence_count += 1
                    break
            elif 32 <= key <= 126:
                if not started:
                    started = True
                    start_time = time.time()
                if len(typed) < len(target) + 10:
                    typed += chr(key)
                    # Auto-advance if exact match
                    if typed == target:
                        elapsed = time.time() - start_time
                        total_time += elapsed
                        total_chars += len(target)
                        correct_chars += len(target)
                        sentence_count += 1
                        # Flash green
                        stdscr.clear()
                        draw_centered(stdscr, h // 2, "✓ Perfect!", curses.color_pair(2) | curses.A_BOLD)
                        stdscr.refresh()
                        curses.napms(500)
                        break

    return total_chars, correct_chars, total_time, sentence_count


def results_screen(stdscr, total_chars, correct_chars, total_time, sentence_count):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    if total_time > 0 and total_chars > 0:
        wpm = (total_chars / 5) / (total_time / 60)
        accuracy = (correct_chars / total_chars) * 100
    else:
        wpm = 0
        accuracy = 0

    # Save score
    scores = save_score(wpm, accuracy, sentence_count)
    rank = next((i + 1 for i, s in enumerate(scores) if s["wpm"] == round(wpm, 1)), len(scores))

    # Grade
    if wpm >= 80:
        grade, grade_text = "S", "LEGENDARY TYPIST!"
    elif wpm >= 60:
        grade, grade_text = "A", "Speed Demon!"
    elif wpm >= 45:
        grade, grade_text = "B", "Above Average!"
    elif wpm >= 30:
        grade, grade_text = "C", "Keep Practicing!"
    else:
        grade, grade_text = "D", "Warming Up..."

    results = [
        "╔══════════════════════════════════════╗",
        "║        📊 RESULTS 📊                 ║",
        "╠══════════════════════════════════════╣",
        f"║   WPM:       {wpm:>6.1f}                  ║",
        f"║   Accuracy:  {accuracy:>5.1f}%                  ║",
        f"║   Sentences: {sentence_count:>6}                  ║",
        f"║   Time:      {total_time:>5.1f}s                  ║",
        "╠══════════════════════════════════════╣",
        f"║   Grade: {grade} - {grade_text:<24} ║",
        f"║   Rank:  #{rank:<30} ║",
        "╠══════════════════════════════════════╣",
        "║   ENTER: Play again                  ║",
        "║   L: Leaderboard  Q: Quit            ║",
        "╚══════════════════════════════════════╝",
    ]

    start_y = max(0, (h - len(results)) // 2)
    for i, line in enumerate(results):
        if i in (0, 2, 7, 10, 13):
            draw_centered(stdscr, start_y + i, line, curses.color_pair(3))
        elif i == 1:
            draw_centered(stdscr, start_y + i, line, curses.color_pair(2) | curses.A_BOLD)
        elif i == 8:
            grade_color = curses.color_pair(2) if grade in ("S", "A") else curses.color_pair(4) if grade == "B" else curses.color_pair(1)
            draw_centered(stdscr, start_y + i, line, grade_color | curses.A_BOLD)
        else:
            draw_centered(stdscr, start_y + i, line, curses.color_pair(5))

    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (curses.KEY_ENTER, 10, 13):
            return "play"
        elif key in (ord('l'), ord('L')):
            return "leaderboard"
        elif key in (ord('q'), ord('Q')):
            return "quit"


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    # Color pairs
    curses.init_pair(1, curses.COLOR_RED, -1)        # Errors
    curses.init_pair(2, curses.COLOR_GREEN, -1)       # Correct / success
    curses.init_pair(3, curses.COLOR_YELLOW, -1)      # Borders
    curses.init_pair(4, curses.COLOR_MAGENTA, -1)     # Highlights
    curses.init_pair(5, curses.COLOR_CYAN, -1)        # Info
    curses.init_pair(6, curses.COLOR_BLUE, -1)        # Blue
    curses.init_pair(7, curses.COLOR_WHITE, -1)       # White
    curses.init_pair(8, 240, -1)                      # Dim gray

    stdscr.nodelay(False)
    stdscr.keypad(True)

    action = "welcome"
    while True:
        if action == "welcome":
            action = welcome_screen(stdscr)
        elif action == "play":
            total_chars, correct_chars, total_time, sentence_count = run_test(stdscr)
            if sentence_count > 0:
                action = results_screen(stdscr, total_chars, correct_chars, total_time, sentence_count)
            else:
                action = "welcome"
        elif action == "leaderboard":
            show_leaderboard(stdscr)
            action = "welcome"
        elif action == "quit":
            break


if __name__ == "__main__":
    curses.wrapper(main)


def main_entry():
    import curses
    curses.wrapper(main)

