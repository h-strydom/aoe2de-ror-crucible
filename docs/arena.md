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
| 4 | Traders | gray (6) | Egyptian (eye candy) | allied with everyone (neutral ground); the player trades with their dock and markets |
| 5 | Allies | gray (6) | Greek | the player's ally: resources sent for objectives, units sent to help. **Not in the map yet** |

Diplomacy: 1 and 5 allied, sharing vision; 2 and 3 allied and enemies of 1 and 5; 4 allied with everyone.
Vision: 2, 3 and 4 see the whole map; 1 and 5 have fog.
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
- 3 seconds in, once the meta upgrades have kept the player's share (and the 2 houses every run starts with), the
  Allies' other buildings in the camp are destroyed (their rubble stays a while), out of the way; their walls and
  towers stay, and an unattackable Allies house on the north edge keeps them in the game
- towers start whole
- walls keep their normal HP but start randomly damaged, none destroyed: about half heavily damaged (10-35%), 29%
  damaged (40-75%), 18% fine (80-100%). The camp's Fortified Walls stay Fortified and the Allies'

The player starts with standard resources (200 food, 200 wood, 150 stone) and 4 villagers by the Town Center; a meta
upgrade adds 6 more just south of them.

Meta upgrades (docs/hub.md) hand more of these buildings to the player at the start.

The player's tech tree out of the box: everything of the Stone Age (villagers, House, Barracks and Clubman, Granary,
Storage Pit, Dock and Fishing Boat), and in the Tool Age only the Slinger, the Archery Range and Bowman, the Stable
and Scout, the Scout Ship, Light Transport and Trade Boat, the Market and Farm. No techs but Tool Age itself: every
other tech is a meta upgrade (the Bronze Age comes with reaching tier 3 in the hub). A kept Archery Range, Stable or
Market (meta upgrades) trains Bowmen, Scouts and builds Farms from the Stone Age: RoR switches those on with the
building, not the age (kept on purpose). Everything else still waits for its age.

The Allies' towers are the tier the player has unlocked: Watch Towers for now. The Walls upgrade hands over the Small
Walls only. The player
never builds walls or gates (RoR's gates come with walls); Watch Towers come with a meta upgrade. The player starts with
City Watch researched. The Allies age up when the player does.
Fish (not whales) hold twice their food, as fishing ships don't move on to the next fish they can see.

**Ages.** The City States (2) start in the Iron Age (eye candy). The Legion (3) starts in the Stone Age; its waves follow an
age clock by difficulty (docs/waves.md). It doesn't research the ages itself yet (to do: then its bases around the map
get stronger too, so leaving them makes them more dangerous).

**Waves.** The waves are the Legion's (3), spawned at the City States (2): a wave every 5 minutes on Standard, 3 on
Moderate, 2 on Hard, and they never end: the run ends when the Wonder falls, or when the player claims victory (a decision, up all run). How they grow is docs/evolving-waves.md
(the numbers in `scenarios/wave_table.py`). Wave 0 comes at once from the Capital, 2 Clubmen and 2 Slingers a lane, and
is sent as soon as it's in position; killing it puts a free Poor boon (any category) on each boon slot. Then waves
alternate: the Capital's two lanes (odd waves), then one from each of the Western and Eastern City States (even
waves). A sent unit standing idle (the road's end, or a tower it took down) is sent on to the Wonder.

Each lane rolls an archetype at the start (no two the same; a caption over a City States building at the lane names
it) and is an army of its own: a main and a support family on its archetype's paths. Before it spawns it takes a step
(grow, move a slot on along its path, or a shared upgrade or age up for the whole Legion). Siege and Priests come and
go from the Bronze Age on. Chat says every step.

**Staging.** Each lane is three rows of three tiles: where a wave spawns (the map edge), where it waits (a row
inside the spawn base) and where it attacks to (in the player's base). A wave spawns a row at a time and walks in,
in line formation, to its waiting row. Then it waits until it's sent, and marches out as one, in formation, straight
down its road. As soon as it heads out, the next wave walks in at the other City States. The Capital's lanes end on
the west and east of the Wonder; each side City State's lane ends beside the Capital lane on its side.

**Sending a wave.** When the waiting wave is in position, the "Send next wave" button on the Wonder comes on. A wave
is sent 5 minutes after the one before (the first at 5:00), or as soon as the player clicks; a click starts the 5
minutes again. Sending early brings later waves (and their ages) early. Sending a wave doesn't clear it: a wave is cleared when every unit
in it is dead. The player sees each wave's units wherever they go (not the rest of the Legion). A timer shows the time to the next send; the objective counts
defeated waves ("Waves defeated: n"), and chat names each one as it falls. Waves clump as they walk, so only
the middle tile of each row matters as a reference.

**Boons.** Each wave defeated (and each Legion base destroyed) gives one decision in the shop (`shop/`): two boon
categories on the Wonder, each from a different tag axis ("Combat boons", "Stable boons"; never a civ, civ type or
flag, and only a tag with at least 4 boons, playtest 2026-11-23), drawn by weight: a category's weight starts at 10 and goes up 10 each time the player picks it,
so the shop leans towards what they go for. Then a random boon of the one picked on each boon slot. The boons
(`crucible.boons`, trimmed to 63 on 2026-11-23) each have a rarity and the effects one level adds: a stat boon can be
bought 5 times, stacking (Assyrians' archer attack speed +8% a level), a big one (a production or research speed-up)
once. A boon comes at its next level only, back in the pool once that's bought. A percentage stops at its cap
(discounts 75%, research time 1 s, other production speeds +90%); each level past it adds an extra instead. Every
level costs its rarity's price (`RARITY_COSTS`: common 200 food, rare 300 food 200 gold, legendary 400 food 400
gold), less the Wonder's boon discount. Wave 0 gives the first level of a common boon on each slot, free. A boon
goes on a free button of the Wonder's first two rows (1-10); boons only stack once all ten hold an unbought one. The
Send next wave button is on 15, the two choices on 11 and 12. The boons bought aren't listed in game.

**Raids.** Each Legion outpost or district still standing sends raiding parties at the player, at random times: the
longer a run takes, the more raids. The bases also post units to hold places, send parties to harass the player's
villagers and patrol around them. Destroying a base stops all of that and gives one decision reward (one more shop
pick). Each base is an optional objective ("Destroy Western Outpost"; also Eastern Outpost,
Southern Farming, Mining and Military Districts, Western Military District): it's destroyed once all its buildings are, but its walls and farms (`scenarios/bases.py`).

**Invulnerable.** Everything of the City States (2) can't be attacked.

**Difficulty.** Higher difficulties start the Legion with bonuses or in a later age (more post-Iron waves), and make
raids more frequent and harder. The 5 minute wave timer never changes.

**Win and lose.**
- win: once the 9th wave is defeated, a Claim victory choice (its only button), left up until clicked: fight on as long as you like
- lose: the player's Wonder is destroyed

## Open

- the waves' contents by age, and how large the last wave is
- how many units a row is when a wave is bigger than one row, and how its rows follow each other
- what a raiding party is (size, units), and how raid frequency is drawn
- how the bases' behaviour is done: an AI (RoR ships AiBuilder_p, a scenario AI set by phases) or triggers
- player 5: where its units appear when the Allies send help
- what the decision reward is beyond one more shop pick
- the example had wave 4 in the Stone Age; read as Tool, since the age up comes at wave 3
