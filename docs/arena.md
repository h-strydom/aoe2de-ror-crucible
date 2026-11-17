# The arena

`assets/crucible_arena.aoe2scenario` is the run map, made by hand in the editor (`crucible arena save` / `install`).
It holds terrain, bases and decoration only: no triggers, no win condition. Everything below is scripted on top of it
by a build, so the map can keep being edited without losing the scripting.

Map: 220 x 220. Compass: y = 0 is north, x = 0 is west.

## Factions

| Player | Faction | Colour | Civ (architecture) | Role |
|---|---|---|---|---|
| 1 | Player | purple (5) | Greek | the human; base in the middle |
| 2 | City States | orange (7) | Roman | every unit and building invulnerable; where the waves spawn |
| 3 | Legion | red (1) | Roman | the main enemy: the waves and the destroyable bases around the map |
| 4 | Traders | gray (6) | (eye candy) | neutral to everyone; the player trades with their dock and markets |
| 5 | Allies | gray (6) | Greek | the player's ally: resources sent for objectives, units sent to help. **Not in the map yet** |

Diplomacy: 1 and 5 allied; 2 and 3 allied and enemies of 1 and 5; 4 neutral to everyone.
All civs are the bonus-less style civs (`datamod/civs.py`).

## Places

As placed in the map now (tile boxes, x0-x1, y0-y1).

**Player (1)** - the centre base, 94-124, 94-132: the Wonder (109.5, 109.5), a Town Center, walls, towers, houses,
barracks and the rest.

**City States (2)** - the wave spawns:
- the Capital: the large two-lane base in the north, 84-134, 0-20
- the Western City State: 0-20, 84-126
- the Eastern City State: 200-220, 94-124

**Legion (3)** - each one destroyed gives a decision reward; while it stands it sends raiding parties:
- the north-west island outpost: 18-28, 40-54 (docks)
- the north-east island outpost: 184-218, 2-46 (docks, Town Center)
- the southern economic district: 94-116, 160-182 (farms, granaries)
- the southern mining district: 69-90, 205-212
- the south-west military district: 6-26, 198-220 (stables)
- the south-south-east military district: 131-157, 198-215 (archery ranges)
- four walled posts with only walls and watch towers: 92-116, 52-56; 44-52, 56-72; 162-178, 98-116; 42-56, 104-116
  (**open**: what are these?)

**Traders (4)**:
- the north-west trading post, in the ocean: 2-14, 2-16 (dock)
- the south-east trading post, in the mountains: 178-219, 180-213 (markets)

## Rules

**Start.** The player owns only the Town Center and the Wonder. Every other building of the centre base belongs to the
Allies (5):
- buildings start at 1 HP: the player sees how the base will look, but the extra defences are useless
- walls keep their normal HP but start randomly damaged: some destroyed, some heavily damaged, some fine; more damaged
  than destroyed or whole

Meta upgrades will hand more of these buildings to the player at the start (later: from the campaign bank).

**Waves.** The waves are the Legion's (3), spawned at the City States (2). They alternate:
- odd waves: two large armies from the Capital (one per lane)
- even waves: two smaller armies, one from each of the Western and Eastern City States

After each wave the shop opens (`shop/`).

**Raids.** Each Legion outpost or district still standing sends raiding parties at the player between waves. Destroying
it stops its raids and gives one decision reward (one more shop pick).

**Invulnerable.** Everything of the City States (2) can't be attacked.

**Win and lose.**
- win: every wave defeated
- lose: the player's Wonder is destroyed

## Open

- the four walled posts of the Legion: outposts, chokepoints, or just walls?
- the walls of the centre base: the Allies' (with the other buildings) or the player's?
- how many waves, their size and timing; when the first raid comes and how often
- what a raiding party is (size, units) and what triggers it to leave
- player 5: where its units appear when the Allies send help
- what the decision reward is beyond one more shop pick
