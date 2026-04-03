#!/usr/bin/env python3
"""🎴 Terminal Blackjack - ASCII Card Game with chips!"""
import curses
import random
import time

SUITS = ['♠', '♥', '♦', '♣']
SUIT_COLORS = {'♠': 7, '♣': 7, '♥': 1, '♦': 1}
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
VALUES = {'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
          '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10}


def make_deck(num_decks=2):
    deck = [(r, s) for r in RANKS for s in SUITS] * num_decks
    random.shuffle(deck)
    return deck


def hand_value(hand):
    total = sum(VALUES[r] for r, s in hand)
    aces = sum(1 for r, s in hand if r == 'A')
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def card_art(rank, suit, hidden=False):
    """Return 5-line ASCII art for a card."""
    if hidden:
        return [
            "┌─────┐",
            "│░░░░░│",
            "│░░░░░│",
            "│░░░░░│",
            "└─────┘",
        ]
    r = rank.ljust(2) if len(rank) < 2 else rank
    r2 = rank.rjust(2) if len(rank) < 2 else rank
    return [
        "┌─────┐",
        f"│{r:<2}   │",
        f"│  {suit}  │",
        f"│   {r2:>2}│",
        "└─────┘",
    ]


def draw_hand(stdscr, cards, y, x, h, w, hide_first=False, label=""):
    """Draw a hand of cards side by side."""
    if label:
        try:
            stdscr.addstr(y - 1, x, label, curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass

    for i, (rank, suit) in enumerate(cards):
        hidden = (i == 0 and hide_first)
        art = card_art(rank, suit, hidden)
        color = SUIT_COLORS.get(suit, 7)

        card_x = x + i * 8
        for dy, line in enumerate(art):
            if y + dy < h and card_x + len(line) < w:
                try:
                    if hidden:
                        stdscr.addstr(y + dy, card_x, line, curses.color_pair(6))
                    else:
                        stdscr.addstr(y + dy, card_x, line, curses.color_pair(color))
                except curses.error:
                    pass


def draw_chips(stdscr, y, x, amount, label=""):
    """Draw chip stack."""
    try:
        if label:
            stdscr.addstr(y, x, label, curses.color_pair(4))
        chip_str = f"${amount}"
        color = curses.color_pair(3) if amount > 0 else curses.color_pair(1)
        stdscr.addstr(y, x + len(label), chip_str, color | curses.A_BOLD)
    except curses.error:
        pass


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


def welcome_screen(stdscr):
    h, w = stdscr.getmaxyx()
    stdscr.clear()

    title = [
        "┌────────────────────────────────────┐",
        "│    🎴 TERMINAL BLACKJACK 🎴        │",
        "├────────────────────────────────────┤",
        "│                                    │",
        "│    Try to beat the dealer!          │",
        "│    Get as close to 21 as you can    │",
        "│    without going over.              │",
        "│                                    │",
        "│    H - Hit     S - Stand            │",
        "│    D - Double  (first turn only)    │",
        "│    Q - Quit                         │",
        "│                                    │",
        "│    Press ENTER to start             │",
        "│    Starting chips: $1000            │",
        "│                                    │",
        "└────────────────────────────────────┘",
    ]

    start_y = max(0, (h - len(title)) // 2)
    for i, line in enumerate(title):
        color = curses.color_pair(3) if i in (0, 2, 15) else curses.color_pair(4) if i == 1 else curses.color_pair(2)
        draw_centered(stdscr, start_y + i, line, color)

    stdscr.refresh()
    while True:
        k = stdscr.getch()
        if k in (curses.KEY_ENTER, 10, 13):
            return True
        if k in (ord('q'), ord('Q')):
            return False


def bet_screen(stdscr, chips):
    h, w = stdscr.getmaxyx()
    bet = 50

    while True:
        stdscr.clear()
        draw_centered(stdscr, h // 2 - 4, "═══ PLACE YOUR BET ═══", curses.color_pair(4) | curses.A_BOLD)
        draw_centered(stdscr, h // 2 - 2, f"Your chips: ${chips}", curses.color_pair(3))
        draw_centered(stdscr, h // 2, f"Bet: ${bet}", curses.color_pair(4) | curses.A_BOLD)

        draw_centered(stdscr, h // 2 + 2, "↑/↓: Change bet (+/- $25)", curses.color_pair(2))
        draw_centered(stdscr, h // 2 + 3, "ENTER: Deal  Q: Quit", curses.color_pair(2))

        # Visual chips
        chip_vis = ""
        remaining = bet
        for val, sym in [(100, "◉"), (50, "●"), (25, "○")]:
            count = remaining // val
            remaining %= val
            chip_vis += (sym + " ") * count

        draw_centered(stdscr, h // 2 + 5, chip_vis, curses.color_pair(4))

        stdscr.refresh()
        k = stdscr.getch()

        if k == curses.KEY_UP or k == ord('+') or k == ord('='):
            bet = min(chips, bet + 25)
        elif k == curses.KEY_DOWN or k == ord('-'):
            bet = max(25, bet - 25)
        elif k in (curses.KEY_ENTER, 10, 13):
            return bet
        elif k in (ord('q'), ord('Q')):
            return -1


def play_round(stdscr, deck, chips, bet):
    h, w = stdscr.getmaxyx()

    if len(deck) < 15:
        deck.clear()
        deck.extend(make_deck())

    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]

    doubled = False
    player_done = False
    result = ""
    winnings = 0

    # Check for blackjack
    if hand_value(player) == 21:
        player_done = True

    while True:
        stdscr.clear()

        # Table felt
        draw_centered(stdscr, 0, "═" * (w - 2), curses.color_pair(3))

        # Dealer
        dealer_val = hand_value(dealer[:1]) if not player_done else hand_value(dealer)
        hide = not player_done
        draw_hand(stdscr, dealer, 2, 4, h, w, hide_first=hide,
                 label=f"DEALER ({dealer_val if not hide else '?'})  ")

        # Player
        pval = hand_value(player)
        draw_hand(stdscr, player, h // 2 + 2, 4, h, w,
                 label=f"YOU ({pval})  ")

        # Chips info
        draw_chips(stdscr, h - 4, 4, chips, "Chips: ")
        draw_chips(stdscr, h - 4, 25, bet, "Bet: ")

        if result:
            color = curses.color_pair(3) if "WIN" in result or "BLACKJACK" in result else \
                    curses.color_pair(1) if "LOSE" in result or "BUST" in result else curses.color_pair(4)
            draw_centered(stdscr, h // 2, f"  {result}  ", color | curses.A_BOLD)
            if winnings > 0:
                draw_centered(stdscr, h // 2 + 1, f"+${winnings}", curses.color_pair(3) | curses.A_BOLD)
            elif winnings < 0:
                draw_centered(stdscr, h // 2 + 1, f"-${abs(winnings)}", curses.color_pair(1) | curses.A_BOLD)
            draw_centered(stdscr, h - 2, "ENTER: Next hand  Q: Quit", curses.color_pair(2))
        elif not player_done:
            controls = "H: Hit  S: Stand"
            if len(player) == 2 and chips >= bet:
                controls += "  D: Double Down"
            draw_centered(stdscr, h - 2, controls, curses.color_pair(2))
        else:
            draw_centered(stdscr, h - 2, "Dealer's turn...", curses.color_pair(4))

        stdscr.refresh()

        if result:
            k = stdscr.getch()
            if k in (curses.KEY_ENTER, 10, 13):
                return chips + winnings, False
            elif k in (ord('q'), ord('Q')):
                return chips + winnings, True
            continue

        if player_done:
            # Dealer plays
            time.sleep(0.5)
            dval = hand_value(dealer)
            if hand_value(player) == 21 and len(player) == 2:
                # Player blackjack
                if dval == 21 and len(dealer) == 2:
                    result = "PUSH - Both Blackjack!"
                    winnings = 0
                else:
                    result = "🎉 BLACKJACK! 🎉"
                    winnings = int(bet * 1.5)
            elif hand_value(player) > 21:
                result = "💥 BUST! 💥"
                winnings = -bet
            else:
                while dval < 17:
                    dealer.append(deck.pop())
                    dval = hand_value(dealer)
                    # Redraw
                    stdscr.clear()
                    draw_centered(stdscr, 0, "═" * (w - 2), curses.color_pair(3))
                    draw_hand(stdscr, dealer, 2, 4, h, w, label=f"DEALER ({dval})  ")
                    draw_hand(stdscr, player, h // 2 + 2, 4, h, w, label=f"YOU ({hand_value(player)})  ")
                    draw_chips(stdscr, h - 4, 4, chips, "Chips: ")
                    draw_chips(stdscr, h - 4, 25, bet, "Bet: ")
                    draw_centered(stdscr, h - 2, "Dealer hits...", curses.color_pair(4))
                    stdscr.refresh()
                    time.sleep(0.7)

                pval = hand_value(player)
                if dval > 21:
                    result = "🎉 DEALER BUSTS - YOU WIN! 🎉"
                    winnings = bet
                elif pval > dval:
                    result = "🎉 YOU WIN! 🎉"
                    winnings = bet
                elif pval < dval:
                    result = "DEALER WINS"
                    winnings = -bet
                else:
                    result = "PUSH"
                    winnings = 0

            if doubled:
                winnings *= 2
            continue

        k = stdscr.getch()
        if k in (ord('h'), ord('H')):
            player.append(deck.pop())
            if hand_value(player) >= 21:
                player_done = True
        elif k in (ord('s'), ord('S')):
            player_done = True
        elif k in (ord('d'), ord('D')) and len(player) == 2 and chips >= bet:
            doubled = True
            bet *= 2
            player.append(deck.pop())
            player_done = True
        elif k in (ord('q'), ord('Q')):
            return chips, True


def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    stdscr.keypad(True)

    if not welcome_screen(stdscr):
        return

    chips = 1000
    deck = make_deck()

    while chips >= 25:
        bet = bet_screen(stdscr, chips)
        if bet < 0:
            break

        chips, quit_game = play_round(stdscr, deck, chips, bet)
        if quit_game:
            break

    # Final screen
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    if chips < 25:
        draw_centered(stdscr, h // 2 - 1, "💸 You're broke! 💸", curses.color_pair(1) | curses.A_BOLD)
    else:
        profit = chips - 1000
        if profit > 0:
            draw_centered(stdscr, h // 2 - 1, f"Walking away with ${chips} (+${profit})", curses.color_pair(3) | curses.A_BOLD)
        else:
            draw_centered(stdscr, h // 2 - 1, f"Walking away with ${chips} ({profit})", curses.color_pair(1) | curses.A_BOLD)

    draw_centered(stdscr, h // 2 + 1, "Thanks for playing! Press any key.", curses.color_pair(2))
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)
