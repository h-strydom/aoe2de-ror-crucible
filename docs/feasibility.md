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

### Catapult tower (towers that fire a Stone Thrower's stone)

`crucible catapult-tower`, 2026-11-09:
- **What works by trigger, for the whole tower type:**
  - the catapult projectile (656, arced);
  - reload and range;
  - splash width;
  - splash for enemies only (level 6).
- **Damage:**
  - **Triggers and XS can't add attack classes.** A tower's melee and building attacks stayed absent with every
    method (Modify Attribute Add/Set, Modify Object Attribute, Change Object Attack, `xsEffectAmount` Add/Set).
  - **What works:** setting the tower's existing pierce attack to 50. Stones then hit for 50, as pierce damage
    (targets' pierce armour applies), with no bonus against buildings.
- **The proper version is the data mod: verified.** A Guard Tower with the Stone Thrower's attack classes (50 melee,
  +140 vs buildings) written in read 0/50/140 in game, and its stones hit an elephant for about 46. Combined with the
  trigger settings above (projectile, reload, range, splash), that's a real catapult tower. In the final mod it would
  be its own unit, unlocked by a technology.
- **Two towers in the build menu: verified** (`crucible tower-build`).
  - The data mod adds a new Catapult Tower building (a Guard Tower copy with the Stone Thrower's attack, stone, range
    3-10 and enemies-only splash) and makes the upgrade-only Ballista Tower buildable.
  - Villagers built both, and both fired.
  - Build slots: 5 and 10 on the military page work; 14 and 15 don't show.
  - Left to do: its own text. The build button read "Guard Tower" (copied), and the built tower showed "Ballista
    Tower", the text behind string 7079. A new unit needs strings of its own.

## Ruins and artifacts

**Ruins and artifacts test results** (`crucible ruins-test`, 2026-11-09, about 50 s logged):
- **The King of the Hill trickle pays for the Monument only.** With the monument trickles (221-224) at 1:
  - the owner of the KotH Monument (826) got about 0.8 of each resource a second;
  - an Artifact Ruins owner got nothing, as did the player who captured a Gaia ruin.

  Ruins and the Monument share resource storage 14, but that isn't what the trickle counts.
- **Ruins trickle, the routes left:**
  - XS paying per ruin owned (the run ended before its first once-a-minute payment; the mechanism matches the
    verified wood-to-gold conversion);
  - a data mod "ruin" that is really a Monument copy with the ruins' look, so KotH's trickle pays it.
- **Artifacts can't garrison.**
  - Relic Carts (159) wouldn't enter a Barracks even with every garrison category allowed (garrison type 127).
    Artifacts are their own unit class (1), which matches no garrison category.
  - The units:
    - 159 is a "Relic Cart" with AoE2's relic look;
    - the AoE1 artifact is 25 "Artifact" (graphic "Artifact (Idle)"), with no garrison task at all;
    - 44 is the War Chest;
    - 944 and 1304 are Relic Carts with the artifact look, hidden in the editor.
- **Artifact boost, the routes left:**
  - "deliver" instead of garrison: XS spots an artifact next to one of your Barracks (`xsGetUnitPosition`) and
    switches the boost on (keep it there, or remove it as spent);
  - a data mod artifact in a garrisonable class with a garrison task, which may break its capture-on-contact.

**Round 2 results** (2026-11-09, 2:20 logged, Crucible Test Data picked):
- **A data mod Ruin Monument works.** A copy of the Monument (826) with the ruins' graphic, icon and name (unit 2751
  in the test mod) earns KotH's trickle exactly like the Monument: 8 of each resource every 10 s for its owner (P2
  and the P3 reference matched to the unit). Player 1 captured the Gaia one and started earning straight away. So
  "ruins that trickle" is a data mod unit plus the four monument trickles at 1.
- **Script pay per ruin works:** P4 got 1 of each resource every 10 s for its one Artifact Ruins. Any rate, any
  resource mix, per player; it doesn't need the data mod.
- **The AoE1 artifact (25)** looks right in game. It has no garrison button, as expected (no garrison task).
- **Delivery by proximity:** the script saw one, then both artifacts within 4 tiles of a Barracks and switched the
  boost on. (Whether training then sped up still has to be confirmed in game.)
- Still untested: a data mod artifact with a garrison task and a garrisonable class, for a real garrison button.

**Round 3 results** (2026-11-09): **artifacts can garrison once they're in a garrisonable class.**
- The data mod gave three artifacts the villager's "garrison into a building" task (action 3, class 3) and opened
  every Barracks to every category (`building.garrison_type` 127). The AoE1 artifact (25), still in the artifact
  class (1), stayed out. The copies in the infantry class (6) and the priest class (18) both garrisoned.
- The script found them with `xsGetGarrisonedUnitIds` + `xsGetUnitObjectId` (log: 2 garrisoned), and the boost
  worked: with the Barracks' work rate at 30, about nine 50-food units trained in 20 s.
- So "an artifact in a Barracks speeds up every Barracks" is doable: a data mod artifact copy in the infantry or
  priest class with a garrison task, plus XS. The class change has side effects to watch: class 6 takes infantry
  bonus damage and counts as infantry for targeting; priest class may draw anti-priest behaviour.
- Capture for the class copies (checked after round 4): Gaia copies in the infantry and priest class **join player
  1 as soon as the game starts**, wherever they stand. Only the real artifact (25) waits grey for a unit to reach
  it. Once owned, the copies still pick up artifacts: walking them next to the grey real one captured it. (The map
  was revealed; whether that's what hands them over is untested.)
  - So a class copy can't sit on the map as an artifact to find. The route: place the real artifact, and when a
    player captures it, swap it for the garrisonable copy (Replace Object, or XS). Untested.

**Round 5 results** (2026-11-09): the editor's per-unit **Capture** setting (`capture_flag` in the scenario,
format 1.59+) decides who joins at the start. A grid of Gaia artifacts, one row per flag, columns = real artifact,
infantry copy, priest copy; what had turned to player 1 at the start:

| Capture flag | Real artifact | Infantry copy | Priest copy |
|---|---|---|---|
| -1 Default | grey | **joined** | **joined** |
| 0 Never | grey | grey | grey |
| 1 Once | **joined** | **joined** | **joined** |
| 2 Multiple Times | grey | grey | grey |
| 3 Never (Gaia aggressive) | grey | grey | grey |

So setting the copies' flag to Never, Multiple Times or Never (Gaia aggressive) keeps them grey at the start.
Then a hoplite walked past the grey ones:

| Capture flag | Real artifact | Infantry copy | Priest copy |
|---|---|---|---|
| 0 Never | captured anyway | stayed grey | stayed grey |
| 2 Multiple Times | **captured** | **captured** | **captured** |
| 3 Never (Gaia aggressive) | captured anyway | turned hostile: walked up, attacked, was killed | was attacked down to 0 HP but never died |

- **Answer: place garrisonable artifact copies as Gaia with capture flag 2 (Multiple Times).** They then act like
  real artifacts: grey until a unit reaches them, captured on contact, and they garrison. No swap needed.
- The real artifact (class 1) ignores the flag for contact capture (Never and Gaia aggressive didn't stop it); only
  Once changed it (joined at the start).
- In a military class, flag 3 makes the copy a hostile Gaia unit. An artifact copy has hit points and can be
  attacked; the priest-class one sat at 0 HP without dying (no dying behaviour), so it's best kept out of fights.
  Whether enemies attack an owned copy in a real game is still untested.

**Round 4 results** (2026-11-09): **a stacking work rate bonus per garrisoned artifact works.** XS sets the
Barracks' work rate (13) to 1 + 0.5 × artifacts garrisoned, on each Barracks look (12, 20, 132, 498): one artifact
made every Barracks work at 150%, two at 200%, for training and research alike (checked by the player in game).
The same pattern should carry over to any building family (a Storage Pit's research, say).

Plan as written before the test:

| Idea | How | Status |
|---|---|---|
| Captured ruins trickle every resource | Ruins are Artifact Ruins (52), which change owner when captured. No native trickle is tied to them (and the trickles tested did nothing in RoR). XS: each second, count each player's ruins and pay resources, as the verified wood-to-gold conversion does; or a looping trigger with fixed amounts | Functions verified elsewhere; untested |
| An artifact cart garrisoned in a Barracks makes every Barracks train in 1 second | The moving artifact carts (159, 944, 1304) already have a "garrison into a building" task. Barracks hold 10 but admit garrison type 0 (as do the Temple and AoE2's relic-holding Monastery, so artifacts may follow a special rule); fallback: raise the Barracks' garrison type by trigger. XS checks each Barracks for a garrisoned cart (`xsGetGarrisonedUnitIds`) and sets every Barracks unit's Train Time (101) to 1 for that player, or raises the Barracks' work rate; it restores them when the cart leaves | Untested |

## Units from AoE2 and Chronicles, and exclusive techs

**How it works** (data checked 2026-11-09):
- The Chronicles civs (Achaemenids, Athenians, Spartans, plus Macedonians and Thracians) live in AoE2's main data
  file, and their unit ids start at 2101. Their sprites are in the shared graphics folder that RoR also reads (RoR's
  own Coustillier entry already uses an AoE2 sprite).
- RoR's data file keeps AoE2's unit ids but reuses some slots (38 is AoE2's Knight and RoR's Cavalry), and about a
  third of its graphic ids point at different sprites. So a ported unit needs its graphics, sounds and linked units
  (corpse, projectiles, alternate form) copied and renumbered where RoR's ids differ: `port.py`. No sprite files are
  copied; the mod refers to the player's own install.
- Chronicles' "pick one" techs are plain techs whose effect disables every tech in the set, itself included (command
  102), e.g. Dekate / Taxiarchs, Oligarchy / Democracy / Tyranny. RoR's data has the same fields and uses 102 itself.

**Round 1** (`crucible port-test`, 2026-11-09): Knight, Crossbowman, Chronicles Hoplite and Immortal ported to the
Barracks; three exclusive Barracks techs.
- **Ported units work**: standing, walking, attacking, dying, projectiles, training. Porting the four took 20 new
  graphics; the rest already matched.
- **Portraits are wrong**: `icon_id` indexes RoR's own icon set and RoR doesn't fall back to AoE2's icon files. The
  Knight (icon 1) showed RoR's priest; the Chronicles units (icons 621, 625, past RoR's set) were black. Fix: point
  each at a fitting RoR portrait. (Copying Chronicles icon art into a mod is not an option.)
- **The Immortal's ranged switch turned it into a fishing ship**: its alternate form is a unit link (genieutils calls
  the field `nothing`), 2174, which is RoR's Oystering Ship. The port has to follow that link too.
- **Exclusive techs are exclusive, but queueing beats it**: you could queue two (in one or two Barracks) and get both,
  since the cost is paid at queue time and the disable only lands when one finishes; cancelling a queued one after
  another finished put them back in the UI. Chronicles has nothing extra in its data against this (Dekate's other
  resources are aura flags). Next: a "token" cost, 1 of a spare resource the player has exactly 1 of.

**Round 2** (2026-11-09):
- **The Immortal's alternate form works** once the port follows the `nothing` link (it switches to ranged and back
  as an Immortal). `nothing` is 0 on units without one, so 0 must not be read as unit 0.
- **A tech cost in a spare resource is ignored**: 1 of resource 30 ("Unused Resource 030"), with every civ starting
  with 1, wasn't shown in the cost and didn't stop queueing. Tech costs seem limited to the four stockpile resources.
- Next: a script. `xsGetTechState(tech, p)` reports queued (4) and researching (2); when one is queued, disable the
  others (`xsEffectAmount(cModifyTech, tech, cAttributeDisable, 0, p)`), re-enable on cancel, and refund a second
  one that finishes anyway.

**Round 3** (2026-11-09): **the script didn't stop it.** Disabling the others with `xsEffectAmount(cModifyTech, ...,
cAttributeDisable)` when one was queued didn't block them: all three could be researched in a row (the refund for
the second and third did fire). In Chronicles, hovering one draws a red cross over the other, the other can't be
started while one researches, and it vanishes when the first finishes. The data shows no extra link, but the tech
`type` differs: Chronicles' unique techs are 0, ours were 9 (copied from RoR's Axe). 33 is the type of switchable
settings that also disable each other (the Market's trade settings, the Athenian governments), not a one-time pick.
Round 4 compares type 0 and 33, script removed.

**Round 4** (2026-11-09): **neither type behaved like Chronicles** (type 0 at the Barracks, type 33 at the Town
Center): no red cross, the others could still be started. Conclusion: Chronicles' exclusive-tech interface (red
cross on hover, blocked while one researches) isn't in RoR, or depends on something outside the data. **Native
exclusive techs in RoR: not possible.**
- What does work: the techs disable each other once one finishes (data, command 102), and a script can refund any
  extra one that finishes (round 3: the refund fired). That keeps the outcome exclusive, but the player can still
  queue and pay for the others first, so it's clumsy.
- For Crucible's "pick one" choices, use what's verified instead: the two-option decision popup, walk-on pads, or
  buttons that a script removes once one is picked.

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



## Boon shop: runtime checks (`crucible check`, 2026-11-10)

- A boon tech placed on the Wonder at build time researches with its rarity price; its effect applies (Camel Riders
  x1.15 HP).
- **Moving a boon onto the Wonder at runtime works**: an unplaced boon (no building) appeared on Wonder button 2 when a
  trigger ran Change Technology Location, and researched (elephants 600 -> 750 HP).
- **Live renaming works**: the two choice buttons on row 3 were renamed by XS every 3 s ("Stable"/"Economy", with a
  counter); both could be researched, as nothing hides the other one yet.
- The check started in the Iron Age, which researches Nobility (cavalry +15% HP) for free, so camels started at 144;
  the check now starts in the Stone Age.
- **A researched choice never comes back on its own** (the data's repeatable flag doesn't help), but **re-enabling it
  by trigger (Enable/Disable Technology) does**, for a researched and a disabled choice alike. So the shop reuses one
  pair of choice techs every wave: on a click, the other is disabled (locked in); when the pick finishes, both are
  re-enabled and renamed to the next two categories.
- A dummy unit trained at the Wonder (a button that never disappears) works, but it needs population room and gives
  the Wonder a gather-point button at row 3, column 1, where choice 1 sits: not used.
- **The one-pair choice cycle works** (3 rounds): clicking one choice disables the other at once (locked in), and when
  the pick finishes both come back with the next round's names on the same buttons. After the last round the
  re-enable still fired, so round 3 came back with nothing locking it: the real shop must not re-enable after the
  last pick (or disable both until the next wave).
- **XS alone places a boon** (`xsEffectAmount(cModifyTech, tech, cAttrSetLocation, 276, p)` then `cAttrSetButton`,
  plus enable): an unplaced boon appeared on the Wonder button asked for, and researched. **XS disables one**
  (`cDisableTech`, `cAttributeDisable`): its button went. But **XS doesn't re-enable it** (`cAttributeEnable`): the
  button stayed gone. (The trigger Enable/Disable Technology does re-enable.)
- Bringing a boon back after XS disabled it: **the trigger Enable/Disable Technology works**; XS setting its state to
  Ready (`cModifyTech`, `cAttrSetState`) doesn't; XS moving it to no building (`cAttrSetLocation -1`) doesn't even
  take it off the Wonder. So the shop places boons and disables choices from XS, and re-enables the choice pair by
  trigger (two triggers in all, none per boon).
- **The shop works in game** (`src/crucible/shop/`, 3 slots, 4 choices a wave, 22 boons): category choices named with
  their counts, lock-in on click, one boon stacked on every row-1 slot per pick (the top one researches, then the next
  shows; all 22 stacked on 3 slots), boon hover text, choices counted down with the next pair shown at once, and
  "no boons left" at the end.

## Compiled boons (`crucible check --test compiled`, 2026-11-10)

All 101 boons compile (`src/crucible/bonuses/compile/`), copying how RoR's own civ bonuses address each stat. Checked
in game: villager food cost (attribute 103, 50 -> 40), population room on a Town Center and a tower (first resource
storage, attribute 21, +4 each), class armour (+1/+1 on villagers) and class attack (+1 on archers), priest range,
house HP across ages, farm food (resource 36: 375), Storage Pit tech costs (-40%). Multiplying the research time
resource (86) did nothing: Toolworking wasn't faster.
