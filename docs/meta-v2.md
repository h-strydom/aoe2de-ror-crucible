# Metaprogression v2: plan

Agreed 2026-11-22. Replaces the free-upgrade hub (docs/hub.md, assets/meta.aoe2scenario) with a currency earned in
runs and the hand-made hub map `metaprogression.aoe2scenario` (80x80, players 1-6).

## Currency

- Defeating a wave pays 1 of the resource of the Legion's age at that wave: Stone Age **food**, Tool **wood**, Bronze
  **gold**, Iron and Post-Iron **stone**. Wave 0 pays food.
- Banked as it's earned (a lost run still pays): keys `meta_food`, `meta_wood`, `meta_gold`, `meta_stone`.
- In the hub the bank is player 1's stockpile; buying an upgrade spends it (prices are placeholders for now: every
  upgrade free, with a cost field to fill in later). Leaving the hub banks what's left.
- **Reset everything** clears every upgrade and refunds everything spent.

## The hub map

| Player | Colour | Tier | Opens after | What it holds |
|---|---|---|---|---|
| 1 | purple | the Wonder | start | global upgrades |
| 2 | blue | 1, Stone | start (yours: TC, 4 villagers, 2 houses) | TC, Granary, Storage Pit, Barracks, 7 houses, 10 villagers, 3 Clubmen |
| 3 | red | 2, Tool | 5 upgrades | TC, Granary, Storage Pit (given); Barracks, Market, Archery Range, Stable, units, walls, a tower |
| 4 | green | 3, Bronze | 10 more | TC, Granary, Storage Pit, Barracks, Archery Range, Stable, Market (given); Academy, Government Center, Siege Workshop, Temple bought |
| 5 | yellow | 4, Iron | 20 more | the same, Iron Age |
| 6 | orange | 5, Post-Iron | 20 more | Barracks, Archery Range, Stable, Academy, Siege Workshop: the final units |

A building with an upgrade on offer is captioned `(*)`, one you can afford `(!)`.

## Upgrades by tier (where bought, levels, what the run gets)

**Tier 1, player 2**
- TC: villagers (6 levels, up to 10), houses (5 more than the 2 every run has), starting Granary, Storage Pit, Barracks.
- Barracks: 3 starting Clubmen.

**Tier 2, player 3** (its TC, Granary and Storage Pit are given)
- TC: a second starting Barracks (Axe upgrade: the 3 Clubmen are Axemen; then 2 more Axemen), starting Market (its
  Tool Age row), starting Archery Range (3, then 2 starting Bowmen), starting Stable (a starting Scout).
- Granary: Watch Tower (research it; the base's towers are yours, as Watch Towers), Small Wall (the base's Small Walls
  are yours, undamaged).
- Storage Pit: its first row of techs.

**Tier 3, player 4** (its buildings given but the Academy, Government Center, Siege Workshop and Temple). The run can
research the Bronze Age.
- TC: starting Academy (and Hoplites), Government Center (its Bronze Age techs), Siege Workshop (building it, and
  Stone Throwers; no starting one), Temple (starting Temple, and its Bronze Age techs).
- Granary: Sentry Tower (starting towers are Sentry Towers; research it), Medium Wall (starting walls are Medium).
- Storage Pit, Market: their next rows. Market: Wheel (and Chariots, without their buildings' own unlocks).
- Barracks: Short, then Broad Swordsmen (starting melee upgraded, and training them).
- TC: the Dock's Bronze Age row (Fishing Ship, Medium War Ship, Merchant Ship): the hub map has no Dock, and the
  Tool Age has no Dock techs (its ships come free). From the Bronze Age the run lets the player build Town Centers (RoR's own, slot 11).
- Archery Range: Improved, then Composite Bowmen (the same).
- Stable: Camel Riders; Cavalry (a starting Cavalry, +1 a level up to 5).

**Tier 4, player 5**. The run can research the Iron Age.
- Starting units become Long Swordsmen, Heavy Cavalry, Horse Archers; Iron Age units and techs to research.
- Granary: Guard Tower (starting towers upgraded, research it; no Ballista Tower), Fortified Wall (the camp's
  Fortified Walls are yours; Medium Walls stay Medium).
- Temple, Government Center: their Iron Age techs.
- TC (its place, new 2026-11-23): the Dock's Iron Age row (Trireme, Heavy Transport, Catapult Trireme, Juggernaut).

**Tier 5, player 6**: access only (starting units aren't upgraded): Legionary, Centurion, Cataphract, Heavy Horse
Archer, Elephant Archer, War and Armored Elephant, Heavy Catapult, Helepolis, and their upgrades.

**The Wonder (player 1)**
- From the start: starting resources (+50 food, 50 wood, 20 gold, 20 stone; 5 levels), resources last longer (+2%; 5).
- With the Bronze Age: an extra boon slot (2), faster boon research (5 levels, the last instant), resource density:
  natural food x2, wood x2, mining x2 (1 each).
- With the Iron Age: an extra boon slot (1), resources last longer (+2%; 5 more), villager training speed (+10%; 5),
  villager cost (-5 food; 5).
- With the Post-Iron tier: the final boon slot.

Each tier player keeps a Barracks (a house isn't enough) in the hub map's north corner: buying everything left them with nothing, and the hub
was won at once (playtest 2026-11-23).

## Build order

1. Currency: earned in the run, banked per wave. *Built.*
2. The new hub: tiers on players 2-6, places, captions, the Wonder, reset with refund, the stockpile. *Built
   (2026-11-22): every upgrade on offer in the hub; the run applies only the old ones yet.*
3. Run effects for tiers 1-2 (mostly today's), walls undamaged. *Built.*
4. Run effects for tiers 3-5: unit and tech access per upgrade, starting unit upgrades, tower and wall tiers, ages.
   *Built (2026-11-22): run_meta's UNLOCKS, ROWS (the buildings' techs by age), UNIT_UNLOCKS (each once the player
   reaches its age), the starting lines, the tower and wall lines.*
5. The Wonder's effects in the run. *Built: starting resources, lasting resources and densities (gaia resources
   multiplied at the start), villager training time and cost.*

## Open

- Prices (placeholders now).
- The old hub map and its tests go once the new one works.
