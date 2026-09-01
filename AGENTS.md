# PsyRacer

Godot 4.7.2 Forward+ night-highway racer by **DiamondHand.Dev**.

| | |
| --- | --- |
| Local | `C:\Users\gotch\PsyRacer-Godot` |
| GitHub | https://github.com/IcarusConsulting/PsyRacer (`main`) |
| Engine | `C:\Users\gotch\OneDrive\Desktop\Godot_v4.7.2-stable_win64.exe` |
| Version | `config/version` in `project.godot` (alpha; git tag `v` + that number) |
| Look bible | `assets/PsyRacerSplash.jpg` |
| Main scene | `scenes/boot.tscn` |

Git/Godot/push mechanics for this PC: user skill **godot-github** (`~/.grok/skills/godot-github/SKILL.md`).

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
