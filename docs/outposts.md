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

How it lands (crucible check, 2026-11-23, decided): ships obey XS orders under the immobile AI, and loading works (XS `cUnitGarrisonedInId`, or the trigger Create Garrisoned
Object), but no transport puts anyone ashore when told to (every way tried). So it lands as RoR-Reimagined's Egypt 5
landing (2026-11-08): the ship sails to the beach (Task Object), and once it's there (objects in area) its party is
created on the beach and the ship sails off. With a loaded ship, its passengers are removed as their copies appear,
so sinking it at sea still kills them.

## Building it, a phase a playtest

1. **Checks** (crucible_check): XS reads a unit's HP (`xsGetUnitProperty(id, cUnitHitpoints)`), for the damage
   test; a transport created loaded ("Create Garrisoned Object") sails to a beach and unloads when tasked there.
2. **Self-defence**: archetype, level, growth, the tick, turtling on damage, destroyed outposts stop. Built
   2026-11-23 (`scenarios/outposts.py`, numbers at its top): 3 defenders each at the start; a turn every 2-4 minutes
   (the first at 1-2); +1 level a turn left alone, +0.3 harassed; defenders 3 + level / 2 + 2 an age (+2 a
   difficulty step), 25 at most, 3 more a turn; harassed = any HP lost by its buildings or defenders, or a defender
   killed, and the defenders attack-move to the spot; turtled for 3 minutes after. Units: the archetype's first
   paths, the line at (level / 4 + the Legion's age) along them. Debug chat on for the playtest (`DEBUG`).
   Playtest 2026-11-24: fine as far as it went, but the garrisons were too small and in a clump, and hit, they
   walked to where they were hit and back until they died; outposts never attacked or harassed.
3. **Spots** and 4. **Attack waves**, built together 2026-11-24 (`scenarios/outposts.py` works out the map's part,
   `scenarios/outposts.xs` is the runtime, numbers at the top of outposts.py):
   - garrison: 4 times phase 2's (12 each at the start), spread over 16 posts round the base's buildings; turtled it
     tops up to 8 times, 4 more every 15 s; at most 120 land units (and 60 ships). Sea outposts: half of it ships
     (Scout Ships, then War Galleys, Triremes and Catapult Triremes by age and level) on 8 water posts round the
     island; the ships go for the player's ships and docks within 60 tiles (bullying the docks) whenever there are
     any;
   - hit (its buildings, garrison or ships), it turtles: everyone out comes home and joins the garrison, and every
     2 s the garrison attack-moves at the player's unit nearest the base (within 25 tiles); with none left, back to
     the posts;
   - the map hack: every 2 s XS lists the player's units by type (villagers, soldiers, ships, docks);
   - spots: the build found 50 (gold, stone, hunt; none within 30 tiles of the Wonder), each the spot of every
     outpost within 50 tiles (the Eastern Outpost has none). A spot is contested while the player has a unit within
     8 tiles; its pressure goes up 1 every 30 s contested (10 at most), down 1 while clear;
   - each turn, not turtled: grow, top up the garrison (12 at most), send the garrison back to its posts, then the
     first of: bully its most pressured contested spot (2 + 2 a pressure + the age, 16 at most: they chase the
     player's units off it, then stay as its guard); guard an unguarded spot of its own (2 + level / 4 + the age, 8
     at most: they stand on it and fight whoever comes); help at any contested spot within 60 tiles; raid the
     player's villagers outside the base within 60 tiles (they chase gatherers, then come home); a sea outpost with
     player ships or docks in reach leaves it to its ships; else an attack wave (3 + level / 2 + 2 an age + 2 a
     difficulty step, 30 at most) at the Wonder: land outposts' appear at their nearest land marker, sea outposts'
     in transports at their two sea markers (Light Transports, 5 each, while two carry it; else Heavy, 10), which
     sail to a beach 10-30 tiles from the outpost nearest the Wonder, land their party (the fake) and sail off;
   - debug chat says each turn and what it did (`DEBUG`).

   Playtest 2026-11-24 (standard): the aggression felt right for Hard; the garrisons spawned from thin air at their
   posts and overspawned once the player left; they clumped; 4 times the garrison was right for Moderate, 6 for Hard;
   old units stayed in the garrison; far too many ships, stacked; the Western Outpost's transports landed in a
   strange spot; transports sank when they left (killed, not removed).
5. **Markers, buildings and rounds**, rebuilt 2026-11-24 to the user's design:
   - markers placed by hand on the arena (player 4's, taken off the map by the build): Priests where the garrison
     stands about (5 an outpost), Scouts the spots it guards (13; a spot belongs to the nearest outpost its units can
     walk to, and gets 2 to 6 guards by its resources, a guard a 1000, + the Legion's age), Fishing Boats where a sea
     outpost's ships keep (3 each), Kings where its transports land (the 3 nearest it, one at random a wave);
   - units come out of a free tile by one of the outpost's buildings in turn (any building for land units, a dock for
     ships); a destroyed building makes none, so with its docks gone a sea outpost has no more ships;
   - behaviour: the garrison wanders round its post (every third unit patrols between two posts), spot guards wander
     on their spot, ships round their spot; each takes a step every 6-14 s;
   - each turn (2-4 minutes on Hard, longer on easier difficulties): turtled (hit in the last 5 minutes) and the
     player still near (25 tiles), it defends (the garrison hunts) and makes nothing; turtled and the player gone, it
     bolsters (2 every 30 s towards twice its garrison); not turtled, it makes nothing while the player is near, else
     tops up 3 and sends guards to the first of its spots the player is on (a bigger party the longer the player
     stays) or that is short of guards; every spot guarded, an attack wave. Spot guards fighting away don't turtle it;
   - the garrison's base (3 + level / 2 + 2 an age) times 2, 4 or 6 by difficulty (Standard, Moderate, Hard), twice
     that turtled; parties and waves 50, 75 or 100% (Hard is what Standard was);
   - units of lines the outpost has moved on from leave the garrison first: as spot guards, and from land outposts in
     attack waves;
   - sea waves: transports (and an escort ship for every 6 in the wave, + 1, 4 at most) start 3 tiles in from a sea
     marker, sail to the water by a landing, land the party on the King's tile (the fake), then sail back to the
     marker with the escorts, where a looping trigger removes them (unverified: removal by type in an area failed on
     Gaia bushes once).
6. **Second playtest (Hard, 2026-11-24)**: turtling 5 minutes was too long, turns too slow, no raids, most spots
   with 1 or 2 guards at 45 minutes, the first land attack at 15 minutes, the garrison slow to swap lines. Now:
   - turtled 2 minutes after the last hit;
   - turns every 90-150 s divided by TURN_SPEED (75, 100, 160%) and by the power;
   - the power: +3% a minute (400% at most), +25% for each outpost destroyed (and each survivor gains 2 levels);
     it scales parties, raids, waves, turns, turtled top-ups and the garrison's top-up a turn;
   - raids: a turn sends one (25, 35, 50% of turns) on the player's villager nearest the outpost outside 22 tiles of
     the Wonder; raiders chase villagers near where they were sent, then go home to the garrison;
   - a spot the player is on gets a party at once, again every 45 s (less with the power) while the player stays;
   - spots want 3 to 8 guards (+ the age, times the aggression and the power), refilled below 75%, two a turn;
   - attack waves back to their first size (2x was massive, playtest 2026-11-25; 60 at most), never before FIRST_WAVE (900, 750, 600 s), and one comes every 5
     minutes (less with the power) even while spots are being refilled; at least 60 s between any two outposts'
     waves (they had piled up at the spawn, playtest 2026-11-25);
   - when its slots' units or its ship move on, its units swap where they stand, one for one (the old ones die).

## Open

- the numbers: defenders per level, the level cap, party sizes per pressure, tick length per difficulty
- a sea outpost's outdated units: they only leave as spot guards (only the Western Outpost has a spot on its island)
- the four walled posts: left as they are
