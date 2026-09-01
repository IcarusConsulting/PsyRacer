# Grok on other PCs

Open this folder as the Grok working directory (local clone or `\\192.168.1.72\fast\Developer\PsyRacer-Godot`). `AGENTS.md` and `.grok/skills/godot-github` load automatically.

To pick up the playbook even when Grok starts in your home folder, add to `~/.grok/config.toml`:

```toml
[skills]
paths = ["\\\\192.168.1.72\\fast\\Developer\\.grok\\skills"]
```
