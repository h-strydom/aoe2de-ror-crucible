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

## The data mod test

```bash
uv run crucible test-mod --install
```

Can the campaign depend on a mod for what triggers can't do? This builds and installs:
- **Crucible Test Data**, a data mod: Return of Rome's own data file and `dropsites.json`, with Hoplites at 999
  hit points, Axemen at 400, the Greeks stripped of their bonuses (a "civ with no bonuses") and Houses
  accepting wood.
- **crucible_mod_test**, a three-mission campaign. A trigger makes Scouts trainable at the Barracks, to test
  buildings that train new units with triggers alone. Mission 3 has two Sentry Towers: one with its arrow limit
  raised from 1 to 6 by trigger, one unchanged, to see whether each garrisoned unit adds an arrow.

Enable the mod in Mods > Installed Mods, restart, then pick "Crucible Test Data" in the campaign's Data Mod
dropdown. The briefing lists the checks.

Found so far: a mod holding only `dropsites.json` counts as a data mod of its own, so everything goes in one data
mod. Scouts trained at the Barracks by trigger alone.

## The resource test

```bash
uv run crucible resource-test --install
uv run crucible resource-report
```

A standalone scenario (pick "Crucible Test Data" as the Data Mod in the Scenario lobby). Each allied computer
player tests one thing, and every gatherer starts working on its own. Round 2 tests resources that hold a different
resource:
- trees switched to gold, per tree;
- berry bushes switched to stone;
- a tree type switched to stone for the whole type;
- a fish switched to gold, for your fishing boat;
- a script paying 10% of chopped wood as gold;
- normal lumberjacks as the control.

A script logs every player's stockpile and each pile's amount and stored resource every 10 seconds;
`resource-report` prints it. Round 1's results (work rate, gather multipliers, generation, trickles) are in
[docs/feasibility.md](docs/feasibility.md).

## The combat test

```bash
uv run crucible combat-test --install
uv run crucible combat-report
```

A standalone scenario: your test units face passive enemy targets in lanes, each change on one unit next to an
unchanged control:
- friendly fire 0 and splash width 3 on Stone Throwers;
- Catapults firing a ballista bolt, and a fast, flat projectile;
- a Ballista with minimum range 0;
- a Hoplite with range 3;
- trade income shares of 25% food, wood and stone on a trade boat.

A script logs hit points and your resources every 5 seconds; `combat-report` prints it.

## What's possible

[docs/feasibility.md](docs/feasibility.md) collects every idea tried so far, what the engine allows, and how sure we are.

## License

MIT
