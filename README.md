# AoE2 DE Return of Rome: Crucible

A roguelite campaign for **Age of Empires II: DE - Return of Rome**, in the spirit of Age of Empires IV's Crucible
mode: survive a run on a battle map, earn currency, spend it in a hub on upgrades that carry into the next run.

> **Status: v1, in testing.** One camp and one run map. Feedback, bugs and ideas are welcome: open an issue.

Built with [aoe-agent-editor](https://github.com/h-strydom/aoe-agent-editor), which writes the scenarios, triggers,
AI and campaign, and keeps progress between missions in the campaign bank.

## Playing

Crucible comes as two mods, both on the official mod site (Mods > Browse Mods in game, search "Crucible"):

1. **Crucible Campaign**: the campaign and its intro slides. Subscribe and **enable** it (Mods > Installed Mods).
2. **Crucible**: the data mod. Subscribe, but leave it **disabled**.

Then open the Crucible campaign from Return of Rome's campaign screen, pick **Crucible** as the Data Mod, and start a
mission. Always start missions from the campaign screen: Restart and Next level don't keep the data mod, and a mission
started without it ends at once, to protect your saved progress.

Play the Camp first to spend your resources, then the Crucible for a run. What you buy in the camp carries into every
run.

## Building it yourself

### Requirements

- Windows, [uv](https://docs.astral.sh/uv/) and Python 3.13+
- Age of Empires II: DE with the Return of Rome expansion

### Getting started

```bash
uv sync
uv run crucible campaign --install  # build and install both mods locally
uv run crucible package             # zips for the mod site, in out/package
```

## What's possible

- [docs/feasibility.md](docs/feasibility.md): every idea tried for Crucible, what the engine allows, and how sure we
  are.
- [docs/aoe2-mechanics.md](docs/aoe2-mechanics.md): AoE2 DE and Chronicles mechanics brought into Return of Rome,
  with test results.

The test code that produced these results was removed on 2026-11-10; it's in the git history before that date.

## License

MIT
