---
name: godot-github
description: >
  Godot 4.7 programming and GitHub commit/push/tag/release for DiamondHand.Dev
  (especially PsyRacer), on any Windows PC on the LAN. Use when editing GDScript,
  scenes, shaders, Godot assets, running the editor, or when the user says commit,
  push, tag, release, GitHub, v0.x, homeserver, Developer share, or "replace the repo".
  Slash: /godot-github
metadata:
  short-description: "Godot 4.7 + GitHub playbook (LAN / any PC)"
---

# Godot + GitHub (any Windows PC)

Canonical copy: this file in the PsyRacer repo. It also lives on the homeserver at
`\\192.168.1.72\fast\Developer\.grok\skills\godot-github\SKILL.md`.
Project look/design locks: `AGENTS.md` at the repo root — follow that when it is loaded.

Grok often starts in the user home folder, not the repo. `git`/`gh` may be missing from PATH.
MCP GitHub file tools cannot ship game binaries. Do not rediscover that.

## Project roots (first that exists)

1. `\\192.168.1.72\fast\Developer\PsyRacer-Godot` (homeserver **fast** working copy)
2. Any git clone of `https://github.com/IcarusConsulting/PsyRacer` (`main`)

Prefer the git root that has `origin` → `IcarusConsulting/PsyRacer` when committing. After a successful push, **mirror back to the Developer share** unless the user says otherwise. Do not keep a second clone on this workstation.

## Resolve tools (do not assume PATH)

```
$git = @(
  (Get-Command git -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
  "C:\Program Files\Git\cmd\git.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

$gh = @(
  (Get-Command gh -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
  "C:\Program Files\GitHub CLI\gh.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

$godot = @(
  "$env:USERPROFILE\OneDrive\Desktop\Godot_v4.7.2-stable_win64_console.exe",
  "$env:USERPROFILE\Desktop\Godot_v4.7.2-stable_win64_console.exe",
  "C:\Users\gotch\OneDrive\Desktop\Godot_v4.7.2-stable_win64_console.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
```

If git is missing: `winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements`.

PowerShell in Grok: no `&&` (use `;`). `GIT_TERMINAL_PROMPT` is often `0`. `GIT_EDITOR` may be `cmd /c exit 0` (empty commit if you omit `-m`). PS 5.1 has no `utf8NoBOM`.

```
Remove-Item Env:GIT_TERMINAL_PROMPT -ErrorAction SilentlyContinue
$env:GIT_EDITOR = "true"
$env:GCM_INTERACTIVE = "always"
```

Commit identity (PsyRacer):

```
git config user.name  "diamondhand.DEV"
git config user.email "89435609+IcarusConsulting@users.noreply.github.com"
```

## GitHub: commit / push / tag / release

1. Work in the project git root (`main` → `IcarusConsulting/PsyRacer`).
2. `git add -A`; `git status`; `git diff --cached --stat`. Do **not** stage `.godot/` or Microsoft fonts (`YuGothR.ttc`).
3. `& $git commit -m "subject" -m "body"`
4. Push with GCM. If the user is logged into github.com, `git push` works without `gh auth login` (can take ~2 min). Do **not** use MCP `push_files` / `create_or_update_file` for png/jpg/mp3/ogv/mp4/ttf/ttc.
5. Version: `config/version` in `project.godot` (no `v`, e.g. `0.10`). Git tag uses `v` (`v0.10`).
6. Alpha: annotated tag + GitHub **prerelease**. `gh auth login --with-token` from GCM often fails (`missing read:org`). Use REST with the git credential; **never print the token**.

Windows vs GitHub case: `Assets` ≠ `assets`. Two-step `git mv` through a temp name. Do not rewrite history unless asked.

## Homeserver mirror

After a successful `git push origin main`:

```
robocopy <git-root> \\192.168.1.72\fast\Developer\PsyRacer-Godot /MIR /XD .godot .git /XF Thumbs.db desktop.ini /NFL /NDL /NP
```

Robocopy exit 0–7 is success. Also copy this skill to
`\\192.168.1.72\fast\Developer\.grok\skills\godot-github\SKILL.md` when it changed.

## Godot 4.7

- `res://` paths lowercase: `assets/`, `scenes/`, `scripts/`, `shaders/`.
- **Commit** `.import` and `.uid`. **Ignore** `.godot/`.
- Never commit Windows/Microsoft fonts. Bundled `YuGothR.ttc` if present, else `SystemFont` (Yu Gothic / Meiryo / Noto Sans CJK JP).
- `FRAME_HZ = 20` is pygame physics scaling only. No `max_fps`. Render follows vsync.
- Godot 4: no `fragment` color `return`; shader parameter names must not collide with locals; type `for` loop variables.
- `VideoStreamPlayer` needs Theora `.ogv` (`ffmpeg -an`).
- Cars: primitive 3D `HyperCar` until Blender `.glb`. `HyperCar.pose()` yaws/leans from lateral speed; chase cam stays on road heading. `car_*.png` sheets stay unused — not on `Sprite3D`.
- Headless "1 resources still in use at exit" is benign. ASCII compositor is **disabled**.
- Art: Imagine + `game-asset-core`. Flood-fill edge-black to alpha on car sheets.

## After a successful push

Reply with repo URL, commit URL, and confirm the Developer share path. Do not claim a push or mirror succeeded without command output.
