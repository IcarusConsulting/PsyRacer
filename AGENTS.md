# PsyRacer

Godot 4.7.2 Forward+ night-highway racer by **DiamondHand.Dev**.

This file auto-loads for Grok on **any PC** whose cwd is this repo (local clone or LAN share).

| | |
| --- | --- |
| GitHub | https://github.com/IcarusConsulting/PsyRacer (`main`) |
| Working copy | `\\192.168.1.72\fast\Developer\PsyRacer-Godot` (homeserver **fast** share) |
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
- Title modes (all 20 km Medium): **Standard** (5 AI, collision → 50% max speed), **Chase** (cop merges at 3000 m, same top speed as player, ram chase, bust if player < 50 km/h), **Enforcement** (player is `police.glb`, 6 AI, rams remove AI with no player slowdown, win when none remain).
- Cars: Standard/Chase player is `assets/cars/player.glb`. Enforcement player and Chase cop are `police.glb`. AI use `ghost.glb`. Yaw/lean from lateral speed; chase cam stays on road heading. Primitive boxes remain a fallback if a GLB fails to load.

## Controls

WASD / arrows drive. Enter starts. Esc returns to title. M mutes.
