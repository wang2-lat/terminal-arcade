#!/usr/bin/env python3
"""🧮 Terminal Scientific Calculator with Function Plotting"""
import curses
import math
import ast
import operator
import re


class SafeEvaluator:
    """AST-based safe math expression evaluator."""

    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    FUNCTIONS = {
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
        'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
        'sqrt': math.sqrt,
        'log': math.log, 'log10': math.log10, 'log2': math.log2,
        'ln': math.log, 'exp': math.exp,
        'abs': abs, 'ceil': math.ceil, 'floor': math.floor,
        'round': round, 'factorial': math.factorial,
        'rad': math.radians, 'deg': math.degrees,
    }

    CONSTANTS = {
        'pi': math.pi, 'e': math.e, 'tau': math.tau, 'inf': float('inf'),
    }

    def __init__(self):
        self.variables = dict(self.CONSTANTS)

    def _eval_node(self, node):
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant: {node.value}")
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator")
            return op(operand)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.FUNCTIONS:
                    args = [self._eval_node(arg) for arg in node.args]
                    return self.FUNCTIONS[func_name](*args)
            raise ValueError(f"Unknown function: {ast.dump(node.func)}")
        elif isinstance(node, ast.Name):
            name = node.id
            if name in self.variables:
                return self.variables[name]
            raise ValueError(f"Unknown variable: {name}")
        else:
            raise ValueError(f"Unsupported expression: {type(node).__name__}")

    def evaluate(self, expr):
        expr = expr.strip()
        if not expr:
            return None
        expr = expr.replace('^', '**')
        expr = expr.replace('×', '*')
        expr = expr.replace('÷', '/')
        try:
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree)
        except Exception as e:
            return f"Error: {e}"


class Calculator:
    def __init__(self):
        self.history = []
        self.evaluator = SafeEvaluator()

    def evaluate(self, expr):
        result = self.evaluator.evaluate(expr)
        if result is not None and not (isinstance(result, str) and result.startswith("Error")):
            self.evaluator.variables['ans'] = result
            self.history.append((expr, result))
        return result


def plot_function(expr, x_min=-10, x_max=10, width=60, height=20):
    """Generate ASCII function plot."""
    evaluator = SafeEvaluator()
    points = []
    step = (x_max - x_min) / width

    for i in range(width):
        x = x_min + i * step
        try:
            eval_expr = expr.replace('x', f'({x})')
            y = evaluator.evaluate(eval_expr)
            if isinstance(y, (int, float)) and not math.isnan(y) and not math.isinf(y):
                points.append((i, y))
            else:
                points.append((i, None))
        except:
            points.append((i, None))

    if not points or all(p[1] is None for p in points):
        return ["Error: could not plot function"], 0, 0

    valid = [p[1] for p in points if p[1] is not None]
    if not valid:
        return ["No valid points"], 0, 0

    y_min = min(valid)
    y_max = max(valid)
    if y_min == y_max:
        y_min -= 1
        y_max += 1

    y_range = y_max - y_min
    padding = y_range * 0.1
    y_min -= padding
    y_max += padding
    y_range = y_max - y_min

    grid = [[' '] * width for _ in range(height)]

    # Draw axes
    zero_row = int((y_max / y_range) * (height - 1)) if y_min <= 0 <= y_max else -1
    zero_col = int((-x_min / (x_max - x_min)) * (width - 1)) if x_min <= 0 <= x_max else -1

    if 0 <= zero_row < height:
        for x in range(width):
            grid[zero_row][x] = '─'
    if 0 <= zero_col < width:
        for y in range(height):
            grid[y][zero_col] = '│'
    if 0 <= zero_row < height and 0 <= zero_col < width:
        grid[zero_row][zero_col] = '┼'

    # Plot points
    for i, y_val in points:
        if y_val is None:
            continue
        row = int(((y_max - y_val) / y_range) * (height - 1))
        row = max(0, min(height - 1, row))
        if 0 <= i < width:
            grid[row][i] = '●'

    lines = [''.join(row) for row in grid]
    return lines, y_min, y_max


def draw_centered(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        stdscr.addstr(y, x, text[:w-1], attr)
    except curses.error:
        pass


def main(stdscr):
    curses.curs_set(1)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)
    try:
        curses.init_pair(8, 240, -1)
    except:
        curses.init_pair(8, curses.COLOR_WHITE, -1)

    stdscr.keypad(True)

    calc = Calculator()
    input_buf = ""
    plot_lines = None
    plot_y_min = plot_y_max = 0
    message = ""
    mode = "calc"  # "calc" or "plot"

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        # Header
        header = "🧮 SCIENTIFIC CALCULATOR"
        draw_centered(stdscr, 0, header, curses.color_pair(4) | curses.A_BOLD)
        try:
            stdscr.addstr(1, 0, "═" * (w - 1), curses.color_pair(4))
        except curses.error:
            pass

        if mode == "calc":
            # History
            hist_start = 3
            max_hist = h - 8
            visible_hist = calc.history[-max_hist:] if calc.history else []

            for i, (expr, result) in enumerate(visible_hist):
                y = hist_start + i
                if y >= h - 5:
                    break
                try:
                    stdscr.addstr(y, 2, f"  {expr}", curses.color_pair(2))
                    result_str = f"= {result}"
                    if isinstance(result, float):
                        if result == int(result) and abs(result) < 1e15:
                            result_str = f"= {int(result)}"
                        else:
                            result_str = f"= {result:.10g}"
                    stdscr.addstr(y, max(40, w // 2), result_str, curses.color_pair(3) | curses.A_BOLD)
                except curses.error:
                    pass

            # Message
            if message:
                try:
                    stdscr.addstr(h - 4, 2, message, curses.color_pair(1))
                except curses.error:
                    pass
                message = ""

            # Input area
            try:
                stdscr.addstr(h - 3, 0, "─" * (w - 1), curses.color_pair(8))
                stdscr.addstr(h - 2, 2, "▶ ", curses.color_pair(4) | curses.A_BOLD)
                stdscr.addstr(h - 2, 4, input_buf, curses.color_pair(7))
            except curses.error:
                pass

            # Help
            help_text = "ENTER:Calc | plot <expr>:Graph | ESC:Quit | 'ans'=last result"
            try:
                stdscr.addstr(h - 1, 0, help_text[:w-1], curses.color_pair(8))
            except curses.error:
                pass

        elif mode == "plot":
            if plot_lines:
                plot_start = 3
                for i, line in enumerate(plot_lines):
                    y = plot_start + i
                    if y >= h - 3:
                        break
                    for j, ch in enumerate(line):
                        px = 5 + j
                        if px >= w - 1:
                            break
                        try:
                            if ch == '●':
                                stdscr.addstr(y, px, ch, curses.color_pair(3) | curses.A_BOLD)
                            elif ch in ('─', '│', '┼'):
                                stdscr.addstr(y, px, ch, curses.color_pair(8))
                            elif ch == '·':
                                stdscr.addstr(y, px, ch, curses.color_pair(2))
                            else:
                                stdscr.addstr(y, px, ch)
                        except curses.error:
                            pass

                # Y-axis labels
                try:
                    stdscr.addstr(plot_start, 0, f"{plot_y_max:>4.1f}", curses.color_pair(4))
                    stdscr.addstr(plot_start + len(plot_lines) - 1, 0, f"{plot_y_min:>4.1f}", curses.color_pair(4))
                except curses.error:
                    pass

            try:
                stdscr.addstr(h - 2, 2, "Press any key to go back to calculator", curses.color_pair(2))
            except curses.error:
                pass

        stdscr.refresh()

        if mode == "calc":
            try:
                stdscr.move(h - 2, 4 + len(input_buf))
            except curses.error:
                pass

        key = stdscr.getch()

        if mode == "plot":
            mode = "calc"
            continue

        if key == 27:  # ESC
            break
        elif key in (curses.KEY_ENTER, 10, 13):
            if input_buf.strip():
                stripped = input_buf.strip()

                if stripped.startswith('plot '):
                    expr = stripped[5:].strip()
                    plot_h = min(25, h - 8)
                    plot_w = min(80, w - 12)
                    plot_lines, plot_y_min, plot_y_max = plot_function(expr, width=plot_w, height=plot_h)
                    mode = "plot"
                elif stripped == 'clear':
                    calc.history.clear()
                elif stripped == 'help':
                    message = "Functions: sin cos tan sqrt log exp abs | Variables: pi e ans | plot <expr>"
                else:
                    result = calc.evaluate(stripped)
                    if isinstance(result, str) and result.startswith("Error"):
                        message = result

                input_buf = ""
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            input_buf = input_buf[:-1]
        elif key == curses.KEY_UP:
            if calc.history:
                input_buf = calc.history[-1][0]
        elif 32 <= key <= 126:
            input_buf += chr(key)


if __name__ == "__main__":
    curses.wrapper(main)
