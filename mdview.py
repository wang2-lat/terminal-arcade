#!/usr/bin/env python3
"""📝 Terminal Markdown Viewer - Render markdown with colors in terminal"""
import curses
import sys
import re
import os


def parse_markdown(text):
    """Parse markdown into styled segments."""
    lines = text.split('\n')
    result = []  # List of (line_text, style) where style is a dict

    for line in lines:
        stripped = line.strip()

        # Headers
        if stripped.startswith('######'):
            result.append((stripped[6:].strip(), {"type": "h6", "color": 5}))
        elif stripped.startswith('#####'):
            result.append((stripped[5:].strip(), {"type": "h5", "color": 5}))
        elif stripped.startswith('####'):
            result.append((stripped[4:].strip(), {"type": "h4", "color": 4}))
        elif stripped.startswith('###'):
            result.append((stripped[3:].strip(), {"type": "h3", "color": 3}))
        elif stripped.startswith('##'):
            result.append(("", {"type": "blank"}))
            result.append((stripped[2:].strip(), {"type": "h2", "color": 2}))
            result.append(("─" * 40, {"type": "hr", "color": 8}))
        elif stripped.startswith('#'):
            result.append(("", {"type": "blank"}))
            result.append((stripped[1:].strip(), {"type": "h1", "color": 3}))
            result.append(("═" * 40, {"type": "hr", "color": 3}))
        # Horizontal rule
        elif re.match(r'^[-*_]{3,}$', stripped):
            result.append(("─" * 40, {"type": "hr", "color": 8}))
        # Code block
        elif stripped.startswith('```'):
            result.append(("┌─ code ─────────────────────", {"type": "code_border", "color": 6}))
        # Blockquote
        elif stripped.startswith('>'):
            text = stripped[1:].strip()
            result.append(("  │ " + text, {"type": "quote", "color": 4}))
        # Unordered list
        elif re.match(r'^[-*+]\s', stripped):
            text = stripped[2:].strip()
            result.append(("  • " + text, {"type": "list", "color": 7}))
        # Ordered list
        elif re.match(r'^\d+\.\s', stripped):
            text = re.sub(r'^\d+\.\s', '', stripped)
            num = re.match(r'^(\d+)', stripped).group(1)
            result.append((f"  {num}. " + text, {"type": "olist", "color": 7}))
        # Checkbox
        elif stripped.startswith('- [x]') or stripped.startswith('- [X]'):
            result.append(("  ☑ " + stripped[5:].strip(), {"type": "check", "color": 2}))
        elif stripped.startswith('- [ ]'):
            result.append(("  ☐ " + stripped[5:].strip(), {"type": "uncheck", "color": 8}))
        # Table (basic)
        elif '|' in stripped and not stripped.startswith('```'):
            cells = [c.strip() for c in stripped.split('|') if c.strip()]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                result.append(("  " + "─" * 40, {"type": "table_sep", "color": 8}))
            else:
                row = "  │ " + " │ ".join(f"{c:<15}" for c in cells) + " │"
                result.append((row, {"type": "table", "color": 4}))
        # Blank line
        elif not stripped:
            result.append(("", {"type": "blank"}))
        # Regular text
        else:
            result.append(("  " + line.rstrip(), {"type": "text", "color": 7}))

    return result


def render_inline(stdscr, y, x, text, base_color, max_w):
    """Render inline markdown (bold, italic, code, links)."""
    pos = x
    i = 0
    while i < len(text) and pos < max_w - 1:
        # Bold
        m = re.match(r'\*\*(.+?)\*\*', text[i:])
        if m:
            for ch in m.group(1):
                if pos < max_w - 1:
                    try:
                        stdscr.addstr(y, pos, ch, curses.color_pair(base_color) | curses.A_BOLD)
                    except curses.error:
                        pass
                    pos += 1
            i += m.end()
            continue

        # Italic
        m = re.match(r'\*(.+?)\*', text[i:])
        if m:
            for ch in m.group(1):
                if pos < max_w - 1:
                    try:
                        stdscr.addstr(y, pos, ch, curses.color_pair(base_color) | curses.A_UNDERLINE)
                    except curses.error:
                        pass
                    pos += 1
            i += m.end()
            continue

        # Inline code
        m = re.match(r'`(.+?)`', text[i:])
        if m:
            code = m.group(1)
            try:
                stdscr.addstr(y, pos, f" {code} ", curses.color_pair(6) | curses.A_BOLD)
            except curses.error:
                pass
            pos += len(code) + 2
            i += m.end()
            continue

        # Link
        m = re.match(r'\[(.+?)\]\((.+?)\)', text[i:])
        if m:
            link_text = m.group(1)
            for ch in link_text:
                if pos < max_w - 1:
                    try:
                        stdscr.addstr(y, pos, ch, curses.color_pair(4) | curses.A_UNDERLINE)
                    except curses.error:
                        pass
                    pos += 1
            i += m.end()
            continue

        # Regular char
        try:
            stdscr.addstr(y, pos, text[i], curses.color_pair(base_color))
        except curses.error:
            pass
        pos += 1
        i += 1


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

    # Load file
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.exists(filepath):
            with open(filepath) as f:
                md_text = f.read()
            title = os.path.basename(filepath)
        else:
            md_text = f"# Error\n\nFile not found: `{filepath}`"
            title = "Error"
    else:
        md_text = """# 📝 Terminal Markdown Viewer

## Features

- **Bold text** and *italic text* rendering
- `inline code` highlighting
- [Links](https://example.com) with underline

## Code Blocks

```python
def hello():
    print("Hello, World!")
```

## Lists

- First item
- Second item with **bold**
- Third item with `code`

1. Ordered one
2. Ordered two
3. Ordered three

## Checkboxes

- [x] Completed task
- [ ] Pending task
- [x] Another done

## Blockquotes

> This is a quote
> It can span multiple lines

## Tables

| Name | Language | Stars |
|------|----------|-------|
| Terminal Arcade | Python | 1000 |
| Fun Projects | Curses | 500 |

---

*Pass a .md file as argument to view it!*

Press **Q** to quit, **↑/↓** to scroll.
"""
        title = "Demo"

    parsed = parse_markdown(md_text)
    scroll = 0

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()

        # Title bar
        try:
            stdscr.addstr(0, 0, f" 📝 {title} ", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(0, w - 20, f"Lines: {len(parsed)}", curses.color_pair(8))
        except curses.error:
            pass

        # Content
        visible = h - 3
        for i, (text, style) in enumerate(parsed[scroll:scroll + visible]):
            y = 1 + i
            color = style.get("color", 7)
            stype = style.get("type", "text")

            if stype in ("h1", "h2"):
                try:
                    stdscr.addstr(y, 2, text[:w-4], curses.color_pair(color) | curses.A_BOLD)
                except curses.error:
                    pass
            elif stype in ("h3", "h4", "h5", "h6"):
                prefix = "  " * (int(stype[1]) - 2)
                try:
                    stdscr.addstr(y, 2, prefix + text[:w-4], curses.color_pair(color) | curses.A_BOLD)
                except curses.error:
                    pass
            elif stype == "hr":
                try:
                    stdscr.addstr(y, 2, text[:w-4], curses.color_pair(color) | curses.A_DIM)
                except curses.error:
                    pass
            elif stype == "code_border":
                try:
                    stdscr.addstr(y, 2, text[:w-4], curses.color_pair(color))
                except curses.error:
                    pass
            elif stype in ("text", "list", "olist", "quote", "check", "uncheck"):
                render_inline(stdscr, y, 0, text, color, w)
            elif stype in ("table", "table_sep"):
                try:
                    stdscr.addstr(y, 0, text[:w-1], curses.color_pair(color))
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addstr(y, 0, text[:w-1], curses.color_pair(color))
                except curses.error:
                    pass

        # Scrollbar
        if len(parsed) > visible:
            bar_h = max(1, int(visible * visible / len(parsed)))
            bar_pos = int(scroll / max(1, len(parsed) - visible) * (visible - bar_h))
            for i in range(visible):
                try:
                    ch = "█" if bar_pos <= i < bar_pos + bar_h else "░"
                    stdscr.addstr(1 + i, w - 1, ch, curses.color_pair(8))
                except curses.error:
                    pass

        # Status bar
        try:
            pct = int(scroll / max(1, len(parsed) - visible) * 100) if len(parsed) > visible else 100
            status = f" ↑/↓:Scroll  PgUp/PgDn  Q:Quit  {pct}% "
            stdscr.addstr(h - 1, 0, status[:w-1], curses.color_pair(8))
        except curses.error:
            pass

        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        elif key == curses.KEY_UP or key == ord('k'):
            scroll = max(0, scroll - 1)
        elif key == curses.KEY_DOWN or key == ord('j'):
            scroll = min(max(0, len(parsed) - (h - 3)), scroll + 1)
        elif key == curses.KEY_PPAGE:
            scroll = max(0, scroll - (h - 5))
        elif key == curses.KEY_NPAGE:
            scroll = min(max(0, len(parsed) - (h - 3)), scroll + (h - 5))
        elif key == curses.KEY_HOME:
            scroll = 0
        elif key == curses.KEY_END:
            scroll = max(0, len(parsed) - (h - 3))


if __name__ == "__main__":
    curses.wrapper(main)
