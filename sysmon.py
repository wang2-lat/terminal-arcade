#!/usr/bin/env python3
"""
SysMon - Terminal System Monitoring Dashboard

A beautiful Hollywood-style system monitoring TUI built with curses and psutil.

Controls:
  q / Q - Quit
  1     - Toggle CPU panel
  2     - Toggle Memory panel
  3     - Toggle Disk panel
  4     - Toggle Network panel
  5     - Toggle Processes panel

Usage:
  python3 sysmon.py
  sysmon          (if launcher installed)
"""

import curses
import locale
import os
import platform
import socket
import sys
import time
from collections import deque
from datetime import timedelta

import psutil

# Wide-char support
locale.setlocale(locale.LC_ALL, "")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPARKLINE_CHARS = " ▁▂▃▄▅▆▇█"
REFRESH_INTERVAL = 1.0
CPU_HISTORY_LEN = 60  # seconds of rolling history

# Box-drawing characters (single-line)
BOX_TL = "╭"
BOX_TR = "╮"
BOX_BL = "╰"
BOX_BR = "╯"
BOX_H = "─"
BOX_V = "│"
BOX_T_DOWN = "┬"
BOX_T_UP = "┴"
BOX_T_RIGHT = "├"
BOX_T_LEFT = "┤"
BOX_CROSS = "┼"

# Color pair IDs
C_NORMAL = 1
C_GREEN = 2
C_YELLOW = 3
C_RED = 4
C_CYAN = 5
C_BLUE = 6
C_MAGENTA = 7
C_HEADER = 8
C_BORDER = 9
C_DIM = 10
C_WHITE_BOLD = 11
C_SPARK_LOW = 12
C_SPARK_MED = 13
C_SPARK_HIGH = 14
C_TITLE = 15
C_BAR_BG = 16

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def human_bytes(n: float) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"


def human_rate(n: float) -> str:
    """Convert bytes/sec to human-readable rate."""
    return human_bytes(n) + "/s"


def get_uptime() -> str:
    """Get system uptime as a human-readable string."""
    boot = psutil.boot_time()
    delta = timedelta(seconds=time.time() - boot)
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def color_for_pct(pct: float) -> int:
    """Return color pair number based on percentage threshold."""
    if pct >= 80:
        return C_RED
    elif pct >= 50:
        return C_YELLOW
    return C_GREEN


def sparkline_char(value: float, lo: float = 0.0, hi: float = 100.0) -> str:
    """Map a value to a sparkline block character."""
    if hi <= lo:
        return SPARKLINE_CHARS[0]
    normalized = max(0.0, min(1.0, (value - lo) / (hi - lo)))
    idx = int(normalized * (len(SPARKLINE_CHARS) - 1))
    return SPARKLINE_CHARS[idx]


def sparkline_color(value: float) -> int:
    """Return color pair for sparkline character based on value."""
    if value >= 80:
        return C_SPARK_HIGH
    elif value >= 50:
        return C_SPARK_MED
    return C_SPARK_LOW


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------


def draw_box(win, y: int, x: int, h: int, w: int, title: str = "", color: int = C_BORDER):
    """Draw a box with rounded corners and optional title."""
    max_y, max_x = win.getmaxyx()
    if y >= max_y or x >= max_x or h < 2 or w < 4:
        return

    # Clamp dimensions
    h = min(h, max_y - y)
    w = min(w, max_x - x)

    try:
        # Top border
        win.addstr(y, x, BOX_TL, curses.color_pair(color))
        win.addstr(y, x + 1, BOX_H * (w - 2), curses.color_pair(color))
        if x + w - 1 < max_x:
            win.addstr(y, x + w - 1, BOX_TR, curses.color_pair(color))

        # Title
        if title and w > 6:
            t = f" {title} "
            t = t[: w - 4]
            tx = x + 2
            win.addstr(y, tx, t, curses.color_pair(C_TITLE) | curses.A_BOLD)

        # Side borders
        for row in range(1, h - 1):
            if y + row < max_y:
                win.addstr(y + row, x, BOX_V, curses.color_pair(color))
                if x + w - 1 < max_x:
                    win.addstr(y + row, x + w - 1, BOX_V, curses.color_pair(color))

        # Bottom border
        if y + h - 1 < max_y:
            win.addstr(y + h - 1, x, BOX_BL, curses.color_pair(color))
            win.addstr(y + h - 1, x + 1, BOX_H * (w - 2), curses.color_pair(color))
            if x + w - 1 < max_x:
                try:
                    win.addstr(y + h - 1, x + w - 1, BOX_BR, curses.color_pair(color))
                except curses.error:
                    pass  # Bottom-right corner of screen
    except curses.error:
        pass


def draw_bar(win, y: int, x: int, width: int, pct: float, label: str = "",
             show_pct: bool = True, extra: str = ""):
    """Draw a colored progress bar with label."""
    max_y, max_x = win.getmaxyx()
    if y >= max_y or x >= max_x:
        return

    color = color_for_pct(pct)
    bar_width = max(1, width - 2)

    filled = int(bar_width * pct / 100.0)
    filled = min(filled, bar_width)

    try:
        # Label on the left
        if label:
            lbl = label[:12].ljust(12)
            win.addstr(y, x, lbl, curses.color_pair(C_DIM))
            bx = x + 13
        else:
            bx = x

        remaining_w = max_x - bx - 1
        actual_bar = min(bar_width, remaining_w - 15)
        if actual_bar < 1:
            return

        # Draw bar
        win.addstr(y, bx, "[", curses.color_pair(C_BORDER))
        filled_actual = int(actual_bar * pct / 100.0)
        bar_str = "█" * filled_actual + "░" * (actual_bar - filled_actual)
        # Draw filled part
        win.addstr(y, bx + 1, "█" * filled_actual, curses.color_pair(color) | curses.A_BOLD)
        # Draw empty part
        win.addstr(y, bx + 1 + filled_actual, "░" * (actual_bar - filled_actual),
                   curses.color_pair(C_DIM))
        win.addstr(y, bx + 1 + actual_bar, "]", curses.color_pair(C_BORDER))

        # Percentage
        if show_pct:
            pct_str = f" {pct:5.1f}%"
            win.addstr(y, bx + actual_bar + 2, pct_str, curses.color_pair(color) | curses.A_BOLD)

        # Extra info (e.g., "4.2GB / 16.0GB")
        if extra:
            ex = f" {extra}"
            ex_x = bx + actual_bar + 9
            if ex_x + len(ex) < max_x:
                win.addstr(y, ex_x, ex, curses.color_pair(C_DIM))
    except curses.error:
        pass


def safe_addstr(win, y: int, x: int, text: str, attr=0):
    """Write string safely, ignoring out-of-bounds."""
    max_y, max_x = win.getmaxyx()
    if y >= max_y or x >= max_x:
        return
    try:
        # Truncate to fit
        avail = max_x - x - 1
        if avail <= 0:
            return
        win.addstr(y, x, text[:avail], attr)
    except curses.error:
        pass


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------


def render_header(win, y: int, x: int, w: int) -> int:
    """Render system info header. Returns height used."""
    h = 4
    draw_box(win, y, x, h, w, "SYSTEM MONITOR", C_CYAN)

    hostname = socket.gethostname()
    os_info = f"{platform.system()} {platform.release()}"
    uptime = get_uptime()
    py_ver = platform.python_version()
    cpu_model = ""
    try:
        if platform.system() == "Darwin":
            import subprocess
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=2
            )
            cpu_model = result.stdout.strip()
        else:
            cpu_model = platform.processor() or "Unknown"
    except Exception:
        cpu_model = platform.processor() or "Unknown"

    cpu_count = psutil.cpu_count(logical=True)
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    # Line 1: hostname, OS, uptime
    line1_parts = [
        (f"  ◈ {hostname}", C_CYAN),
        (f"  {os_info}", C_DIM),
        (f"  ↑ {uptime}", C_GREEN),
        (f"  py{py_ver}", C_MAGENTA),
    ]
    cx = x + 1
    for text, color in line1_parts:
        safe_addstr(win, y + 1, cx, text, curses.color_pair(color) | curses.A_BOLD)
        cx += len(text) + 1

    # Line 2: CPU model, cores, time
    line2_parts = [
        (f"  ⊕ {cpu_model}", C_DIM),
        (f"  [{cpu_count} cores]", C_BLUE),
        (f"  ⏱ {now}", C_DIM),
    ]
    cx = x + 1
    for text, color in line2_parts:
        safe_addstr(win, y + 2, cx, text, curses.color_pair(color))
        cx += len(text) + 1

    return h


def render_cpu_panel(win, y: int, x: int, w: int, h: int,
                     cpu_history: deque, per_cpu: list[float]) -> int:
    """Render CPU usage panel with sparkline graph. Returns height used."""
    draw_box(win, y, x, h, w, "CPU USAGE", C_GREEN)

    inner_w = w - 4
    inner_x = x + 2
    row = y + 1

    # Overall CPU with sparkline
    overall = cpu_history[-1] if cpu_history else 0.0
    color = color_for_pct(overall)

    label = f"  CPU Total: {overall:5.1f}%"
    safe_addstr(win, row, inner_x, label, curses.color_pair(color) | curses.A_BOLD)
    row += 1

    # Sparkline graph - rolling 60s
    graph_w = min(inner_w, 60)
    history_slice = list(cpu_history)[-graph_w:]
    if len(history_slice) < graph_w:
        history_slice = [0.0] * (graph_w - len(history_slice)) + history_slice

    spark_str = ""
    spark_colors = []
    for val in history_slice:
        spark_str += sparkline_char(val)
        spark_colors.append(sparkline_color(val))

    # Draw sparkline with per-character coloring
    for i, (ch, sc) in enumerate(zip(spark_str, spark_colors)):
        if inner_x + i < x + w - 2:
            safe_addstr(win, row, inner_x + i, ch, curses.color_pair(sc) | curses.A_BOLD)
    row += 1

    # Time axis labels
    axis = "60s ago" + " " * max(0, graph_w - 11) + "now"
    safe_addstr(win, row, inner_x, axis[:inner_w], curses.color_pair(C_DIM))
    row += 1

    # Per-core mini bars (compact, 2 per line)
    if per_cpu and row < y + h - 1:
        cols = 2
        col_w = inner_w // cols
        for i, pct in enumerate(per_cpu):
            col = i % cols
            r = row + i // cols
            if r >= y + h - 1:
                break
            cx = inner_x + col * col_w
            core_label = f"C{i:<2}"
            c = color_for_pct(pct)
            bar_len = max(1, col_w - 12)
            filled = int(bar_len * pct / 100.0)
            safe_addstr(win, r, cx, core_label, curses.color_pair(C_DIM))
            safe_addstr(win, r, cx + 4, "█" * filled, curses.color_pair(c))
            safe_addstr(win, r, cx + 4 + filled, "░" * (bar_len - filled), curses.color_pair(C_DIM))
            safe_addstr(win, r, cx + 4 + bar_len + 1, f"{pct:5.1f}%", curses.color_pair(c))

    return h


def render_memory_panel(win, y: int, x: int, w: int, h: int) -> int:
    """Render memory usage panel. Returns height used."""
    draw_box(win, y, x, h, w, "MEMORY", C_BLUE)

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    inner_x = x + 2
    inner_w = w - 4
    row = y + 1

    # RAM bar
    bar_w = max(10, inner_w - 2)
    extra = f"{human_bytes(mem.used)} / {human_bytes(mem.total)}"
    draw_bar(win, row, inner_x, bar_w, mem.percent, "RAM", extra=extra)
    row += 1

    # RAM details
    details = (
        f"  Active: {human_bytes(mem.active):>8}  "
        f"Inactive: {human_bytes(mem.inactive):>8}  "
        f"Available: {human_bytes(mem.available):>8}"
    )
    safe_addstr(win, row, inner_x, details[:inner_w], curses.color_pair(C_DIM))
    row += 1

    # Swap bar
    if swap.total > 0:
        extra_swap = f"{human_bytes(swap.used)} / {human_bytes(swap.total)}"
        draw_bar(win, row, inner_x, bar_w, swap.percent, "Swap", extra=extra_swap)
    else:
        safe_addstr(win, row, inner_x, "  Swap: not configured", curses.color_pair(C_DIM))
    row += 1

    return h


def render_disk_panel(win, y: int, x: int, w: int, h: int) -> int:
    """Render disk usage panel. Returns height used."""
    draw_box(win, y, x, h, w, "DISK", C_MAGENTA)

    inner_x = x + 2
    inner_w = w - 4
    row = y + 1

    partitions = psutil.disk_partitions(all=False)
    bar_w = max(10, inner_w - 2)

    for part in partitions:
        if row >= y + h - 1:
            break
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue

        # Shorten mount point for display
        mp = part.mountpoint
        if len(mp) > 12:
            mp = "..." + mp[-9:]

        extra = f"{human_bytes(usage.used)} / {human_bytes(usage.total)}"
        draw_bar(win, row, inner_x, bar_w, usage.percent, mp, extra=extra)
        row += 1

    return h


def render_network_panel(win, y: int, x: int, w: int, h: int,
                         net_prev: dict, net_history: dict) -> int:
    """Render network I/O panel. Returns height used."""
    draw_box(win, y, x, h, w, "NETWORK", C_YELLOW)

    inner_x = x + 2
    inner_w = w - 4
    row = y + 1

    # Header
    header = f"  {'Interface':<12} {'▼ Recv/s':>12} {'▲ Sent/s':>12} {'Total Recv':>12} {'Total Sent':>12}"
    safe_addstr(win, row, inner_x, header[:inner_w], curses.color_pair(C_DIM) | curses.A_BOLD)
    row += 1

    # Separator
    safe_addstr(win, row, inner_x, "─" * min(inner_w, 65), curses.color_pair(C_BORDER))
    row += 1

    counters = psutil.net_io_counters(pernic=True)
    now = time.time()

    for iface, stats in sorted(counters.items()):
        if row >= y + h - 1:
            break
        # Skip loopback and inactive
        if iface == "lo0" or iface.startswith("lo"):
            continue
        if stats.bytes_recv == 0 and stats.bytes_sent == 0:
            continue

        recv_rate = 0.0
        sent_rate = 0.0

        if iface in net_prev:
            prev = net_prev[iface]
            dt = now - prev["time"]
            if dt > 0:
                recv_rate = (stats.bytes_recv - prev["recv"]) / dt
                sent_rate = (stats.bytes_sent - prev["sent"]) / dt

        # Sparkline for this interface
        if iface not in net_history:
            net_history[iface] = {"recv": deque(maxlen=30), "sent": deque(maxlen=30)}
        net_history[iface]["recv"].append(recv_rate)
        net_history[iface]["sent"].append(sent_rate)

        iface_short = iface[:12]
        line = (
            f"  {iface_short:<12} "
            f"{'▼ ' + human_rate(recv_rate):>12} "
            f"{'▲ ' + human_rate(sent_rate):>12} "
            f"{human_bytes(stats.bytes_recv):>12} "
            f"{human_bytes(stats.bytes_sent):>12}"
        )
        recv_color = C_GREEN if recv_rate < 1_000_000 else (C_YELLOW if recv_rate < 10_000_000 else C_RED)
        safe_addstr(win, row, inner_x, line[:inner_w], curses.color_pair(recv_color))
        row += 1

        # Mini sparkline for recv rate
        if row < y + h - 1:
            spark_data = list(net_history[iface]["recv"])
            if spark_data:
                hi = max(max(spark_data), 1.0)
                spark = ""
                for val in spark_data[-min(30, inner_w):]:
                    spark += sparkline_char(val, 0, hi)
                safe_addstr(win, row, inner_x + 2, f"  rx: {spark}", curses.color_pair(C_CYAN))
            row += 1

    # Update previous counters
    for iface, stats in counters.items():
        net_prev[iface] = {"recv": stats.bytes_recv, "sent": stats.bytes_sent, "time": now}

    return h


def render_processes_panel(win, y: int, x: int, w: int, h: int) -> int:
    """Render top processes panel. Returns height used."""
    draw_box(win, y, x, h, w, "TOP PROCESSES", C_RED)

    inner_x = x + 2
    inner_w = w - 4
    row = y + 1

    # Header
    header = f"  {'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  {'Name':<30}  {'Status':<8}"
    safe_addstr(win, row, inner_x, header[:inner_w],
                curses.color_pair(C_WHITE_BOLD) | curses.A_BOLD | curses.A_UNDERLINE)
    row += 1

    # Get top processes
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by CPU%, top 10
    procs.sort(key=lambda p: p.get("cpu_percent", 0) or 0, reverse=True)
    top_procs = procs[:min(10, h - 3)]

    for proc in top_procs:
        if row >= y + h - 1:
            break
        pid = proc.get("pid", 0)
        name = (proc.get("name", "???") or "???")[:30]
        cpu_pct = proc.get("cpu_percent", 0.0) or 0.0
        mem_pct = proc.get("memory_percent", 0.0) or 0.0
        status = (proc.get("status", "???") or "???")[:8]

        color = color_for_pct(cpu_pct)
        line = f"  {pid:>7}  {cpu_pct:>6.1f}  {mem_pct:>6.1f}  {name:<30}  {status:<8}"
        safe_addstr(win, row, inner_x, line[:inner_w], curses.color_pair(color))
        row += 1

    return h


def render_status_bar(win, y: int, x: int, w: int, panels_visible: dict):
    """Render the bottom status bar."""
    max_y, max_x = win.getmaxyx()
    if y >= max_y:
        return

    bar = "  "
    keys = [
        ("1:CPU", "cpu"),
        ("2:MEM", "memory"),
        ("3:DISK", "disk"),
        ("4:NET", "network"),
        ("5:PROC", "processes"),
    ]
    for label, key in keys:
        on = panels_visible.get(key, True)
        marker = "●" if on else "○"
        bar += f" {marker} {label} "

    bar += "  │  Q: Quit  │  Refresh: 1s"

    safe_addstr(win, y, x, " " * min(w, max_x - x), curses.color_pair(C_HEADER))
    safe_addstr(win, y, x, bar[:w], curses.color_pair(C_HEADER) | curses.A_BOLD)


# ---------------------------------------------------------------------------
# Layout engine
# ---------------------------------------------------------------------------


def compute_layout(max_y: int, max_x: int, panels_visible: dict) -> dict:
    """Compute panel positions and sizes based on terminal dimensions."""
    layout = {}
    pad = 0

    # Header always at top
    header_h = 4
    layout["header"] = {"y": pad, "x": pad, "w": max_x - pad * 2, "h": header_h}
    current_y = header_h + pad

    available_h = max_y - current_y - 1  # -1 for status bar
    available_w = max_x - pad * 2

    # Count visible panels
    visible = [k for k in ["cpu", "memory", "disk", "network", "processes"] if panels_visible.get(k, True)]
    if not visible:
        layout["status_bar"] = {"y": max_y - 1, "x": 0, "w": max_x}
        return layout

    # Wide layout: CPU + Memory on left, Disk + Network on right, Processes full-width below
    # Narrow layout: everything stacked vertically
    is_wide = available_w >= 80

    if is_wide:
        left_w = available_w // 2
        right_w = available_w - left_w
        right_x = pad + left_w

        # Top row: CPU (left) + Disk (right)
        top_panels = []
        if "cpu" in visible:
            top_panels.append(("cpu", "left"))
        if "memory" in visible:
            top_panels.append(("memory", "left"))
        if "disk" in visible:
            top_panels.append(("disk", "right"))
        if "network" in visible:
            top_panels.append(("network", "right"))

        left_panels = [p for p, side in top_panels if side == "left"]
        right_panels = [p for p, side in top_panels if side == "right"]

        # Calculate heights
        n_cores = psutil.cpu_count(logical=True) or 4
        cpu_h = max(8, 5 + (n_cores + 1) // 2)
        mem_h = 5
        disk_h = min(8, 3 + len(psutil.disk_partitions(all=False)))
        net_h = max(6, min(12, available_h // 3))
        proc_h = max(8, 13)

        # Left column
        ly = current_y
        if "cpu" in visible:
            actual_cpu_h = min(cpu_h, available_h - 2)
            layout["cpu"] = {"y": ly, "x": pad, "w": left_w, "h": actual_cpu_h}
            ly += actual_cpu_h
        if "memory" in visible:
            actual_mem_h = min(mem_h, max(4, available_h - (ly - current_y) - 2))
            layout["memory"] = {"y": ly, "x": pad, "w": left_w, "h": actual_mem_h}
            ly += actual_mem_h

        # Right column
        ry = current_y
        if "disk" in visible:
            actual_disk_h = min(disk_h, available_h - 2)
            layout["disk"] = {"y": ry, "x": right_x, "w": right_w, "h": actual_disk_h}
            ry += actual_disk_h
        if "network" in visible:
            actual_net_h = min(net_h, max(6, available_h - (ry - current_y) - 2))
            layout["network"] = {"y": ry, "x": right_x, "w": right_w, "h": actual_net_h}
            ry += actual_net_h

        # Processes: full width below both columns
        bottom_y = max(ly, ry)
        if "processes" in visible:
            remaining = max(5, max_y - bottom_y - 1)
            layout["processes"] = {"y": bottom_y, "x": pad, "w": available_w, "h": remaining}

    else:
        # Narrow: stack vertically
        cy = current_y
        panel_h = max(5, available_h // len(visible))

        for panel in visible:
            actual_h = min(panel_h, max_y - cy - 1)
            if actual_h < 3:
                break
            layout[panel] = {"y": cy, "x": pad, "w": available_w, "h": actual_h}
            cy += actual_h

    layout["status_bar"] = {"y": max_y - 1, "x": 0, "w": max_x}
    return layout


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------


def main(stdscr):
    # Setup curses
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    # Init colors
    curses.start_color()
    curses.use_default_colors()

    # Define color pairs
    curses.init_pair(C_NORMAL, curses.COLOR_WHITE, -1)
    curses.init_pair(C_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(C_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_RED, curses.COLOR_RED, -1)
    curses.init_pair(C_CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(C_BLUE, curses.COLOR_BLUE, -1)
    curses.init_pair(C_MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_HEADER, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(C_BORDER, curses.COLOR_CYAN, -1)
    curses.init_pair(C_DIM, 245 if curses.COLORS >= 256 else curses.COLOR_WHITE, -1)
    curses.init_pair(C_WHITE_BOLD, curses.COLOR_WHITE, -1)
    curses.init_pair(C_SPARK_LOW, curses.COLOR_GREEN, -1)
    curses.init_pair(C_SPARK_MED, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_SPARK_HIGH, curses.COLOR_RED, -1)
    curses.init_pair(C_TITLE, curses.COLOR_WHITE, -1)
    curses.init_pair(C_BAR_BG, 240 if curses.COLORS >= 256 else curses.COLOR_WHITE, -1)

    # State
    cpu_history: deque = deque(maxlen=CPU_HISTORY_LEN)
    net_prev: dict = {}
    net_history: dict = {}
    panels_visible = {
        "cpu": True,
        "memory": True,
        "disk": True,
        "network": True,
        "processes": True,
    }

    # Initial CPU percent call (first call returns 0)
    psutil.cpu_percent(percpu=True)
    last_update = 0.0

    while True:
        # Handle input
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key in (ord("q"), ord("Q")):
            break
        elif key == ord("1"):
            panels_visible["cpu"] = not panels_visible["cpu"]
        elif key == ord("2"):
            panels_visible["memory"] = not panels_visible["memory"]
        elif key == ord("3"):
            panels_visible["disk"] = not panels_visible["disk"]
        elif key == ord("4"):
            panels_visible["network"] = not panels_visible["network"]
        elif key == ord("5"):
            panels_visible["processes"] = not panels_visible["processes"]

        now = time.time()
        if now - last_update < REFRESH_INTERVAL and key == -1:
            continue
        last_update = now

        # Collect metrics
        per_cpu = psutil.cpu_percent(percpu=True)
        overall_cpu = sum(per_cpu) / len(per_cpu) if per_cpu else 0.0
        cpu_history.append(overall_cpu)

        # Render
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        if max_y < 10 or max_x < 40:
            safe_addstr(stdscr, 0, 0, "Terminal too small! Need at least 40x10.",
                        curses.color_pair(C_RED))
            stdscr.refresh()
            continue

        layout = compute_layout(max_y, max_x, panels_visible)

        # Render header
        if "header" in layout:
            l = layout["header"]
            render_header(stdscr, l["y"], l["x"], l["w"])

        # Render CPU
        if "cpu" in layout and panels_visible.get("cpu"):
            l = layout["cpu"]
            render_cpu_panel(stdscr, l["y"], l["x"], l["w"], l["h"], cpu_history, per_cpu)

        # Render Memory
        if "memory" in layout and panels_visible.get("memory"):
            l = layout["memory"]
            render_memory_panel(stdscr, l["y"], l["x"], l["w"], l["h"])

        # Render Disk
        if "disk" in layout and panels_visible.get("disk"):
            l = layout["disk"]
            render_disk_panel(stdscr, l["y"], l["x"], l["w"], l["h"])

        # Render Network
        if "network" in layout and panels_visible.get("network"):
            l = layout["network"]
            render_network_panel(stdscr, l["y"], l["x"], l["w"], l["h"], net_prev, net_history)

        # Render Processes
        if "processes" in layout and panels_visible.get("processes"):
            l = layout["processes"]
            render_processes_panel(stdscr, l["y"], l["x"], l["w"], l["h"])

        # Status bar
        if "status_bar" in layout:
            l = layout["status_bar"]
            render_status_bar(stdscr, l["y"], l["x"], l["w"], panels_visible)

        stdscr.refresh()


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
