# Waves

Built 2026-11-21: the numbers live in `src/crucible/scenarios/wave_table.py` (this page is the reasoning), the
running of them in `scenarios/waves.py` and `waves.xs`. Unit ages are RoR's own (read from the data file): Hoplites, Stone
Throwers and Priests come with their Bronze Age buildings; Composite Bowmen are Bronze; Ballistas, Catapults,
elephants, horse archers and the Long Swordsman are Iron; the last upgrades (Legionary, Centurion, Cataphract,
Armored Elephant, Heavy Horse Archer, Heavy Catapult, Helepolis) are the post-Iron wave.

Struggling is the point: the Legion ages on its own clock, and the player's way to keep up is the meta (the Bronze Age
itself comes with hub tier 3) and the run's boons.

## Shape

- **Wave 0** at the start, instant: killing it gives free Poor boons (docs/todo.md). Then waves 1 to 9 as now, so the
  objective becomes "Defeat 10 waves".
- **Four lanes**: Capital west, Capital east (the capital waves), the Western and Eastern City States (the city-state
  waves: one group from each side). Every wave is two groups; wave 9 is all four. All sizes below are per group.
- **Melee and ranged in every wave**: melee units get stuck on walls, so a wave always brings ranged units (and siege
  later) to take them down. A lane's **archetype** skews the ratio and picks the unit lines: about 70% its main kind,
  30% the other, at least one of each.
- **Archetypes**: at the start of a run each lane rolls one (no two the same, so each wave mixes two kinds). From wave
  3 (Tool Age) a lane's waves follow its archetype; before that every lane is Clubmen with a few Slingers.
- **Siege** in every wave from the Bronze Age on.

## Ages

What the player's age is expected to be at each wave, and when the Legion ages, by difficulty. Moderate is keeping up;
Hard needs the player ahead of the curve; Standard leaves them an age up.

| Time | Wave | Player, Standard | Player, Moderate | Player, Hard |
|---|---|---|---|---|
| 0:00 | 0 | Stone | Stone | Stone |
| 5:00 | 1 | Stone | Stone | Stone, going Tool |
| 10:00 | 2 | Stone | going Tool (~10-12) | Tool (~8) |
| 15:00 | 3 | Tool | Tool | Tool, saving for Bronze |
| 20:00 | 4 | Tool | Tool, going Bronze | Bronze (~18-20) |
| 25:00 | 5 | Tool, going Bronze | Bronze (~23-25) | Bronze |
| 30:00 | 6 | Bronze | Bronze | Iron (~28-30) |
| 35:00 | 7 | Bronze | Iron (~35-38) | Iron |
| 40:00+ | 8-9 | Bronze, Iron | Iron | Iron |

| The Legion reaches | Standard | Moderate | Hard |
|---|---|---|---|
| Tool | wave 4 (20:00) | wave 3 (15:00) | wave 2 (10:00) |
| Bronze | wave 6 (30:00) | wave 5 (25:00) | wave 4 (20:00) |
| Iron | wave 8 (40:00) | wave 7 (35:00) | wave 6 (30:00) |
| Post-Iron | wave 9 | wave 9 | wave 8 |

## Archetypes

Each age: the main line (about 70%), then the other kind (about 30%).

| Archetype | Main | Tool | Bronze | Iron | Post-Iron |
|---|---|---|---|---|---|
| Swordsmen | melee | Axemen / Bowmen | Short, Broad Swordsmen / Improved Bowmen | Long Swordsmen / Composite Bowmen | Legionaries / Composite Bowmen |
| Phalanx | melee | Axemen / Slingers | Hoplites / Slingers, Improved Bowmen | Phalangites / Composite Bowmen | Centurions / Composite Bowmen |
| Cavalry | melee | Scouts / Bowmen | Cavalry, Camel Riders / Chariot Archers | Heavy Cavalry / Horse Archers | Cataphracts / Heavy Horse Archers |
| Elephants | melee | Scouts / Bowmen | Chariots / Improved Bowmen | War Elephants / Elephant Archers | Armored Elephants / Elephant Archers |
| Bowmen | ranged | Bowmen, Slingers / Axemen | Improved, Composite Bowmen / Short Swordsmen | Composite Bowmen, Elephant Archers / Long Swordsmen | Composite Bowmen, Elephant Archers / Legionaries |
| Horse archers | ranged | Bowmen / Scouts | Chariot Archers / Cavalry | Horse Archers / Heavy Cavalry | Heavy Horse Archers / Cataphracts |
| Chariots | both | Scouts / Bowmen | Chariots / Chariot Archers | Scythe Chariots / Chariot Archers | Scythe Chariots / Elephant Archers |

Before the archetypes (Stone waves): Clubmen, with Slingers as the ranged part (the Legion spawns them before it could
train them).

Siege per group: Bronze: 1 Stone Thrower. Iron: 1 Catapult, 1 Ballista. Post-Iron: 2 Heavy Catapults, 1-2
Helepolises. Priests: 1 per group from the Bronze Age on Hard, from the Iron Age on Moderate.

## Waves by difficulty

Per group, as units (melee and ranged, split by the archetype) + siege. The age is the Legion's (above).

| Wave | Standard | Moderate | Hard |
|---|---|---|---|
| 0 | 3 Clubmen | 4 Clubmen | 5 Clubmen |
| 1 | 3 Clubmen, 1 Slinger | 4 Clubmen, 1 Slinger | 4 Clubmen, 2 Slingers |
| 2 | 3 Clubmen, 1 Slinger | 4 Clubmen, 2 Slingers | 7 (Tool) |
| 3 | 5 | 7 (Tool) | 8 |
| 4 | 6 (Tool) | 8 | 10 + 1 (Bronze) |
| 5 | 7 | 9 + 1 (Bronze) | 11 + 1 |
| 6 | 8 + 1 (Bronze) | 10 + 1 | 13 + 2 (Iron) |
| 7 | 9 + 1 | 11 + 2 (Iron) | 14 + 2 |
| 8 | 10 + 2 (Iron) | 13 + 2 | 16 + 3 (post-Iron) |
| 9 | 11 + 3 (post-Iron) | 15 + 3 (post-Iron) | 18 + 4 |

Totals (two groups; wave 9: four): Standard 6, 8, 8, 10, 12, 14, 18, 20, 24, 56; Moderate 8, 10, 12, 14, 16, 20, 22,
26, 30, 72; Hard 10, 12, 14, 16, 22, 24, 30, 32, 38, 88.

- **Wave 0** is melee only (playtest 2026-11-21): Clubmen, no Slingers. It walks from the Capital (about a minute),
  and the meta's starting Clubmen count.
- Difficulty changes sizes, the Legion's age clock and the Priest extras; the 5-minute timer never changes
  (docs/arena.md).

## How it runs

- The XS reads the game difficulty (`xsGetDifficulty`): Easiest and Standard play Standard, Moderate Moderate, Hard
  and up Hard. It rolls the lanes' archetypes, then spawns each group with `xsCreateUnit` in rows inwards from the
  spawn row and keeps the ids, so a wave is staged when all its living units are on a staging row and defeated when
  none is left.
- The Legion doesn't age itself (no techs): only which units it spawns follows the clock.
- Archetypes are named in chat as each wave walks in ("Wave 3 (Tool Age), Capital west: Cavalry, ...").

## Open

- Wave 9: 56 to 88 units in all; too big? Tune after a playtest.
- The Legion researching its age techs (armour, attack) with the clock.
- A Priests or Siege archetype for later tiers?
