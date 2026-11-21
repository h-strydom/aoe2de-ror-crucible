# Evolving waves: proposal

Not built: a proposal to review (2026-11-21). It replaces the fixed table in docs/waves.md after a Hard playtest: wave
0 was harmless and wave 5 brought Stone Throwers, a cliff rather than a climb.

The idea (from the playtest): no hand-set sizes or ages. Each lane is an army that starts tiny and **evolves one step
each time it's ready**, by chance, so every run's enemy grows differently. Waves never end; rewards grow with them.

## Shape

- **Lanes**: the Capital's two, the Western and Eastern City States'. Each rolls an **archetype** at the start (no two
  the same, as now); the archetype steers which swaps and upgrades it takes.
- **Wave 0**: 2 melee and 2 ranged per Capital lane (Clubmen, Slingers). Killing it puts a free Poor boon on each slot
  (built).
- **Cadence**: a wave every **5 min on Standard, 3 on Moderate, 2 on Hard**; the Send button still sends early. Waves
  alternate Capital / City States as now, so a lane sends every other wave.
- **Evolve when ready**: as a lane's next wave is spawned, it takes one step (below), then spawns. Chat says it: "Capital
  west evolves: Bowmen become Improved Bowmen."
- **No end**: "Defeat 10 waves" goes; the objective shows waves defeated. The run ends when the Wonder falls (the best
  wave can go to the bank for the meta later).

## A step

Each step is one of these, by weight; the age-up roll comes first.

| Step | Chance | What |
|---|---|---|
| Age up | 5%, +5% for every step without one, back to 5% after | The Legion's next age: its age tech (free stats), new swaps and upgrades open, and from the Bronze Age a siege unit joins (one more each age after) |
| Grow | 45 of the rest | +1 unit, or +1 per 6 in the army once it's bigger; the new unit goes to the archetype's main kind about 60-70% of the time |
| Upgrade | 30 | A tech of the Legion's age or earlier it hasn't got: attack, armour, range, speed, HP (list below) |
| Swap | 25 | One unit line becomes another of the same kind, open in its age (paths below) |

**Catch-up rule** (from a simulation of 2000 runs): with free swaps, a lane often reached the Post-Iron Age still on
Axemen and Slingers. So a swap always takes a line that's an age or more behind first, and an age up also lifts any line
two ages behind by one.

Simulated pacing per lane with these numbers: Tool around step 5 (10-90%: 2-9), Bronze around 10 (6-15), Iron around 16
(10-22), Post-Iron around 21 (15-28); at step 30 about 30 units (20-50). A lane steps every other wave, so double these
for wave numbers: on Hard (2 min), Bronze at around 40 minutes.

## Upgrades (RoR's own techs, researched for the Legion)

| Age | Upgrades |
|---|---|
| Tool | Tool Working (attack), Leather Armor (soldiers, archers, cavalry) |
| Bronze | Metal Working, Scale Armor (soldiers, archers, cavalry), Bronze Shield, Wheel (speed), Nobility (cavalry HP) |
| Iron | Metallurgy, Chain Mail (three), Iron Shield, Alchemy (missile attack), Ballistics, Aristocracy |
| Post-Iron | Logistics, Tower Shield, Medicine (Priests) |

Archetypes weight their own: Cavalry takes the cavalry armour and Nobility first, Bowmen the archer armour and Alchemy.

## Swaps (each step one slot's line)

| Kind | Stone | Tool | Bronze | Iron | Post-Iron |
|---|---|---|---|---|---|
| Infantry | Clubmen | Axemen | Short Swordsmen, Hoplites | Broad, Long Swordsmen, Phalangites | Legionaries, Centurions |
| Foot ranged | Slingers | Bowmen, Slingers | Improved Bowmen | Composite Bowmen | Composite Bowmen |
| Mounted | | Scouts | Cavalry, Camel Riders, Chariots | Heavy Cavalry, War Elephants, Scythe Chariots | Cataphracts, Armored Elephants |
| Mounted ranged | | | Chariot Archers | Horse Archers, Elephant Archers | Heavy Horse Archers |

A swap moves along a row (a line's next) or, if the archetype allows, across rows of the same kind (melee to melee,
ranged to ranged): Cavalry swaps infantry into mounted, Phalanx stays on Hoplites and their line, Chariots swaps into
chariots. So the archetype shows more as the run goes on.

## Rewards

Every wave defeated still gives a boon choice. As waves grow, the shop's tier-up chance grows with the wave number
(say +1% per wave on each roll, so wave 20 is 30%/40% instead of 10%/20%), and every 5th wave gives two choices.

## What changes from now

- `wave_table.py`: the fixed groups and age clock go; it holds wave 0, the step weights, the age-up roll, the upgrade
  and swap tables, and the cadence per difficulty.
- `waves.xs`: each lane keeps its army (counts per line, its techs, its age); a step before each spawn; the Legion's
  techs and ages researched by trigger (a looping trigger per tech, as for the button, set by a variable).
- Objective and victory: waves defeated, no claim-victory decision.

## Questions for you

1. **Shared or per lane?** Per lane (above: four armies growing apart) or one Legion that steps once per wave and every
   lane spawns from it?
2. **Age up for the whole Legion?** The age tech gives the Legion free stats, so if one lane ages, all its units do.
   Simplest: one Legion age, shared, rolled once per wave; lanes still grow and swap on their own.
3. **Difficulty**: only the cadence (5/3/2 min), or also the step weights (Hard grows more)?
4. **The end**: run until the Wonder falls, or keep a "claim victory" button after, say, wave 20 for a shorter run?
