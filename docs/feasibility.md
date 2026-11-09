# What we can and can't get away with

Ideas for Crucible, and what Return of Rome allows. Each entry says how it's done (**triggers**, **XS** scenario
script, or the **data mod**) and how sure we are: **verified** in game, **data** (read from the game files),
or **unverified**. Verified engine facts also go into aoe-agent-editor's `src/aoe2ed/docs/engine-facts.md`.

## The data mod

- **Campaigns can depend on a data mod.** **Verified** (`crucible test-mod`, 2026-11-09).
  - Picked in the campaign screen's Data Mod dropdown. "Scenario Default" loads the mod the scenario was created
    with, and picking another shows a warning.
  - Installed Mods marks data mods with a gear.
  - Still open: which scenario field records the data mod, so our scenarios can name it by default.
- **Only one data mod at a time.** **Verified**: a mod holding only `dropsites.json` showed up as a separate data
  mod. So everything (data file and JSON files) ships as one mod.
- **We edit RoR's data file with genieutils-py.** **Verified.** It writes the file back identically when unchanged,
  and our edits (hit points, civ bonuses, drop sites, tasks) all took effect.

## Units and buildings

| Idea | How | Status |
|---|---|---|
| A building trains a unit it normally doesn't (Scouts at the Barracks) | Triggers: Enable Object, then Modify Attribute Train Location (42) and Train Button (43) | **Verified** |
| Extra drop sites (Houses take wood) | Data mod: `dropsites.json` entry **and** the building on each villager job unit's drop site list (`bird.drop_sites`). The JSON alone shows the cursor but villagers go idle | **Verified** |
| A civ with no bonuses, on an existing architecture | Data mod: strip the civ's tech tree effect to its disables and empty its civ-only techs (Greeks tested) | **Verified** |
| Unit stats (hit points etc.) | Data mod, or triggers (Modify Attribute) | **Verified** (data mod) |
| AoE2 civ bonuses in RoR | Data mod (proper bonuses), or XS/triggers at the start for most stat and economy bonuses; behaviour-based ones need the data mod or can't be done | Data; unverified |
| Chronicles content in RoR | Ideas and stats only. Its art is paid DLC and can't be redistributed | Not allowed |

## Bonus damage

- **RoR has AoE2's attack and armour classes.** *Data, 2026-11-09.*
  - Slingers: +3 vs archers (armour class 15) and +3 vs class 13 (stone defense), with 3 pierce armour.
  - Chariot Archers have archer armour −2, so they take +5 from Slingers.
  - Camel Riders get +8 vs cavalry (class 8), while Chariots have cavalry armour 4.
  - Stone Throwers get +140 vs buildings (class 11).
  - So Slingers already work as mild skirmishers. (AoE2's Elite Skirmisher: +4 vs archers, more vs spearmen, 4 pierce armour.)
- **Bonuses can be changed:** triggers (Modify Attribute Attack/Armor with an armour class, per unit type) or the
  data mod (permanent; can also add new classes). Unverified in game.
- **A bonus only lands if the target has that armour class.** So who counts as what is decided by armour classes,
  not unit type.
- **Hoplites vs cavalry:** give Hoplites an attack against class 8 (cavalry). Today only Camel Riders have one (+8).
  Cavalry and Scouts have class 8 armour 0 (full bonus); Chariots have 4, which blunts it.
- **Cavalry archers count only as archers:** they carry both archer (15) and cavalry (8) armour:
  - Horse Archer 0/0;
  - Elephant Archer 0/0, plus elephant class 5;
  - Chariot Archer −2/4.

  Remove their class 8 entry, and cavalry bonuses (camels, a Hoplite bonus) skip them while archer bonuses
  (Slingers) still apply. Data mod: delete the entry. Triggers: probably, via the Remove Armor Type attribute (164;
  Add Armor Type is 160), unverified.
  - Caveat: armour only. Their unit class stays cavalry archer (36), which AI scripts, class-wide civ bonuses
    (Assyrian archer fire rate covers classes 0 and 36) and garrison rules use. The data mod can change the class
    too, with wider knock-on effects.

### "Counts as" buffs (emergent combos)

The idea: a buff makes a unit also count as another type, e.g. Hoplites count as cavalry. They take cavalry upgrades
and civ bonuses, and also take extra damage from camels. Removing an armour class makes a unit immune to the bonuses
aimed at it. That splits into two engine pieces:

| Piece | How | Status |
|---|---|---|
| Vulnerability: take (or stop taking) a class's bonus damage | Triggers: Add Armor Type (160) / Remove Armor Type (164), per unit type for a player, any time in a run | Trigger attributes exist; unverified |
| Benefits: cavalry upgrades and cavalry civ bonuses | **Not by class:** a unit has one class, and triggers/XS can't change it (the data mod only permanently, and that's a swap, not an "also"). Instead **mirror** the effects: read from the data file which techs and civ bonuses touch cavalry (we already parse them for `aoe2ed.civs`). When the buff is picked, apply the ones already active to the Hoplite with `xsEffectAmount`, then each later one as it's researched | Possible; unverified |

Limits:
- **Still infantry underneath:** anything that checks the real class (AI targeting, garrison rules, class filters in
  triggers) still sees infantry.
- **Ability-like bonuses:** mirroring covers stat changes (cost, speed, HP, attack, armour, fire rate), which is
  almost all RoR bonuses.

## Combat tuning

All trigger attributes (Modify Attribute, per unit type for a player) or data mod. Values read from RoR's data,
2026-11-09.

**Combat test results** (`crucible combat-test`, 2026-11-09). Changes were made per unit (Modify Object Attribute).
Some units attacked outside their lane, so the lanes aren't perfectly clean:
- **Friendly Fire Damage (119) doesn't switch friendly fire off**, in any form: one unit or the whole type, 0 or
  0.01, or on the projectile. Your hoplites lost the same hit points in every lane (friendly fire test round 1). The
  attribute reference calls it the "blast damage multiplier to non directly targeted units", so it isn't specific to
  friendly units.
- **The real switch is Blast Attack Level (44):** a base level 0-3 plus combinable flags (ugc.aoe2.rocks):
  - 4 = damage enemy units only;
  - 8 = ignore friendly fire;
  - 64 = damage falls off with distance;
  - 128 = a narrow cone in front.

  Stone Throwers are level 2. RoR's data already uses 6, 10, 34, 66 and 138.
- **Verified (friendly fire test round 2): + 4 switches friendly fire off; + 8 does nothing in RoR.**
  - Level 6 left your hoplites untouched while the enemy target died, on one Stone Thrower (Modify Object Attribute)
    and on every Catapult (Modify Attribute).
  - With the Catapults the splash still hit the enemy beside the target (50 → 33), so splash still works on enemies.
  - Level 10 hurt your hoplites as much as the control did.
- **Splash width 3: works.** All four outer targets, 2 tiles from the centre, were hit and died within 25 s.
- **Minimum range 0: works.** The changed Ballista hit the enemy beside it (600 → 0); the control's target stayed
  at 600.
- **Projectile swaps: work.** The Catapult firing a ballista bolt visibly fired a bolt with normal catapult damage
  (about 58 per 5 s). The fast, flat projectile looked like a cannon shot (user's view).
- **"Melee ranged" units: work.** The Hoplite with range 3 attacked from range (user's view). Its target and the
  control's both took damage in the log, from units straying out of their lanes.
- **Trade shares: work.** At 25% each, a 24-gold trade paid 13 gold plus 3 food, 3 wood and 3 stone. Each share came
  out at about half the setting. The trade boat's panel still shows only gold; the extra resources arrive on delivery.

| Idea | Setting | RoR today |
|---|---|---|
| Siege without friendly fire | **Verified:** Blast Attack Level (44) + 4 ("enemy units only"), per unit or per type. Not + 8, and not Friendly Fire Damage (119): both do nothing for this | Stone Thrower, Catapult 2; Heavy Catapult 1 |
| Bigger splash | Blast Width (22); Blast Attack Level (44) decides who splash hits | Stone Thrower 0.8, Catapult 1.25, Catapult Trireme 1.0 |
| Trampling melee units | Blast Width plus a Blast Attack Level that splashes (Hoplites are at 3: none) | None in RoR |
| Projectile speed and arc (cannon-galleon style) | The projectile is a unit: Movement Speed (5) on it, Projectile Arc (69) | Catapult projectile 656: speed 3.5, arc 0.5. Bolt 367: 4.1, arc 0.02. Stone Throwers and Catapults share 656, so changing it changes both unless the data mod gives one its own copy |
| Minimum range | Minimum Range (20) | Ballista, Stone Thrower, Catapult 3 |
| Range | Maximum Range (12) | Melee 0, Bowman 5, Catapults 10-12 |
| "Melee ranged" units | A melee unit (no projectile) with Maximum Range above 0 should hit from that distance | Untested; the oddest one |
| Accuracy | Accuracy Percent (11), Attack Dispersion (64) | Siege and archers 100 |
| Traders return some of every resource | Player attributes Trade Food/Wood/Stone Percent (251-253) | AoE2 civ bonuses use them; RoR may ignore them like the trickles. Fallback: XS reads trade income (101) each second and pays shares, as the verified wood-to-gold conversion does |

## Resources

Resource test scenario (`crucible resource-test`, 2026-11-09; 6.5 minutes logged). Each stone mine started at 350.

| Idea | How | Status |
|---|---|---|
| Stop gathering (work rate 0) | Triggers: Modify Attribute work rate (13) on the job units (stone miners 124/220) | **Verified:** miners at work rate 0 gathered nothing and the mine stayed at 350 |
| Gather faster (stone 500% faster) | The same work rate, ×6. Data: miner 0.52, lumberjack 0.55, fishing boat 0.40 | Mechanism verified (0 works); ×6 untested |
| Resources last longer, more per unit | Triggers: Modify Resource on the player multiplier the gather task uses: Stone Bonus (79), Gold Bonus (47), Wood Bonus (189), Food Bonus (190), Fishing Productivity (219). It's the game's own "Resources last +X%" setting (RoR's lobby techs: Gold Bonus 1.15 to 4.0) | **Verified:** Stone Bonus 10 gave about 10 stone per unit the mine lost. At 6:00 it had 731 stone with 274 left in the mine, against the control's 299 stone with 50 left. Income was 2.4× (each trip fills faster, but walking stays the same) |
| Multiplier 0 | — | **Verified: ignored.** Stone Bonus 0 played exactly like the control (same income, same depletion) |
| Depletion per gatherer (ships don't deplete fish, villagers do) | Villager fishermen (56/57) and fishing boats share Fishing Productivity (219). Data mod: point the boat's gather task (`resource_multiplier`) at an unused player attribute and set that very high: boats' fish last (almost) forever, villagers' don't | Data; the multiplier part is verified, the repointing isn't |
| Swap what a gather takes (`resource_in`) | Data mod | **Verified: not what decides it.** Boats told to take wood from fish still took fish and paid food, so the target decides what's gathered. `resource_out` (what's paid) is untested |
| Generation (flat income) | Triggers: Modify Resource Food/Wood/Stone/Gold Generation (230-233) | **Verified: per minute.** Food Generation 60 gave exactly +1 food a second; Wood Generation 1 gave +1 wood a minute. Good for hub perks |
| Military Food Trickle (287) | Triggers | **No effect in RoR:** 3, with 5 hoplites, gave no food |
| Chopping gives gold (266) and the other native "gather X, also get Y" ones (241, 236, 267, 298) | Triggers | **Chopping gold had no effect in RoR:** 33 gave no gold. RoR's and AoE2's lumberjack tasks are identical, so it's engine-side and seemingly off in RoR. The others are untested and probably the same |
| Any ratio (chopping gives a bit of stone) | XS: each second, read total wood gathered (167), pay a share as another resource (`xsSetPlayerAttribute`) | **Verified** (round 2): 10% of wood as gold, exactly (212 wood, 21 gold) |
| A pile that holds a different resource (gold trees, stone berry bushes, gold fish) | Triggers: Type First Storage (168), per object (Modify Object Attribute) or per type (Modify Attribute) | **The switch takes, but changes nothing gathered.** Piles reported gold/stone after both per-object and type-wide changes, so a type-wide change does reach objects already on the map. But lumberjacks on gold trees got wood, foragers on stone bushes got food, and the boat on a gold fish got food. **The gatherer's task decides what's paid**, not what the pile holds (round 2) |
| Special resources that really pay out differently (a "gold tree", whales with gold) | Data mod: a new resource object, plus a gather task on the gatherer aimed at that object's id (tasks target a class or a unit id) that pays the other resource (`resource_out`). Fishing boats pay food from fish through `resource_out`, so that field is what decides the payout | Data; unverified |
| Animal decay | Disable Animal Decay (292), decay rate (12) | Untested |
| Reading a pile's remaining amount | XS `xsGetUnitProperty(id, cUnitAttributeHeld)` | **Verified** (mines read 350 at the start) |

## Garrisons

- **Garrison arrows:** verified with triggers alone. A tower needs three settings, and the units one:
  - Maximum Total Missiles above 1 (107);
  - Secondary Projectile Unit 505 (65), which is the extra-arrow projectile;
  - a garrison type that admits the unit (30);
  - the unit needs garrison firepower 1 (130).

  RoR ships with arrow limit 1, no secondary arrow, villagers-only towers and firepower 0 for every unit. As in
  AoE2, villagers and archers add arrows; hoplites (firepower 0) don't.
- **Soldiers garrisoning in buildings:** needs the data mod. **Verified.** RoR soldiers can only board transport
  ships; the mod copies the villager's "garrison into a building" task onto foot soldiers.
- **Garrison slots per building:** triggers set capacity (2) and who may enter (30; 1 = villagers). *Data:* towers
  hold 5 villagers only; Barracks, Archery Range, Stable and Academy hold 10 but admit nobody (type 0); the Town
  Center holds 15 villagers.

### The garrison upgrade system (Empire Earth style)

The design: garrison villagers into a building for a bonus that depends on how many are inside. Slots are fixed
per building (Barracks 2, tower 5); only villagers may enter. The population they use is given back while they're
inside, and then they can't come out.

| Piece | How | Status |
|---|---|---|
| Villagers only, fixed slots | Triggers: capacity (2) and garrison type (30) per building type | Towers verified; others data |
| Tower: +1 arrow per villager | Garrison arrows (above): live, follows the number inside | **Verified** |
| Barracks: +100% training per villager | **No per-building way.** Training speed is the building's work rate (13). XS can only change it for every building of a type at once (`xsEffectAmount`), and triggers only for buildings placed in advance. Options: per player (every Barracks shares the bonus; exact with one Barracks), or Barracks variants in the data mod swapped by XS (risky: garrison, queue, finished state) | Limitation |
| Population back | XS: count villagers in bonus buildings each second, raise the player's bonus population (`xsSetPlayerAttribute`) by that number | Functions exist; unverified |
| No ungarrisoning | XS: track who went in (`xsGetGarrisonedUnitIds`) and send anyone who comes out straight back (`xsTaskUnits`), or remove them. Only needed if the population trick works; without it, ungarrisoning is allowed | Functions exist; unverified |
| Sacrifice for good (unit gone, building upgraded) | XS can remove a garrisoned unit (`xsRemoveUnit`, population back at once). But XS can't set one building's arrows or speed, so a permanent per-building upgrade needs building variants swapped by XS | Limitation |

Useful XS for this: `xsGetPlayerUnitIds`, `xsGetGarrisonedUnitIds`, `xsGetUnitPosition`, `xsRemoveUnit`,
`xsTaskUnits`, `xsSetUnitCaption` (label a building, e.g. "Sentry Tower (3/5)"), `xsSetPlayerAttribute`,
`xsEffectAmount`, `xsModifyUnitTasks` (edit one unit's tasks). XS has no setter for one unit's attributes.

## Map and mission tricks (the engine test map; not yet played)

| Idea | How | Status |
|---|---|---|
| Walkable but unbuildable ground | Terrains with no buildings: Rock 1 (40), Quicksand (46), Bogland (101); most blocked: Beach, Swamp, Shallows, Ice | Data; unverified (speed penalties?) |
| Spawn safe zone | Looping trigger: Enable Unit Attackable for the whole map, then Disable in the zone | Unverified (splash damage?) |
| One object's resources (200 food on a bush) | Modify Object Attribute: Amount of 1st Resource Storage (21), over an area or chosen objects | Unverified |
| March in formation | Task Object Line/Box/Staggered/Flank Formation, then Move with a group command; AI `up-target-point` | Unverified |
| More than two choices | The decision popup has exactly 2; use walk-on pads, buttons on a building (custom techs), or chained popups | Popup verified |


