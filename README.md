# Terminal Arcade 🕹️

**18 stunning terminal applications** — games, visualizations, and tools, all in pure Python with zero external dependencies (except Pillow for ASCII art).

```
pip install terminal-arcade
```

Every app runs entirely in your terminal using `curses`. No GUI, no browser, just beautiful ASCII.

## Games 🎮

| App | Command | Description |
|-----|---------|-------------|
| **Snake** | `snake` | Classic snake with speed progression and colorful rendering |
| **Tetris** | `tetris` | Full Tetris with ghost pieces, hold, next preview, line clear animations |
| **Space Shooter** | `space-shooter` | Arcade shooter with combos, power-ups, and boss battles |
| **Blackjack** | `blackjack` | 21-point card game with ASCII cards and chip betting system |
| **Typing Test** | `typing-test` | WPM speed test with accuracy tracking and persistent leaderboard |
| **2048** | `game2048` | Classic number-merging puzzle with colorful tiles and high score tracking |
| **Minesweeper** | `minesweeper` | Full minesweeper with 3 difficulties, flagging, and chord reveal |
| **Cat Pet** | `catpet` | Adorable ASCII cat desktop pet — feed, pet, and play with yarn! |

## Visualizations 🌈

| App | Command | Description |
|-----|---------|-------------|
| **Matrix Rain** | `matrix` | Movie-accurate digital rain with katakana and multi-color modes |
| **Spinning Globe** | `globe` | Rotating 3D ASCII Earth with continents and ocean shading |
| **Fluid Sim** | `fluid` | Real-time fluid dynamics — water, fire, smoke, and rainbow modes |
| **Particles** | `particles` | Particle effects engine — fire, fireworks, rain, snow, matrix, galaxy |
| **Music Visualizer** | `music-viz` | Audio spectrum animation with bars, mirror, wave, and circle modes |
| **Game of Life** | `life` | Conway's Game of Life with presets, age coloring, and speed control |

## Tools 🛠️

| App | Command | Description |
|-----|---------|-------------|
| **ASCII Art** | `ascii-art <image>` | Convert images to colored ASCII art with multiple charsets |
| **Maze Solver** | `maze` | Random maze generation with animated A* pathfinding visualization |
| **Calculator** | `calculator` | Scientific calculator with function graphing (`plot sin(x)`) |
| **Git Stats** | `git-stats` | Analyze all local repos, generate HTML report with heatmaps and charts |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/wang2-lat/terminal-arcade.git
cd terminal-arcade

# Run any game directly
python3 snake.py
python3 tetris.py
python3 matrix.py

# Or install the commands globally (macOS)
# Each .py file has a corresponding launcher in /opt/homebrew/bin/
```

## Requirements

- Python 3.8+
- `curses` (built-in on macOS/Linux)
- `Pillow` (only for ascii_art.py)

## Screenshots

Fire up your terminal and try them! Each app has built-in controls — press `q` to quit, and check the status bar for all keybindings.

```
🐍 snake        — Arrow keys to move, eat food, grow longer
🎮 tetris       — Arrows + Space for hard drop, H for hold
🚀 space-shooter — WASD/Arrows + Space to fire
🎴 blackjack    — H:Hit S:Stand D:Double
⚡ typing-test  — Just type! Track your WPM improvement
🌧️  matrix       — Q:Quit C:Color mode toggle
🌍 globe        — +/-:Speed C:Color toggle
🌊 fluid        — M:Mode A:Auto-source R:Reset
🐉 particles    — M:Mode SPACE:Manual firework
🎵 music-viz    — V:Visualization C:Color B:BPM
🔮 life         — SPACE:Pause R:Random P:Preset +/-:Speed
🏰 maze         — ENTER:Generate and solve
🧮 calculator   — Type math, `plot sin(x)` for graphs
📊 git-stats    — Generates HTML report automatically
🎨 ascii-art    — `python3 ascii_art.py photo.jpg`
🎮 game2048     — Arrow keys to slide and merge tiles
🎯 minesweeper  — Arrows + Enter:Reveal F:Flag C:Chord
🐱 catpet       — P:Pet F:Feed Y:Yarn SPACE:Jump
```

## License

MIT — do whatever you want with it.

---

*Built for fun in a single session by Claude + a human who said "go wild for 5 hours"* 🤖
