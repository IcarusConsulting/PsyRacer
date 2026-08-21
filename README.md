# PsyRacer V1.0

**by Diamond Hand Dev** (DiamondHand.Dev)

![PsyRacer cover](Assets/PsyRacerSplash.jpg)

A colorful terminal arcade racer. Drive a pseudo-3D highway, dodge traffic, and reach the finish line.

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
- Color-cycling menus and splash screen
- Background music (`Assets/Background Music.mp3`) with on/off in the menu

## Requirements

- [Python 3.10](https://www.python.org/downloads/) or newer
- Windows (keyboard, color, and console handling match PsyPong)
- A color-capable terminal such as Windows Terminal
- No extra pip packages

## How to play

```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\PsyRacer V1.0"
python racer.py
```

If `python` is not found, try `py racer.py`. Click the terminal so it has focus.

## Controls

| Action | Key |
| --- | --- |
| Leave splash / confirm | `Enter` |
| Menu | `Up` / `Down` then `Enter` |
| Accelerate | `W` or `Up` |
| Brake | `S` or `Down` |
| Steer | `A` / `D` or `Left` / `Right` |
| Quit to menu | `Esc` or `Q` |

Stay on the asphalt. Hitting another car slams the brakes. Lights go red-red-red-green, then race five AI cars to a packed finish line.

The main menu has **Music: On/Off** to pause or resume the soundtrack.

## GitHub social preview

`Assets/PsyRacerSplash.jpg` is the game cover. After you publish the repo, set it as the social preview so Discord, X, Slack, and GitHub itself show this art when the link is shared:

1. Open the repo on GitHub
2. **Settings → General → Social preview**
3. Upload `Assets/PsyRacerSplash.jpg`

## Credits

- **Game** — Diamond Hand Dev (DiamondHand.Dev)
- **Title** — PsyRacer V1.0
- **Engine** — Python 3, standard library only
- **Music** — `Assets/Background Music.mp3`
- **Cover** — `Assets/PsyRacerSplash.jpg`

© Diamond Hand Dev. All rights reserved.
