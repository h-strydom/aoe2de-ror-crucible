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
| 4 | Traders | gray (6) | Egyptian (eye candy) | neutral to everyone; the player trades with their dock and markets |
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
- four walled posts, walls and watch towers only: 92-116, 52-56; 44-52, 56-72; 162-178, 98-116; 42-56, 104-116.
  Defences, not districts: they stop the player rushing the enemy (and look good). No reward, no raids.

**Traders (4)**:
- the north-west trading post, in the ocean: 2-14, 2-16 (dock)
- the south-east trading post, in the mountains: 178-219, 180-213 (markets)

## Rules

**Start.** The player owns only the Town Center and the Wonder. Every other building of the centre base, walls
included, belongs to the Allies (5):
- buildings start at 1 HP: they work (a tower shoots) but one hit destroys them. The player sees how the base will
  look, and gets defences that are free but one hit from gone
- walls keep their normal HP but start randomly damaged: some destroyed, some heavily damaged, some fine; more damaged
  than destroyed or whole

Meta upgrades will hand more of these buildings to the player at the start (later: from the campaign bank).

**Ages.** The City States (2) start in the Iron Age (eye candy). The Legion (3) starts in the Stone Age and ages up with
the waves: its bases around the map get stronger too, so leaving them makes them more dangerous.

**Waves.** The waves are the Legion's (3), spawned at the City States (2), one every 5 minutes, alternating:
- capital waves: two armies from the Capital, one per lane
- city-state waves: two smaller armies, one from each of the Western and Eastern City States

After each capital and city-state pair the Legion ages up: it gets every tech of the new age, and the new age's units
join the wave pool. Units already on the map get the techs too.

| Wave | Time | Age | From | Example |
|---|---|---|---|---|
| 1 | 5:00 | Stone | Capital | 4 + 4 Clubmen |
| 2 | 10:00 | Stone | city states | 6 + 4 Clubmen |
| 3 | 15:00 | Tool (up) | Capital | Axemen, Slingers, Scouts, Bowmen join |
| 4 | 20:00 | Tool | city states | |
| 5 | 25:00 | Bronze (up) | Capital | Bronze Age units join |
| 6 | 30:00 | Bronze | city states | |
| 7 | 35:00 | Iron (up) | Capital | Iron Age units join |
| 8 | 40:00 | Iron | city states | |
| 9 | 45:00 | post-Iron (up) | all three | the last, massive wave |

post-Iron: the last upgrades, such as Ballista to Helepolis, Catapult to Heavy Catapult, Phalangite to Centurion.

**Calling a wave early.** A "Spawn next wave" button (on the Wonder) spawns the next wave now and starts the 5 minute
timer again. A short cooldown after any wave stops the next one spawning on top of it before it has walked out. A
called wave that brings an age up brings it early: the player can call waves 1 and 2 at once, fight the Clubmen, and
then meet Tool Age units at 5:00. Calling a wave doesn't clear it: a wave is cleared when every unit in it is dead.

**Raids.** Each Legion outpost or district still standing sends raiding parties at the player, at random times: the
longer a run takes, the more raids. The bases also post units to hold places, send parties to harass the player's
villagers and patrol around them. Destroying a base stops all of that and gives one decision reward (one more shop
pick).

**Invulnerable.** Everything of the City States (2) can't be attacked.

**Difficulty.** Higher difficulties start the Legion with bonuses or in a later age (more post-Iron waves), and make
raids more frequent and harder. The 5 minute wave timer never changes.

**Win and lose.**
- win: wave 9 has spawned and every wave is cleared
- lose: the player's Wonder is destroyed

## Open

- the waves' contents by age, and how large the last wave is
- the cooldown after calling a wave (how long it takes a wave to walk out)
- what a raiding party is (size, units), and how raid frequency is drawn
- how the bases' behaviour is done: an AI (RoR ships AiBuilder_p, a scenario AI set by phases) or triggers
- player 5: where its units appear when the Allies send help
- what the decision reward is beyond one more shop pick
- the example had wave 4 in the Stone Age; read as Tool, since the age up comes at wave 3
