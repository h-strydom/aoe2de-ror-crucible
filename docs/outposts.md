# Outposts

Designed 2026-11-23 (playtest notes). The Legion's six bases on the arena (docs/arena.md, `scenarios/bases.py`)
come alive: the constant light pressure the player has to relieve, next to the waves' steadily growing pressure.
"Raid them or get raided."

Nothing is announced. An outpost acts every few minutes, by time alone; the player finds out by scouting or by
losing villagers. Destroying an outpost (its objective) stops everything it does.

## The outposts

| Outpost | Where | Land or sea | Attack waves from |
|---|---|---|---|
| Western Outpost | north-west island, 18-28, 40-54 | sea (docks) | the sea markers, by transport |
| Eastern Outpost | north-east island, 184-218, 2-46 | sea (docks, Town Center) | the sea markers, by transport |
| Southern Farming District | 94-116, 160-182 | land | the land markers |
| Southern Mining District | 69-90, 205-212 | land | the land markers |
| Western Military District | 6-26, 198-220 | land | the land markers |
| Southern Military District | 131-157, 198-215 | land | the land markers |

Every outpost can be reached on foot (land or shallows). Markers: 3 land (the south edge), 4 sea (north and west
edges), placed by hand (`scenarios/outposts.py`); each outpost uses the markers nearest it.

The four walled posts of watch towers aren't outposts: they don't act.

## What an outpost does, in order

Each outpost has a **state** and acts on a **tick**: every 2 to 4 minutes (random, so outposts don't act in step).
Each tick it does the first of these that applies.

1. **Turtle.** If any of its buildings or units took damage since its last tick, it pulls everything home: guards
   and bullies return and defend the base. It stays turtled until it goes a span (3 minutes) without damage, then
   goes out again. While turtled it doesn't grow.
2. **Defend itself.** Fewer defenders than its level calls for: it spawns more at the base.
3. **Bully.** A player villager or building at one of its spots (below): it sends a party at them, attack-moving onto
   the gatherers themselves (map hack: it knows where they are). Each tick the player stays, the spot's **pressure**
   goes up and the party with it, until the player leaves; pressure drains while the spot is clear.
4. **Guard.** A spot of its own without a guard squad: it sends one (2-4 units by level) to stand on it.
5. **Help.** All its own spots guarded: it sends a squad to another outpost's contested spot (spots overlap), or
   straight at a player gatherer outside the player's base (map hack).
6. **Attack.** Nothing above to do (defended, every spot guarded, none contested): it sends an attack wave at the
   Wonder.

Each tick it doesn't turtle, it also **grows**: its level goes up one, so the longer it's left alone, the more and
the better its defenders (a level adds defenders and moves its lines on within the Legion's age).

## Spots (what an outpost guards)

Found by the build, automatically (playtest 2026-11-23): every gold or stone cluster of 4 or more mines and every
hunt group within about 50 tiles of an outpost is one of its spots. A spot near two outposts is both's; that's the
overlap that lets them help each other. The build lists them (a table in this doc once built) so any can be struck or
added by hand.

## Units

Each outpost rolls an **archetype** as a wave lane does (Infantry, Bowmen, Cavalry, Phalanx, Chariots...,
docs/evolving-waves.md); its defenders, bullies, guards and attackers are that archetype's lines at the Legion's
current age. Outposts never roll upgrades of their own: they inherit the Legion's (shared), so an outpost's units
have every upgrade the waves have. They scale like the waves but less (2026-11-23): they grow slowly all run, and
faster while left alone (a level each tick they aren't turtled); the defender count and party sizes grow with the
Legion's age as well as the level.

**Rewards.** An outpost's attack waves award nothing. Destroying the outpost gives the boon choice (its objective,
`scenarios/bases.py`).

The sea outposts also keep **ships** around their islands, which defend the outpost and bully the player's docks and
fishing boats they can reach (map hack). With no player dock to bully, and nothing else to do, a sea outpost attacks:
its wave spawns loaded in Light Transports at its sea markers, sails to a beach outside the outpost and lands, then
attack-moves the Wonder. Two transports until two can't carry the wave, then the larger transport.

## Building it, a phase a playtest

1. **Checks** (crucible_check): XS reads a unit's HP (`xsGetUnitProperty(id, cUnitHitpoints)`), for the damage
   test; a transport created loaded ("Create Garrisoned Object") sails to a beach and unloads when tasked there.
2. **Self-defence**: archetype, level, growth, the tick, turtling on damage, destroyed outposts stop.
3. **Spots**: the guard squads, the bully and its pressure, help between outposts, harassing gatherers.
4. **Attack waves**: land outposts from the land markers; sea outposts' ships and transports.

## Open

- the numbers: defenders per level, the level cap, party sizes per pressure, tick length per difficulty
- the four walled posts: left as they are
