# Evolving waves

Built 2026-11-21 (numbers in `src/crucible/scenarios/wave_table.py`, running in `waves.py` and `waves.xs`). It replaces the fixed table in docs/waves.md after a Hard playtest: wave
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

## Decided (2026-11-21)

- Each lane grows and swaps on its own; upgrades and ages are the Legion's, shared: a lane that rolls one doesn't grow.
- An upgrade is only rolled if it improves a unit some lane fields (read from each tech's effects in the data: Bronze
  Shield helps Slingers, Leather Armor for archers doesn't), or the siege and Priests once the Legion can bring them.
- Siege and Priests aren't in every wave: each lane brings them by chance per age (wave_table SIEGE_CHANCE,
  PRIEST_CHANCE).
- Two more steps at weight 0 for now: nothing, and again (two more steps, which may be again: at most MAX_STEPS).
- Age up: from 2%, +2% per step without one (steps come two per wave, so shared ageing is faster than the per-lane
  simulation above).
- Difficulty is the cadence only; the run goes on until the Wonder falls.
- A browser simulation of 50 waves lives outside the repo (`_Workspace/crucible-wave-sim`, `generate.py` writes it
  from these tables).

## Paths and families (2026-11-21, built)

Replaces the swap tables above. Units come in families (Swordsmen: Short, Broad, Long Swordsman, Legionary); a lane's
slot holds a family on its archetype's path and fields the line the Legion has upgraded that family to. The waves just
spawn the better unit: no line-upgrade tech is researched (stat upgrades and ages still are).

| Archetype | Main | Support |
|---|---|---|
| Legion | Clubmen > Swordsmen | Slingers > Bowmen > (Composite, or Chariot Archers) |
| Phalanx | Clubmen > Hoplites | the same |
| Cavalry | Clubmen > Scouts > Cavalry | the same |
| Chariots | Clubmen > Scouts > Chariots | Slingers > Bowmen > Chariot Archers |
| Elephants | Clubmen > Scouts > Chariots > Elephants | Slingers > Bowmen > Chariot Archers > Elephant Archers |
| Archers | Slingers > Bowmen | one of: Clubmen > Scouts > Chariots > (Camel Riders); Clubmen > Swordsmen; Clubmen > Hoplites; Clubmen > Scouts > Cavalry |
| Mounted Archers | Slingers > Bowmen > Chariot Archers > (Horse or Elephant Archers) | as Archers |

- Choices in a path are rolled once, at the start. The Post-Iron lines (Legionaries, Centurions, Cataphracts, Armored
  Elephants, Heavy Horse Archers) are main-slot only: a support stops a line short (Long Swordsmen, Phalangites, Heavy
  Cavalry).
- An age up moves every main slot on as far as the new age opens its path (MOVE_ON): a Cavalry lane is Scouts at the
  Tool Age, Cavalry at Bronze. Supports move on by swaps.
- Each step is done `scale` times: 1, +1 every 10 waves, times GROW_SCALE, UPGRADE_SCALE, SWAP_SCALE (1 now; curses
  can raise one). Age up: from 1%, +1% per step.
- A caption over a City States building at each lane names its archetype; chat says it too.
- Simulated (2000 Hard runs): Tool around wave 6, Bronze 12, Iron 18, Post-Iron 24; about 8 units a lane at wave 10, 14
  at 20, 25 at 30, 65 at 49. Archers' main and the supports end on Bronze Age units (RoR has nothing later).
- Open: what happens once the upgrades run out (around wave 35), and how siege and Priests mix in.
- Bowmen come from the Bronze Age, not the Tool (playtests 2026-11-21): Slingers beat the player's archers, and plain
  Bowmen in the Tool Age made a lane easier, so ranged lanes hold Slingers until then; they start as plain Bowmen (going
  straight to Improved was too big a jump), and Improved and Composite come by line upgrades.
- Line steps are swaps, per lane (playtest 2026-11-21): one or two waves into the Bronze Age, shared line upgrades and
  move-on had every lane on Hoplites and Composite Bowmen. Now a swap moves a slot up its family's next line (Short to
  Broad Swordsmen) or, at the top, to its path's next family; move-on is off; the shared upgrades are stat techs only.
  Simulated two waves into Bronze: Slingers 38%, Clubmen 21%, Axemen 15%, Scouts 9%, Bowmen 7%, Hoplites 1%.
