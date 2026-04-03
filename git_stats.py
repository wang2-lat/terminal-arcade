#!/usr/bin/env python3
"""
Git Repository Stats Analyzer
Scans git repos under ~/ and generates a self-contained HTML report
with SVG charts, heatmaps, and per-repo stats cards.
"""

import subprocess
import os
import sys
import math
import webbrowser
import html
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOME = Path.home()
SCAN_ROOT = HOME
MAX_DEPTH = 2
OUTPUT_HTML = HOME / "fun-projects" / "git_report.html"

# File extension -> language mapping
EXT_LANG = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TSX",
    ".jsx": "JSX", ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".json": "JSON", ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".rs": "Rust", ".go": "Go", ".java": "Java", ".kt": "Kotlin",
    ".c": "C", ".h": "C/C++ Header", ".cpp": "C++", ".cc": "C++",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".sql": "SQL", ".graphql": "GraphQL", ".proto": "Protobuf",
    ".toml": "TOML", ".ini": "INI", ".cfg": "Config",
    ".xml": "XML", ".svg": "SVG", ".lua": "Lua",
    ".r": "R", ".R": "R", ".m": "Objective-C",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
    ".tf": "Terraform", ".dockerfile": "Docker",
}

# Colors for languages (top ones get distinct colors)
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "TSX": "#3178c6", "JSX": "#f1e05a", "HTML": "#e34c26", "CSS": "#563d7c",
    "SCSS": "#c6538c", "JSON": "#292929", "Markdown": "#083fa1",
    "Shell": "#89e051", "Rust": "#dea584", "Go": "#00ADD8",
    "Java": "#b07219", "Kotlin": "#A97BFF", "C": "#555555",
    "C++": "#f34b7d", "C/C++ Header": "#555555", "Ruby": "#701516",
    "PHP": "#4F5D95", "Swift": "#F05138", "SQL": "#e38c00",
    "YAML": "#cb171e", "TOML": "#9c4221", "Vue": "#41b883",
    "Svelte": "#ff3e00", "Astro": "#ff5a03", "Lua": "#000080",
    "R": "#198CE7", "Objective-C": "#438eff", "Docker": "#384d54",
    "Terraform": "#7B42BC", "GraphQL": "#e10098", "Protobuf": "#6a9fb5",
    "Config": "#888888", "INI": "#888888", "XML": "#0060ac", "SVG": "#ff9900",
}

FALLBACK_COLORS = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4",
    "#469990", "#dcbeff", "#9A6324", "#800000", "#aaffc3",
]


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def run_git(repo_path: str, args: list[str], timeout: int = 30) -> str:
    """Run a git command in the given repo and return stdout."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, Exception):
        return ""


def find_repos(root: Path, max_depth: int = 2) -> list[Path]:
    """Find git repositories under root up to max_depth levels."""
    repos = []
    try:
        result = subprocess.run(
            ["find", str(root), "-maxdepth", str(max_depth),
             "-name", ".git", "-type", "d"],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line:
                repos.append(Path(line).parent)
    except Exception:
        pass
    return sorted(repos, key=lambda p: p.name.lower())


def collect_repo_stats(repo_path: Path) -> dict | None:
    """Collect all stats for a single repository."""
    rp = str(repo_path)

    # Quick check: is it actually a git repo?
    check = run_git(rp, ["rev-parse", "--git-dir"], timeout=5)
    if not check:
        return None

    name = repo_path.name
    stats: dict = {"name": name, "path": rp}

    # --- Commit log (author, date, timestamp) ---
    # Format: author_name|ISO-date|unix-timestamp
    log_raw = run_git(rp, [
        "log", "--all", "--format=%aN|%aI|%at", "--no-merges"
    ], timeout=60)

    commits = []
    authors: Counter = Counter()
    day_counts: Counter = Counter()      # YYYY-MM-DD -> count
    hour_counts: Counter = Counter()     # 0-23 -> count
    weekday_counts: Counter = Counter()  # 0=Mon..6=Sun -> count

    if log_raw:
        for line in log_raw.split("\n"):
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            author, iso_date, ts_str = parts
            authors[author] += 1
            try:
                ts = int(ts_str)
                dt = datetime.fromtimestamp(ts)
                day_str = dt.strftime("%Y-%m-%d")
                day_counts[day_str] += 1
                hour_counts[dt.hour] += 1
                weekday_counts[dt.weekday()] += 1
                commits.append({"author": author, "date": day_str, "ts": ts, "dt": dt})
            except (ValueError, OSError):
                continue

    total_commits = len(commits)
    if total_commits == 0:
        return None

    stats["total_commits"] = total_commits
    stats["authors"] = authors.most_common(10)
    stats["day_counts"] = dict(day_counts)
    stats["hour_counts"] = dict(hour_counts)
    stats["weekday_counts"] = dict(weekday_counts)

    # First / last commit
    timestamps = [c["ts"] for c in commits]
    stats["first_commit"] = datetime.fromtimestamp(min(timestamps)).strftime("%Y-%m-%d")
    stats["last_commit"] = datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d")

    # --- Languages by file extension (tracked files) ---
    files_raw = run_git(rp, ["ls-files"], timeout=15)
    lang_counts: Counter = Counter()
    total_files = 0
    if files_raw:
        for f in files_raw.split("\n"):
            f = f.strip()
            if not f:
                continue
            total_files += 1
            ext = os.path.splitext(f)[1].lower()
            lang = EXT_LANG.get(ext)
            if lang:
                lang_counts[lang] += 1
    stats["languages"] = lang_counts.most_common(15)
    stats["total_files"] = total_files

    # --- Lines of code (fast: git ls-files piped to wc) ---
    try:
        result = subprocess.run(
            f'git -C "{rp}" ls-files | head -500 | xargs -I{{}} wc -l "{rp}/{{}}" 2>/dev/null | tail -1',
            shell=True, capture_output=True, text=True, timeout=30
        )
        loc_line = result.stdout.strip()
        if loc_line:
            parts = loc_line.split()
            stats["loc"] = int(parts[0]) if parts and parts[0].isdigit() else 0
        else:
            stats["loc"] = 0
    except Exception:
        stats["loc"] = 0

    return stats


# ---------------------------------------------------------------------------
# SVG Chart generators
# ---------------------------------------------------------------------------

def svg_heatmap(all_day_counts: dict[str, int], width: int = 900) -> str:
    """GitHub-style commit heatmap for the last 365 days."""
    today = datetime.now().date()
    start = today - timedelta(days=364)

    # Find the Sunday on or before start
    start_weekday = start.weekday()  # Mon=0 .. Sun=6
    # We want weeks starting on Sunday: adjust
    days_to_sunday = (start_weekday + 1) % 7
    grid_start = start - timedelta(days=days_to_sunday)

    # Collect values
    max_val = max(all_day_counts.values()) if all_day_counts else 1
    if max_val == 0:
        max_val = 1

    cell = 14
    gap = 3
    cols = 53
    rows = 7
    left_margin = 40
    top_margin = 30
    svg_w = left_margin + cols * (cell + gap) + 10
    svg_h = top_margin + rows * (cell + gap) + 30

    # Color scale (5 levels)
    levels = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

    def get_color(count: int) -> str:
        if count == 0:
            return levels[0]
        ratio = count / max_val
        if ratio < 0.25:
            return levels[1]
        elif ratio < 0.5:
            return levels[2]
        elif ratio < 0.75:
            return levels[3]
        return levels[4]

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
             f'viewBox="0 0 {svg_w} {svg_h}" style="max-width:100%;">']

    # Day labels
    day_labels = ["Mon", "", "Wed", "", "Fri", "", "Sun"]
    for i, label in enumerate(day_labels):
        if label:
            y = top_margin + i * (cell + gap) + cell - 2
            parts.append(f'<text x="{left_margin - 8}" y="{y}" fill="#8b949e" '
                         f'font-size="11" text-anchor="end" font-family="system-ui,sans-serif">{label}</text>')

    # Month labels
    month_positions = {}
    for col in range(cols):
        day = grid_start + timedelta(days=col * 7)
        if day.day <= 7:
            month_name = day.strftime("%b")
            if month_name not in month_positions:
                month_positions[month_name] = left_margin + col * (cell + gap)

    for month_name, x_pos in month_positions.items():
        parts.append(f'<text x="{x_pos}" y="{top_margin - 8}" fill="#8b949e" '
                     f'font-size="11" font-family="system-ui,sans-serif">{month_name}</text>')

    # Cells
    for col in range(cols):
        for row in range(rows):
            day = grid_start + timedelta(days=col * 7 + row)
            if day > today or day < start:
                continue
            day_str = day.strftime("%Y-%m-%d")
            count = all_day_counts.get(day_str, 0)
            color = get_color(count)
            x = left_margin + col * (cell + gap)
            y = top_margin + row * (cell + gap)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                f'rx="3" ry="3" fill="{color}">'
                f'<title>{day_str}: {count} commit{"s" if count != 1 else ""}</title>'
                f'</rect>'
            )

    # Legend
    legend_x = svg_w - 200
    legend_y = svg_h - 15
    parts.append(f'<text x="{legend_x - 40}" y="{legend_y + 10}" fill="#8b949e" '
                 f'font-size="11" font-family="system-ui,sans-serif">Less</text>')
    for i, c in enumerate(levels):
        parts.append(f'<rect x="{legend_x + i * (cell + 3)}" y="{legend_y}" '
                     f'width="{cell}" height="{cell}" rx="3" fill="{c}"/>')
    parts.append(f'<text x="{legend_x + 5 * (cell + 3) + 5}" y="{legend_y + 10}" fill="#8b949e" '
                 f'font-size="11" font-family="system-ui,sans-serif">More</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def svg_pie_chart(lang_data: list[tuple[str, int]], size: int = 300) -> str:
    """Inline SVG pie chart for language breakdown."""
    if not lang_data:
        return '<p style="color:#8b949e;">No language data</p>'

    total = sum(c for _, c in lang_data)
    if total == 0:
        return '<p style="color:#8b949e;">No language data</p>'

    cx, cy, r = size // 2, size // 2, size // 2 - 20
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size + 30}" '
             f'viewBox="0 0 {size} {size + 30}" style="max-width:100%;">']

    color_idx = 0
    start_angle = -90  # Start from top

    for lang, count in lang_data:
        pct = count / total
        angle = pct * 360

        color = LANG_COLORS.get(lang)
        if not color:
            color = FALLBACK_COLORS[color_idx % len(FALLBACK_COLORS)]
            color_idx += 1

        if pct >= 0.999:
            # Full circle
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}">'
                         f'<title>{lang}: {count} files ({pct:.0%})</title></circle>')
            continue

        # Arc path
        start_rad = math.radians(start_angle)
        end_rad = math.radians(start_angle + angle)

        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)

        large_arc = 1 if angle > 180 else 0

        path = (f'M {cx},{cy} L {x1:.2f},{y1:.2f} '
                f'A {r},{r} 0 {large_arc} 1 {x2:.2f},{y2:.2f} Z')

        parts.append(f'<path d="{path}" fill="{color}" stroke="#0d1117" stroke-width="1">'
                     f'<title>{lang}: {count} files ({pct:.0%})</title></path>')

        start_angle += angle

    parts.append('</svg>')
    return "\n".join(parts)


def svg_pie_legend(lang_data: list[tuple[str, int]]) -> str:
    """HTML legend for the pie chart."""
    if not lang_data:
        return ""
    total = sum(c for _, c in lang_data)
    if total == 0:
        return ""

    rows = []
    color_idx = 0
    for lang, count in lang_data:
        pct = count / total * 100
        color = LANG_COLORS.get(lang)
        if not color:
            color = FALLBACK_COLORS[color_idx % len(FALLBACK_COLORS)]
            color_idx += 1
        rows.append(
            f'<div style="display:flex;align-items:center;gap:8px;padding:3px 0;">'
            f'<span style="width:12px;height:12px;border-radius:3px;background:{color};flex-shrink:0;"></span>'
            f'<span style="color:#e6edf3;font-size:13px;">{html.escape(lang)}</span>'
            f'<span style="color:#8b949e;font-size:12px;margin-left:auto;">{pct:.1f}%</span>'
            f'</div>'
        )
    return "\n".join(rows)


def svg_bar_chart(data: list[tuple[str, int]], width: int = 700, height: int = 350,
                  bar_color: str = "#39d353", label: str = "commits") -> str:
    """Horizontal bar chart as inline SVG."""
    if not data:
        return '<p style="color:#8b949e;">No data</p>'

    max_val = max(v for _, v in data) if data else 1
    if max_val == 0:
        max_val = 1

    left_margin = 160
    right_margin = 80
    top_margin = 10
    bar_height = 28
    bar_gap = 6
    chart_height = top_margin + len(data) * (bar_height + bar_gap) + 10
    bar_area_w = width - left_margin - right_margin

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{chart_height}" '
             f'viewBox="0 0 {width} {chart_height}" style="max-width:100%;">']

    for i, (name, val) in enumerate(data):
        y = top_margin + i * (bar_height + bar_gap)
        bar_w = max(2, (val / max_val) * bar_area_w)

        # Label
        display_name = name if len(name) <= 22 else name[:20] + ".."
        parts.append(
            f'<text x="{left_margin - 10}" y="{y + bar_height // 2 + 5}" '
            f'fill="#e6edf3" font-size="13" text-anchor="end" '
            f'font-family="system-ui,sans-serif">{html.escape(display_name)}</text>'
        )

        # Bar
        parts.append(
            f'<rect x="{left_margin}" y="{y}" width="{bar_w:.1f}" height="{bar_height}" '
            f'rx="4" fill="{bar_color}" opacity="0.85">'
            f'<title>{html.escape(name)}: {val} {label}</title></rect>'
        )

        # Value
        parts.append(
            f'<text x="{left_margin + bar_w + 8}" y="{y + bar_height // 2 + 5}" '
            f'fill="#8b949e" font-size="12" font-family="system-ui,sans-serif">{val:,}</text>'
        )

    parts.append('</svg>')
    return "\n".join(parts)


def svg_hour_histogram(hour_counts: dict[int, int], width: int = 700, height: int = 200) -> str:
    """Vertical bar chart showing commits by hour of day."""
    if not hour_counts:
        return '<p style="color:#8b949e;">No data</p>'

    max_val = max(hour_counts.values()) if hour_counts else 1
    if max_val == 0:
        max_val = 1

    left_margin = 40
    bottom_margin = 35
    top_margin = 15
    chart_w = width - left_margin - 20
    chart_h = height - bottom_margin - top_margin
    bar_w = chart_w / 24 - 4

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" style="max-width:100%;">']

    # Y axis line
    parts.append(f'<line x1="{left_margin}" y1="{top_margin}" '
                 f'x2="{left_margin}" y2="{top_margin + chart_h}" '
                 f'stroke="#30363d" stroke-width="1"/>')

    # X axis line
    parts.append(f'<line x1="{left_margin}" y1="{top_margin + chart_h}" '
                 f'x2="{width - 20}" y2="{top_margin + chart_h}" '
                 f'stroke="#30363d" stroke-width="1"/>')

    for h in range(24):
        val = hour_counts.get(h, 0)
        bar_h = max(1, (val / max_val) * chart_h)
        x = left_margin + h * (chart_w / 24) + 2
        y = top_margin + chart_h - bar_h

        # Gradient from dim to bright based on value
        intensity = val / max_val if max_val > 0 else 0
        if intensity < 0.25:
            color = "#0e4429"
        elif intensity < 0.5:
            color = "#006d32"
        elif intensity < 0.75:
            color = "#26a641"
        else:
            color = "#39d353"

        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'rx="2" fill="{color}" opacity="0.9">'
            f'<title>{h:02d}:00 - {val} commits</title></rect>'
        )

        # Hour label (every 3 hours)
        if h % 3 == 0:
            parts.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{top_margin + chart_h + 18}" '
                f'fill="#8b949e" font-size="11" text-anchor="middle" '
                f'font-family="system-ui,sans-serif">{h:02d}</text>'
            )

    parts.append('</svg>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# HTML report generation
# ---------------------------------------------------------------------------

def generate_html(repos_stats: list[dict]) -> str:
    """Generate the full self-contained HTML report."""

    # Aggregate stats
    total_commits = sum(r["total_commits"] for r in repos_stats)
    total_repos = len(repos_stats)
    total_files = sum(r["total_files"] for r in repos_stats)
    total_loc = sum(r["loc"] for r in repos_stats)

    # Aggregate all authors
    all_authors: Counter = Counter()
    for r in repos_stats:
        for author, count in r["authors"]:
            all_authors[author] += count

    # Aggregate day counts
    all_day_counts: Counter = Counter()
    for r in repos_stats:
        for day, count in r["day_counts"].items():
            all_day_counts[day] += count

    # Aggregate hour counts
    all_hour_counts: Counter = Counter()
    for r in repos_stats:
        for hour, count in r["hour_counts"].items():
            all_hour_counts[hour] += count

    # Aggregate languages
    all_langs: Counter = Counter()
    for r in repos_stats:
        for lang, count in r["languages"]:
            all_langs[lang] += count

    # Top repos by commits
    top_repos = sorted(repos_stats, key=lambda x: x["total_commits"], reverse=True)[:10]
    top_repos_data = [(r["name"], r["total_commits"]) for r in top_repos]

    # Earliest and latest dates
    all_first = min(r["first_commit"] for r in repos_stats)
    all_last = max(r["last_commit"] for r in repos_stats)

    # Streak calculation
    today_str = datetime.now().strftime("%Y-%m-%d")
    streak = 0
    d = datetime.now().date()
    while all_day_counts.get(d.strftime("%Y-%m-%d"), 0) > 0:
        streak += 1
        d -= timedelta(days=1)

    # Active days
    active_days = len(all_day_counts)

    # Build charts
    heatmap_svg = svg_heatmap(dict(all_day_counts))
    pie_svg = svg_pie_chart(all_langs.most_common(12))
    pie_legend = svg_pie_legend(all_langs.most_common(12))
    bar_svg = svg_bar_chart(top_repos_data)
    hour_svg = svg_hour_histogram(dict(all_hour_counts))

    # Build per-repo cards
    repo_cards = []
    for r in sorted(repos_stats, key=lambda x: x["total_commits"], reverse=True):
        top_lang = r["languages"][0][0] if r["languages"] else "N/A"
        top_lang_color = LANG_COLORS.get(top_lang, "#8b949e")
        top_author = r["authors"][0][0] if r["authors"] else "N/A"

        card = f'''
        <div class="repo-card">
            <div class="repo-name">{html.escape(r["name"])}</div>
            <div class="repo-path">{html.escape(r["path"])}</div>
            <div class="repo-meta">
                <div class="meta-item">
                    <span class="meta-label">Commits</span>
                    <span class="meta-value">{r["total_commits"]:,}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Files</span>
                    <span class="meta-value">{r["total_files"]:,}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Top Author</span>
                    <span class="meta-value" title="{html.escape(top_author)}">{html.escape(top_author[:18])}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Primary Lang</span>
                    <span class="meta-value">
                        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{top_lang_color};margin-right:5px;vertical-align:middle;"></span>
                        {html.escape(top_lang)}
                    </span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Active</span>
                    <span class="meta-value">{html.escape(r["first_commit"])} &mdash; {html.escape(r["last_commit"])}</span>
                </div>
            </div>
        </div>'''
        repo_cards.append(card)

    # Top authors section
    top_authors_html = ""
    for i, (author, count) in enumerate(all_authors.most_common(10)):
        pct = count / total_commits * 100
        bar_w = pct
        top_authors_html += f'''
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid #21262d;">
            <span style="color:#8b949e;font-size:13px;width:24px;text-align:right;">{i+1}.</span>
            <span style="color:#e6edf3;font-size:14px;min-width:150px;">{html.escape(author)}</span>
            <div style="flex:1;background:#161b22;border-radius:4px;height:20px;overflow:hidden;">
                <div style="background:#238636;height:100%;width:{bar_w:.1f}%;border-radius:4px;min-width:2px;"></div>
            </div>
            <span style="color:#8b949e;font-size:13px;min-width:80px;text-align:right;">{count:,} ({pct:.1f}%)</span>
        </div>'''

    # Weekday distribution
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    all_weekday_counts: Counter = Counter()
    for r in repos_stats:
        for wd, count in r["weekday_counts"].items():
            all_weekday_counts[wd] += count

    max_wd = max(all_weekday_counts.values()) if all_weekday_counts else 1
    weekday_bars = ""
    for i in range(7):
        val = all_weekday_counts.get(i, 0)
        h = max(4, (val / max_wd) * 120) if max_wd > 0 else 4
        weekday_bars += f'''
        <div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
            <div style="background:#238636;width:36px;height:{h:.0f}px;border-radius:4px;opacity:0.85;" title="{val} commits"></div>
            <span style="color:#8b949e;font-size:12px;">{weekday_names[i]}</span>
            <span style="color:#58a6ff;font-size:11px;">{val:,}</span>
        </div>'''

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Git Stats Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
    line-height: 1.6;
    padding: 24px;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #58a6ff, #39d353);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 4px;
  }}
  .subtitle {{ color: #8b949e; font-size: 14px; margin-bottom: 32px; }}
  .summary-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 36px;
  }}
  .summary-card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: border-color 0.2s;
  }}
  .summary-card:hover {{ border-color: #58a6ff; }}
  .summary-number {{
    font-size: 36px;
    font-weight: 700;
    color: #58a6ff;
    line-height: 1.2;
  }}
  .summary-label {{ color: #8b949e; font-size: 13px; margin-top: 4px; }}
  .section {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
  }}
  .section-title {{
    font-size: 20px;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .section-title::before {{
    content: '';
    width: 4px;
    height: 24px;
    background: linear-gradient(180deg, #58a6ff, #39d353);
    border-radius: 2px;
    display: inline-block;
  }}
  .lang-grid {{
    display: flex;
    gap: 32px;
    align-items: flex-start;
    flex-wrap: wrap;
  }}
  .lang-legend {{
    flex: 1;
    min-width: 200px;
  }}
  .repo-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 16px;
  }}
  .repo-card {{
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 18px;
    transition: border-color 0.2s, transform 0.15s;
  }}
  .repo-card:hover {{
    border-color: #58a6ff;
    transform: translateY(-2px);
  }}
  .repo-name {{
    font-size: 16px;
    font-weight: 600;
    color: #58a6ff;
    margin-bottom: 4px;
  }}
  .repo-path {{
    font-size: 11px;
    color: #484f58;
    margin-bottom: 12px;
    word-break: break-all;
  }}
  .repo-meta {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }}
  .meta-item {{
    display: flex;
    flex-direction: column;
  }}
  .meta-label {{ font-size: 11px; color: #8b949e; }}
  .meta-value {{ font-size: 14px; color: #e6edf3; font-weight: 500; }}
  .meta-item:last-child {{
    grid-column: 1 / -1;
  }}
  .footer {{
    text-align: center;
    color: #484f58;
    font-size: 12px;
    margin-top: 36px;
    padding: 16px 0;
    border-top: 1px solid #21262d;
  }}
  .weekday-grid {{
    display: flex;
    gap: 12px;
    justify-content: center;
    align-items: flex-end;
    padding: 20px 0;
  }}
  @media (max-width: 768px) {{
    body {{ padding: 12px; }}
    .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .repo-grid {{ grid-template-columns: 1fr; }}
    .lang-grid {{ flex-direction: column; }}
  }}
</style>
</head>
<body>
<div class="container">

  <h1>Git Repository Stats</h1>
  <p class="subtitle">Scanned {total_repos} repositories under ~/  &middot;  Generated {now_str}</p>

  <!-- Summary Cards -->
  <div class="summary-grid">
    <div class="summary-card">
      <div class="summary-number">{total_repos}</div>
      <div class="summary-label">Repositories</div>
    </div>
    <div class="summary-card">
      <div class="summary-number">{total_commits:,}</div>
      <div class="summary-label">Total Commits</div>
    </div>
    <div class="summary-card">
      <div class="summary-number">{total_files:,}</div>
      <div class="summary-label">Tracked Files</div>
    </div>
    <div class="summary-card">
      <div class="summary-number">{total_loc:,}</div>
      <div class="summary-label">Lines of Code</div>
    </div>
    <div class="summary-card">
      <div class="summary-number">{active_days:,}</div>
      <div class="summary-label">Active Days</div>
    </div>
    <div class="summary-card">
      <div class="summary-number">{streak}</div>
      <div class="summary-label">Current Streak</div>
    </div>
  </div>

  <!-- Commit Heatmap -->
  <div class="section">
    <div class="section-title">Commit Activity (Last 365 Days)</div>
    <div style="overflow-x:auto;">
      {heatmap_svg}
    </div>
  </div>

  <!-- Language Breakdown + Hour Histogram side by side -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px;">
    <div class="section" style="margin-bottom:0;">
      <div class="section-title">Language Breakdown</div>
      <div class="lang-grid">
        <div>{pie_svg}</div>
        <div class="lang-legend">{pie_legend}</div>
      </div>
    </div>
    <div class="section" style="margin-bottom:0;">
      <div class="section-title">Commit Time Distribution</div>
      <div style="overflow-x:auto;">
        {hour_svg}
      </div>
      <div style="margin-top:16px;">
        <div class="section-title" style="font-size:16px;">Day of Week</div>
        <div class="weekday-grid">
          {weekday_bars}
        </div>
      </div>
    </div>
  </div>

  <!-- Top Repos Bar Chart -->
  <div class="section">
    <div class="section-title">Top 10 Most Active Repositories</div>
    <div style="overflow-x:auto;">
      {bar_svg}
    </div>
  </div>

  <!-- Top Authors -->
  <div class="section">
    <div class="section-title">Top Contributors</div>
    {top_authors_html}
  </div>

  <!-- Per-Repo Cards -->
  <div class="section">
    <div class="section-title">All Repositories ({total_repos})</div>
    <div class="repo-grid">
      {"".join(repo_cards)}
    </div>
  </div>

  <div class="footer">
    Git Stats Analyzer &middot; {all_first} to {all_last} &middot; {total_commits:,} commits across {total_repos} repos
  </div>

</div>
</body>
</html>'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("🔍 Scanning for git repositories...")
    repos = find_repos(SCAN_ROOT, MAX_DEPTH)
    print(f"   Found {len(repos)} repositories\n")

    if not repos:
        print("No git repos found. Exiting.")
        sys.exit(1)

    # Collect stats in parallel
    print("📊 Collecting stats...")
    all_stats = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(collect_repo_stats, r): r for r in repos}
        for future in as_completed(futures):
            repo = futures[future]
            try:
                stats = future.result()
                if stats:
                    all_stats.append(stats)
                    print(f"   ✓ {stats['name']} ({stats['total_commits']} commits)")
            except Exception as e:
                print(f"   ✗ {repo.name}: {e}")

    if not all_stats:
        print("No repos with commits found. Exiting.")
        sys.exit(1)

    print(f"\n📝 Generating report for {len(all_stats)} repositories...")
    html_content = generate_html(all_stats)

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html_content, encoding="utf-8")
    print(f"   Report saved to {OUTPUT_HTML}")

    # Auto-open in browser
    webbrowser.open(f"file://{OUTPUT_HTML}")
    print("   Opened in browser ✨")


if __name__ == "__main__":
    main()
