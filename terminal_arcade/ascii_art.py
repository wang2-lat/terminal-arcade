#!/usr/bin/env python3
"""
Terminal Image-to-ASCII Art Converter

Converts images (jpg, png, etc.) to colored ASCII art using true color
(24-bit) ANSI escape codes. Supports multiple character density sets,
adjustable width, color/grayscale modes, URL input, and a built-in demo.

Usage:
    python3 ascii_art.py <image_path>
    python3 ascii_art.py <image_path> --width 120 --charset detailed
    python3 ascii_art.py <image_path> --no-color
    python3 ascii_art.py <image_url>
    python3 ascii_art.py                  # built-in gradient demo
"""

import argparse
import math
import os
import shutil
import sys
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Character density sets — ordered darkest to lightest (for dark backgrounds)
# ---------------------------------------------------------------------------

CHARSETS = {
    "simple":   " .:-=+*#%@",
    "detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "blocks":   " ░▒▓█",
}

ASPECT_RATIO = 0.55  # terminal chars are taller than wide


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------

def brightness(r: int, g: int, b: int) -> float:
    """Perceived luminance (ITU-R BT.601)."""
    return 0.299 * r + 0.587 * g + 0.114 * b


def image_to_ascii(
    img: Image.Image,
    width: int,
    charset: str = "simple",
    color: bool = True,
) -> str:
    """Convert a PIL Image to a string of (optionally colored) ASCII art."""
    chars = CHARSETS[charset]
    num_chars = len(chars)

    # Resize keeping aspect ratio
    orig_w, orig_h = img.size
    new_width = width
    new_height = int((orig_h / orig_w) * new_width * ASPECT_RATIO)
    new_height = max(new_height, 1)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    img = img.convert("RGB")

    pixels = img.load()
    lines: list[str] = []

    for y in range(new_height):
        parts: list[str] = []
        for x in range(new_width):
            r, g, b = pixels[x, y]
            bright = brightness(r, g, b)
            idx = int(bright / 256 * num_chars)
            idx = min(idx, num_chars - 1)
            ch = chars[idx]

            if color and ch != " ":
                # True color (24-bit) ANSI foreground
                parts.append(f"\033[38;2;{r};{g};{b}m{ch}\033[0m")
            else:
                parts.append(ch)

        lines.append("".join(parts))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo image generation
# ---------------------------------------------------------------------------

def generate_demo_image(size: int = 512) -> Image.Image:
    """Generate a colorful gradient/pattern for demo purposes."""
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)

    for y in range(size):
        for x in range(size):
            # Diagonal rainbow gradient with circular highlights
            angle = math.atan2(y - size / 2, x - size / 2)
            dist = math.sqrt((x - size / 2) ** 2 + (y - size / 2) ** 2) / (size / 2)
            dist = min(dist, 1.0)

            hue = (angle / (2 * math.pi) + 0.5) % 1.0
            r, g, b = hsv_to_rgb(hue, 0.7 + 0.3 * (1 - dist), 1.0 - 0.4 * dist)
            img.putpixel((x, y), (int(r * 255), int(g * 255), int(b * 255)))

    # Draw some geometric shapes for variety
    draw.ellipse(
        [size // 4, size // 4, 3 * size // 4, 3 * size // 4],
        outline=(255, 255, 255),
        width=3,
    )
    draw.rectangle(
        [size // 3, size // 3, 2 * size // 3, 2 * size // 3],
        outline=(0, 0, 0),
        width=3,
    )

    return img


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    """Convert HSV (0-1 range) to RGB (0-1 range)."""
    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i %= 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    return v, p, q


# ---------------------------------------------------------------------------
# Image loading helpers
# ---------------------------------------------------------------------------

def load_image_from_path(path: str) -> Image.Image:
    """Load an image from a local file path."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        print(f"Error: File not found: {p}", file=sys.stderr)
        sys.exit(1)
    try:
        return Image.open(p)
    except Exception as e:
        print(f"Error: Cannot open image: {e}", file=sys.stderr)
        sys.exit(1)


def load_image_from_url(url: str) -> Image.Image:
    """Download an image from a URL and return as PIL Image."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ascii-art/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"Error: Cannot download image: {e}", file=sys.stderr)
        sys.exit(1)

    tmp = tempfile.NamedTemporaryFile(suffix=".img", delete=False)
    try:
        tmp.write(data)
        tmp.close()
        return Image.open(tmp.name)
    except Exception as e:
        print(f"Error: Cannot open downloaded image: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def is_url(s: str) -> bool:
    """Check whether a string looks like a URL."""
    return s.startswith(("http://", "https://"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def get_terminal_width() -> int:
    """Return the current terminal width, defaulting to 80."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert images to colored ASCII art in the terminal.",
        epilog="Examples:\n"
               "  ascii_art.py photo.jpg\n"
               "  ascii_art.py photo.png --width 100 --charset blocks\n"
               "  ascii_art.py https://example.com/image.jpg --no-color\n"
               "  ascii_art.py   (runs built-in demo)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help="Path or URL to the image (omit for built-in demo)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Output width in characters (default: terminal width)",
    )
    parser.add_argument(
        "--charset",
        choices=list(CHARSETS.keys()),
        default="simple",
        help="Character density set (default: simple)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color output (grayscale ASCII only)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    width = args.width or get_terminal_width()

    # Load the image
    if args.image is None:
        print("No image provided — generating built-in demo pattern...\n",
              file=sys.stderr)
        img = generate_demo_image()
    elif is_url(args.image):
        print(f"Downloading {args.image} ...", file=sys.stderr)
        img = load_image_from_url(args.image)
    else:
        img = load_image_from_path(args.image)

    # Convert and print
    result = image_to_ascii(
        img,
        width=width,
        charset=args.charset,
        color=not args.no_color,
    )
    print(result)


if __name__ == "__main__":
    main()


def main_entry():
    import curses
    curses.wrapper(main)

