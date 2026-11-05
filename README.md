# AoE2 DE Return of Rome: Crucible

A roguelite campaign for **Age of Empires II: DE - Return of Rome**, in the spirit of Age of Empires IV's Crucible
mode: survive a run on a battle map, earn currency, spend it in a hub on upgrades that carry into the next run.

> **Status: setting up.** The first iteration will have one run map and one hub map. Before designing them, a test
> map settles what the engine can do.

Built with [aoe-agent-editor](https://github.com/h-strydom/aoe-agent-editor), which writes the scenarios, triggers,
AI and campaign, and keeps progress between missions in the campaign bank.

## Requirements

- Windows, [uv](https://docs.astral.sh/uv/) and Python 3.12+
- Age of Empires II: DE with the Return of Rome expansion

## Getting started

```bash
uv sync
```

## The engine test map

```bash
uv run crucible test-map --install
```

Builds `out/crucible_engine_test.aoe2scenario` and copies it into your Return of Rome scenario folder. Play it from
Return of Rome's Scenario menu. Each part of the map answers one question, with a control beside it:

| Where | Question | What's there |
|---|---|---|
| Top-left edge | Can ground be walkable but unbuildable? | Strips of Rock 1, Quicksand, Bogland, Beach, Swamp, Shallows and Ice, with villagers and resources to try building on each |
| Left (start) | Can units at the spawn be made safe? | A road-bordered square; every second, your units inside become unattackable. An enemy army (with stone throwers, for splash) marches in at 0:20; two hoplites outside are the control |
| Bottom | Can one object's resources be changed? | Berry bushes set to 200 food over an area (row A) next to untouched ones (row B); gold mines set to 50 by a type-wide change; stone mines to 75 per object |
| Right | Do units march in formation? | Two allied groups: group A takes a line formation at 0:30 and a box formation at 1:30; group B just moves |

The briefing in game lists what to look for.

## License

MIT
