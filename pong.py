#!/usr/bin/env python3
"""🏓 Terminal Pong - Classic arcade with AI opponent!"""
import curses
import time
import math
import random

PADDLE_HEIGHT = 5
BALL_CHARS = ["●", "◉", "○"]


class Paddle:
    def __init__(self, x, h):
        self.x = x
        self.y = h // 2 - PADDLE_HEIGHT // 2
        self.height = PADDLE_HEIGHT
        self.score = 0
        self.speed = 1.5

    def move_up(self):
        self.y = max(1, self.y - self.speed)

    def move_down(self, h):
        self.y = min(h - 2 - self.height, self.y + self.speed)

    def draw(self, stdscr, color):
        for i in range(self.height):
            py = int(self.y) + i
            try:
                if i == 0:
                    stdscr.addstr(py, self.x, "╔", curses.color_pair(color) | curses.A_BOLD)
                elif i == self.height - 1:
                    stdscr.addstr(py, self.x, "╚", curses.color_pair(color) | curses.A_BOLD)
                else:
                    stdscr.addstr(py, self.x, "║", curses.color_pair(color) | curses.A_BOLD)
            except curses.error:
                pass


class Ball:
    def __init__(self, h, w):
        self.reset(h, w)

    def reset(self, h, w):
        self.x = w / 2
        self.y = h / 2
        angle = random.uniform(-0.5, 0.5)
        direction = random.choice([-1, 1])
        self.vx = direction * 0.6 * math.cos(angle)
        self.vy = 0.4 * math.sin(angle)
        self.speed = 0.6
        self.trail = []

    def update(self, dt, h):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)

        self.x += self.vx * dt * 40
        self.y += self.vy * dt * 40

        # Bounce off top/bottom
        if self.y <= 1:
            self.y = 1
            self.vy = abs(self.vy)
        elif self.y >= h - 2:
            self.y = h - 2
            self.vy = -abs(self.vy)

    def draw(self, stdscr):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            ix, iy = int(tx), int(ty)
            try:
                alpha = i / len(self.trail)
                ch = "·" if alpha < 0.5 else "•"
                stdscr.addstr(iy, ix, ch, curses.color_pair(8))
            except curses.error:
                pass

        # Ball
        bx, by = int(self.x), int(self.y)
        try:
            stdscr.addstr(by, bx, "●", curses.color_pair(7) | curses.A_BOLD)
        except curses.error:
            pass


class AI:
    def __init__(self, difficulty=0.7):
        self.difficulty = difficulty  # 0=easy, 1=hard
        self.reaction_delay = 0
        self.target_y = 0

    def update(self, paddle, ball, h, dt):
        self.reaction_delay -= dt
        if self.reaction_delay <= 0:
            self.reaction_delay = 0.1 * (1 - self.difficulty * 0.5)
            # Predict ball position
            if ball.vx > 0:  # Ball coming towards AI
                time_to_reach = (paddle.x - ball.x) / (ball.vx * 40) if ball.vx > 0 else 0
                predicted_y = ball.y + ball.vy * 40 * time_to_reach
                # Bounce prediction
                while predicted_y < 1 or predicted_y > h - 2:
                    if predicted_y < 1:
                        predicted_y = 2 - predicted_y
                    if predicted_y > h - 2:
                        predicted_y = 2 * (h - 2) - predicted_y
                self.target_y = predicted_y + random.gauss(0, 2 * (1 - self.difficulty))
            else:
                self.target_y = h / 2  # Return to center

        center = paddle.y + paddle.height / 2
        if center < self.target_y - 1:
            paddle.move_down(h)
        elif center > self.target_y + 1:
            paddle.move_up()


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


def draw_net(stdscr, h, w):
    cx = w // 2
    for y in range(1, h - 1):
        if y % 2 == 0:
            try:
                stdscr.addstr(y, cx, "│", curses.color_pair(8) | curses.A_DIM)
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

    # Welcome
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    title = [
        "╔══════════════════════════╗",
        "║     🏓 TERMINAL PONG 🏓  ║",
        "╠══════════════════════════╣",
        "║                          ║",
        "║  W/S or ↑/↓: Move paddle ║",
        "║  First to 11 wins!       ║",
        "║                          ║",
        "║  1: Easy AI              ║",
        "║  2: Medium AI            ║",
        "║  3: Hard AI              ║",
        "║  Q: Quit                 ║",
        "║                          ║",
        "╚══════════════════════════╝",
    ]
    for i, line in enumerate(title):
        color = curses.color_pair(3) if i in (0, 2, 12) else curses.color_pair(4) if i == 1 else curses.color_pair(2)
        draw_centered(stdscr, h // 2 - len(title) // 2 + i, line, color)
    stdscr.refresh()

    ai_difficulty = 0.5
    while True:
        k = stdscr.getch()
        if k == ord('1'):
            ai_difficulty = 0.3
            break
        elif k == ord('2'):
            ai_difficulty = 0.6
            break
        elif k == ord('3'):
            ai_difficulty = 0.9
            break
        elif k in (ord('q'), ord('Q')):
            return

    # Game setup
    stdscr.nodelay(True)
    h, w = stdscr.getmaxyx()

    p1 = Paddle(2, h)
    p2 = Paddle(w - 3, h)
    ball = Ball(h, w)
    ai = AI(ai_difficulty)

    last_time = time.time()
    win_score = 11
    paused = False
    game_over = False
    countdown = 3
    countdown_timer = 0

    while True:
        now = time.time()
        dt = min(now - last_time, 0.1)
        last_time = now

        h, w = stdscr.getmaxyx()
        p2.x = w - 3

        # Input
        keys = set()
        while True:
            try:
                k = stdscr.getch()
                if k == -1:
                    break
                keys.add(k)
            except:
                break

        if ord('q') in keys or ord('Q') in keys:
            break
        if ord('p') in keys or ord('P') in keys:
            paused = not paused
        if ord('r') in keys or ord('R') in keys:
            p1.score = 0
            p2.score = 0
            ball.reset(h, w)
            game_over = False
            countdown = 3

        if paused or game_over:
            stdscr.erase()
            # Draw field
            try:
                stdscr.addstr(0, 0, "═" * (w - 1), curses.color_pair(3))
                stdscr.addstr(h - 1, 0, "═" * (w - 1), curses.color_pair(3))
            except curses.error:
                pass
            draw_net(stdscr, h, w)
            p1.draw(stdscr, 2)
            p2.draw(stdscr, 1)
            ball.draw(stdscr)

            # Score
            score_text = f"  {p1.score}  │  {p2.score}  "
            draw_centered(stdscr, 0, score_text, curses.color_pair(3) | curses.A_BOLD)

            if game_over:
                winner = "YOU WIN!" if p1.score >= win_score else "AI WINS!"
                color = curses.color_pair(2) if p1.score >= win_score else curses.color_pair(1)
                draw_centered(stdscr, h // 2 - 1, f"  {winner}  ", color | curses.A_BOLD)
                draw_centered(stdscr, h // 2 + 1, "R: Rematch  Q: Quit", curses.color_pair(8))
            else:
                draw_centered(stdscr, h // 2, "PAUSED", curses.color_pair(3) | curses.A_BOLD)

            stdscr.refresh()
            time.sleep(0.05)
            continue

        # Countdown
        if countdown > 0:
            countdown_timer += dt
            if countdown_timer >= 1:
                countdown -= 1
                countdown_timer = 0

            stdscr.erase()
            try:
                stdscr.addstr(0, 0, "═" * (w - 1), curses.color_pair(3))
                stdscr.addstr(h - 1, 0, "═" * (w - 1), curses.color_pair(3))
            except curses.error:
                pass
            draw_net(stdscr, h, w)
            p1.draw(stdscr, 2)
            p2.draw(stdscr, 1)
            if countdown > 0:
                draw_centered(stdscr, h // 2, str(countdown), curses.color_pair(3) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(0.05)
            continue

        # Player movement
        if curses.KEY_UP in keys or ord('w') in keys:
            p1.move_up()
        if curses.KEY_DOWN in keys or ord('s') in keys:
            p1.move_down(h)

        # AI movement
        ai.update(p2, ball, h, dt)

        # Ball update
        ball.update(dt, h)

        # Paddle collision
        # Left paddle
        if (ball.x <= p1.x + 1 and ball.vx < 0 and
            p1.y <= ball.y <= p1.y + p1.height):
            ball.vx = abs(ball.vx) * 1.05  # Speed up slightly
            offset = (ball.y - p1.y - p1.height / 2) / (p1.height / 2)
            ball.vy += offset * 0.3

        # Right paddle
        if (ball.x >= p2.x - 1 and ball.vx > 0 and
            p2.y <= ball.y <= p2.y + p2.height):
            ball.vx = -abs(ball.vx) * 1.05
            offset = (ball.y - p2.y - p2.height / 2) / (p2.height / 2)
            ball.vy += offset * 0.3

        # Scoring
        if ball.x < 0:
            p2.score += 1
            ball.reset(h, w)
            countdown = 1
            if p2.score >= win_score:
                game_over = True
        elif ball.x > w:
            p1.score += 1
            ball.reset(h, w)
            countdown = 1
            if p1.score >= win_score:
                game_over = True

        # Draw
        stdscr.erase()

        # Borders
        try:
            stdscr.addstr(0, 0, "═" * (w - 1), curses.color_pair(3))
            stdscr.addstr(h - 1, 0, "═" * (w - 1), curses.color_pair(3))
        except curses.error:
            pass

        draw_net(stdscr, h, w)

        # Score display
        score_text = f"  {p1.score}  │  {p2.score}  "
        draw_centered(stdscr, 0, score_text, curses.color_pair(3) | curses.A_BOLD)

        # Labels
        try:
            stdscr.addstr(0, 3, "YOU", curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(0, w - 5, "AI", curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass

        p1.draw(stdscr, 2)
        p2.draw(stdscr, 1)
        ball.draw(stdscr)

        stdscr.refresh()
        time.sleep(0.016)


if __name__ == "__main__":
    curses.wrapper(main)
