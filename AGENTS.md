# PsyRacer

Godot 4.7.2 Forward+ night-highway racer by **DiamondHand.Dev**.

This file auto-loads for Grok on **any PC** whose cwd is this repo (local clone or LAN share).

| | |
| --- | --- |
| GitHub | https://github.com/IcarusConsulting/PsyRacer (`main`) |
| LAN mirror | `\\192.168.1.72\fast\Developer\PsyRacer-Godot` |
| This workstation | `C:\Users\gotch\PsyRacer-Godot` |
| Version | `config/version` in `project.godot` (alpha; git tag `v` + that number) |
| Look bible | `assets/PsyRacerSplash.jpg` |
| Main scene | `scenes/boot.tscn` |
| Playbook | `.grok/skills/godot-github/SKILL.md` (also `\\192.168.1.72\fast\Developer\.grok\skills\`) |

On a new Grok Build PC, either open this folder as cwd or add to `~/.grok/config.toml`:

```toml
[skills]
paths = ["\\\\192.168.1.72\\fast\\Developer\\.grok\\skills"]
```

## Design locks (do not regress)

- No trees, no roadside buildings, no rear-view mirror, no lamp **cones** (keep LED bulbs).
- Horizon cyberpunk city eases closer/larger toward the finish.
- Matrix rain wraps the sky (cylinder around the camera) and dies at the horizon; falls from the sky — cylinder `UV.y` is already top, do not flip.
- Splash: visor clip (`assets/splash_intro.ogv` / `splash_still.jpg`); title + UI stay until the white flash into the race; title fill hue-shifts, orange border stays; byline `by DiamondHand.Dev`.
- Music: `assets/Background Music.mp3` loops from launch, `M` mutes, videos have no audio.
- Lamps sit just outside the roadway, blue-white both sides.
- Overhead NEXCO-style gantries every 2000 m (Yu Gothic / system CJK).
- Easy 10 km / Medium 20 km / Hard 30 km; 5 AI; collision → 50% max speed.
- Cars are the primitive 3D hypercar (boxes/cylinders), not sprite sheets. Yaw/lean from lateral speed; chase cam stays on road heading.

## Controls

WASD / arrows drive. Enter starts. Esc returns to title. M mutes.
