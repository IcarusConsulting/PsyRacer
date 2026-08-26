# PsyRacer V1.0

**by Diamond Hand Dev** (DiamondHand.Dev)

![PsyRacer cover](Assets/PsyRacerSplash.jpg)

A colorful terminal arcade racer. Drive a pseudo-3D highway, dodge traffic, and reach the finish line. The race view is a large playfield with a rear-view mirror on the right that shows cars and roadside objects as you pass them.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Version](https://img.shields.io/badge/version-1.0-purple)
![Platform](https://img.shields.io/badge/platform-Windows-blue)

## Features

- Pseudo-3D highway with curves, trees, and buildings
- Five AI Indy cars on the grid with you
- Starting lights: red, red, red, then green (3, 2, 1, GO!)
- Checkered finish line with a crowd
- Easy 10,000 m / Medium 20,000 m / Hard 30,000 m
- High scores
- Color-cycling menus and a splash with a looping cyberpunk skyline
- Maximized pygame window, with optional exclusive fullscreen
- Background music with on/off in the menu

## Requirements

- [Python 3.10](https://www.python.org/downloads/) or newer
- Windows
- [pygame](https://www.pygame.org/) (`pip install pygame`)

> Built and tested on **Windows**. The game opens a maximized pygame window. Music still uses the Windows MCI APIs.

## How to play

Clone the repo and keep the `Assets` folder next to `racer.py`.

```bash
git clone https://github.com/IcarusConsulting/PsyRacer.git
cd PsyRacer
```

On Windows, start it with:

```powershell
pip install pygame
python racer.py
```

If `python` is not found, try `py racer.py`.

## Controls

The splash screen shows a looping cyberpunk skyline. Press **Enter** to reach the main menu.

On menus, move with the arrow keys and confirm with Enter. Number keys still work as shortcuts.

| Action | Key |
| --- | --- |
| Leave splash / confirm | `Enter` |
| Move menu highlight | `Up` / `Down` |
| Select highlighted item | `Enter` |
| Jump to a menu item | `1`–`5` |
| Toggle fullscreen | `F11` or menu **Display** |
| Accelerate | `W` or `Up` |
| Brake | `S` or `Down` |
| Steer | `A` / `D` or `Left` / `Right` |
| Return to menu | `Esc` or `Q` |

### Game modes

1. **Start Race** — pick Easy, Medium, or Hard, then take the grid.
2. **High Scores** — top placing board with 3-letter initials.
3. **Music: On/Off** — pause or resume the background track.
4. **Display: Windowed/Fullscreen** — start maximized windowed; switch to exclusive fullscreen.
5. **Exit**

Stay on the asphalt. Hitting another car cuts both of you to half of max speed. Lights go red-red-red-green, then you race five AI cars to a packed finish line.

A top-10 placing makes the board. Enter up to three initials like an old arcade: type A–Z, cycle with Up/Down, move with Left/Right, then Enter. Records rank by place, then distance.

## Project layout

```text
PsyRacer/
├── racer.py
├── README.md
├── .gitignore
├── Assets/
│   ├── Background Music.mp3
│   ├── PsyRacerSplash.jpg
│   ├── PsyRacerSplash.mp4
│   └── sprites/                # cars, skyline, trees, clouds
└── racer_scores.txt            # created locally after a race
```

You can replace `Assets/Background Music.mp3` with another MP3 of the same name.

## Troubleshooting

- **Nothing happens when you press keys** — click the game window so it is focused.
- **pygame not found** — run `pip install pygame` in the same Python you use to launch the game.
- **No music** — confirm `Assets/Background Music.mp3` is in the project folder and that system volume is not muted.
- **`python` not found** — install Python 3, enable **Add python.exe to PATH**, and reopen the terminal.

## GitHub social preview

`Assets/PsyRacerSplash.jpg` is the game cover. Set it as the social preview so Discord, X, Slack, and GitHub show this art when the link is shared:

1. Open the repo on GitHub
2. **Settings → General → Social preview**
3. Upload `Assets/PsyRacerSplash.jpg`

## Credits

- **Game** — Diamond Hand Dev (DiamondHand.Dev)
- **Title** — PsyRacer V1.0
- **Engine** — Python 3 and pygame
- **Music** — `Assets/Background Music.mp3`
- **Cover** — `Assets/PsyRacerSplash.jpg`

Made with a grid, a finish line, and too many colors.

---

© Diamond Hand Dev. All rights reserved.
