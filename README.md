# AoE2 DE Return of Rome: Crucible

A roguelite campaign for **Age of Empires II: DE - Return of Rome**, in the spirit of Age of Empires IV's Crucible
mode: survive a run on a battle map, earn currency, spend it in a hub on upgrades that carry into the next run.

> **Status: feasibility done, design next.** The test scenarios that settled what the engine can do have been
> retired; what they found is in [docs/](docs/). The first iteration will have one run map and one hub map.

Built with [aoe-agent-editor](https://github.com/h-strydom/aoe-agent-editor), which writes the scenarios, triggers,
AI and campaign, and keeps progress between missions in the campaign bank.

## Requirements

- Windows, [uv](https://docs.astral.sh/uv/) and Python 3.12+
- Age of Empires II: DE with the Return of Rome expansion

## Getting started

```bash
uv sync
```

## What's possible

- [docs/feasibility.md](docs/feasibility.md): every idea tried for Crucible, what the engine allows, and how sure we
  are.
- [docs/aoe2-mechanics.md](docs/aoe2-mechanics.md): AoE2 DE and Chronicles mechanics brought into Return of Rome,
  with test results.

The test code that produced these results was removed on 2026-11-10; it's in the git history before that date.

## License

MIT
