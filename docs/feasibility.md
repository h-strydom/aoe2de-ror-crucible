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
