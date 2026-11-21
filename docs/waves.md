# Waves: proposal

Suggestions to review; nothing here is built yet. Unit ages are RoR's own (read from the data file): Hoplites, Stone
Throwers and Priests come with their Bronze Age buildings; Composite Bowmen are Bronze; Ballistas, Catapults,
elephants, horse archers and the Long Swordsman are Iron; the last upgrades (Legionary, Centurion, Cataphract,
Armored Elephant, Heavy Horse Archer, Heavy Catapult, Helepolis) are the post-Iron wave.

## Shape

- **Wave 0** at the start, instant: killing it gives free Poor boons (docs/todo.md). Then waves 1 to 9 as now, so the
  objective becomes "Defeat 10 waves".
- **Four lanes**: Capital west, Capital east (the capital waves), the Western and Eastern City States (the city-state
  waves). Wave 9 comes down all four.
- **Archetypes**: at the start of a run each lane rolls one (no two the same, so each wave mixes two kinds). From wave
  3 (Tool Age) a lane's waves are mostly its archetype's units; before that everyone is Clubmen.
- **Every wave** from 3 on: about 70% archetype, about 15-20% "others" (units of the same age from the other
  archetypes), and siege from Bronze on.

## Archetypes

| Archetype | Tool (waves 3-4) | Bronze (5-6) | Iron (7-8) | Post-Iron (9) |
|---|---|---|---|---|
| Swordsmen | Axemen | Short, then Broad Swordsmen | Long Swordsmen | Legionaries |
| Phalanx | Axemen, a few Slingers | Hoplites | Phalangites | Centurions |
| Bowmen | Bowmen, Slingers | Improved, then Composite Bowmen | Composite Bowmen, Elephant Archers | Composite Bowmen, Elephant Archers |
| Horse archers | Bowmen, Scouts | Chariot Archers | Horse Archers | Heavy Horse Archers |
| Cavalry | Scouts | Cavalry, Camel Riders | Heavy Cavalry | Cataphracts |
| Elephants | Scouts | Chariots | War Elephants | Armored Elephants |
| Chariots | Scouts | Chariots, Chariot Archers | Scythe Chariots, Chariot Archers | Scythe Chariots, Elephant Archers |

Others by age: Tool: Slingers, Bowmen, Scouts, Axemen. Bronze: any Bronze unit above, plus a Priest on Hard. Iron and
post-Iron: any of that age's units, Priests on Moderate and Hard.

Siege by age (per lane): Bronze: 1 Stone Thrower. Iron: 1 Catapult, 1 Ballista. Post-Iron: 2 Heavy Catapults,
1-2 Helepolises.

## Waves by difficulty

Units per lane (a capital wave is two lanes, a city-state wave two lanes, wave 9 four), as archetype + others +
siege.

| Wave | Age | From | Standard | Moderate | Hard |
|---|---|---|---|---|---|
| 0 | Stone | Capital | 2 Clubmen | 3 Clubmen | 3 Clubmen + 2 Slingers |
| 1 | Stone | Capital | 4 Clubmen | 5 Clubmen | 5 Clubmen + 1 Slinger |
| 2 | Stone | City states | 4 Clubmen | 5 Clubmen + 1 Slinger | 6 Clubmen + 2 Slingers |
| 3 | Tool | Capital | 5 + 1 | 6 + 2 | 8 + 2 |
| 4 | Tool | City states | 5 + 1 | 7 + 2 | 9 + 2 |
| 5 | Bronze | Capital | 6 + 1 + 1 | 8 + 2 + 1 | 10 + 2 + 1 |
| 6 | Bronze | City states | 6 + 2 + 1 | 9 + 2 + 1 | 11 + 3 + 1 |
| 7 | Iron | Capital | 7 + 2 + 2 | 10 + 2 + 2 | 12 + 3 + 2 |
| 8 | Iron | City states | 8 + 2 + 2 | 11 + 3 + 2 | 13 + 3 + 3 |
| 9 | Post-Iron | All four | 9 + 2 + 3 | 12 + 3 + 3 | 15 + 4 + 4 |

Totals, both lanes (wave 9: four): Standard 4, 8, 8, 12, 12, 16, 18, 22, 24, 56; Moderate 6, 10, 12, 16, 18, 22, 24,
28, 32, 72; Hard 10, 12, 16, 20, 22, 26, 30, 34, 38, 92.

- **Standard wave 0**: 4 Clubmen against a Town Center and the Wonder: not losable.
- **Hard wave 0**: Slingers outrange villagers, so the player needs a few soldiers by the time it arrives. It walks
  from the Capital (about a minute), and the meta's starting Clubmen count.
- Difficulty changes only sizes and the Slinger/Priest extras here; the 5-minute timer never changes (docs/arena.md).

## Open

- Wave 9: 56 to 92 units in all, spawned a row at a time; too big?
- Should "others" lean against the player (more anti-cavalry when they field cavalry), or stay random?
- Do archetypes stay hidden, or does the wave's name say it ("Capital west: Cavalry")?
- A Priests or Siege archetype for later tiers?
