# AoE2 DE mechanics worth bringing into Crucible

Survey of 2026-11-09: what AoE2's data file uses that Return of Rome's never does, read straight from both files
(effect types, the unit attributes techs change, and unit task types). RoR runs on the same executable, and every
AoE2-only setting tried so far has worked in RoR (blast levels, garrison arrows, projectile speed, data mod attack
classes, ported Chronicles units), so these are likely to work too. None of them is tested yet.

**How each gets tested**
- **Trigger**: a Modify Attribute effect on a RoR unit in a scenario; no data mod needed.
- **Data mod**: a unit task or tech that only exists in data (copy the task onto a RoR unit, or port the AoE2 unit).

## Most promising (boons and curses with emergent play)

| Mechanic | AoE2 example | Crucible use | Test |
|---|---|---|---|
| Regeneration rate (attribute 109) | Cavalry / villager / ship regeneration civ bonuses | "Field medics": units heal over time | Trigger |
| Damage reflection (118) | Khitans' Lamellar Armor | Thorns: attackers take a share of their hit | Trigger |
| Area damage (115) | Taxiarchs, Vadhavadha | Melee cleave: hits splash to neighbours | Trigger |
| Bonus damage resistance (24) | Citadels, elephant resistance bonus | Counter-proof units ("ignore 50% of bonus damage") | Trigger |
| Add attack type (161) | Varangians team bonus | A unit gains a new bonus class mid-game. Our earlier finding: Set/Add can't create an attack class; 161 is a separate attribute made for exactly that, so it may get round it | Trigger |
| Dead unit id (57) | Units that leave something on death | "Splits on death": a unit leaves a smaller unit, a pickup or a ruin when it dies | Trigger |
| Charge attack (task 133, attributes 59-63, 125) | Chronicles Hoplite and Companion Cavalry, Coustillier | Shock troops: a charged first hit for big damage, recharging over time | Data mod (the ported Elite Hoplite has it) |
| Aura (task 155) | Strategos, Centurion, Caravanserai, Chronicles heroes | A commander or a building that buffs everything nearby | Data mod |
| Loot (task 154) | Units that gain resources from kills | Plunder: kills pay gold, a roguelite economy hook | Data mod |
| Movable drop site (task 153) | Mule Cart | A wagon that follows the army as a drop-off | Data mod (port the Mule Cart) |
| HP transform (task 158) | Jian Swordsman | "Berserk": below X% HP the unit turns into a stronger form | Data mod |
| Spawn unit (effect type 7) | Free relic, free villager civ bonuses | A tech or boon that drops a unit at a building | Data mod tech |
| Effects on enemies (effect types 21 and 26; 11 and 12 are team) | Hun Atheism (enemy relic/wonder victories take longer), Razing Bounty | **Curses**: a boon that makes the enemy's costs or times worse; team buffs for allied AI | Data mod tech |

## Useful knobs (simple, trigger-testable)

| Mechanic | Use |
|---|---|
| Food / gold / stone cost (103, 105, 106) | Per-resource discounts, e.g. "military costs no gold" |
| Garrison heal rate (108) | Buildings as hospitals |
| Search radius (23) | Units that spot and engage from further away |
| Conversion time (111, 112) | Priest boons and curses (RoR's priests are a big deal) |
| Trailing unit (145-147) | Curare: units leave a trail, e.g. a poison or fire patch |
| Combat ability (63) | Bit flags for special combat behaviour (ignore armour and the like); needs mapping |
| Available / disabled unit flag (126, 127) | Switch hero units on and off |
| Training count / special ability (81) | Batch training, unit specials |

## Already verified in RoR (from earlier tests)

Garrison arrows (102, 107, 130), blast width and levels (22, 44), minimum range (20), projectile settings (16, 65,
67-69), train location and button (42, 43), resource storage (21), work rate (13), friendly fire (119 does nothing; the
blast level flag does).

## Suggested rounds

1. **Trigger batch**, one lane each like the combat test: regeneration, damage reflection, area damage, bonus damage
   resistance, add attack type, dead unit id, conversion time. One scenario, no data mod.
2. **Data mod tasks**: charge (ported Elite Hoplite), aura (copy the Centurion's onto a RoR unit), loot, the Mule Cart,
   HP transform.
3. **Data mod techs**: spawn unit, an enemy curse (type 21/26), a team buff.

## Results, part 1 (`crucible mech-test`, 2026-11-09, attributes set by trigger)

Logged every 2 s; the Crucible Test Data mod was active (Axemen 400 HP). Some enemy units wandered, which muddied
lanes 5 and 10 after the first 30 s.

| Lane | Result |
|---|---|
| 1 Regeneration out of combat | **Works, on units and buildings**: 60/min healed exactly 1 HP a second on the swordsman and on the House, up to full; the controls stayed damaged |
| 2 Regeneration in combat | **Works in combat too**: the regenerating swordsman ended its fight with 6 HP against the control's 4 (the fight lasted ~12 s) |
| 3 Reflection, melee | **Works, but weakly**: the Axeman hitting the reflecting swordsman lost 5 HP (the control's lost none), all in the first ~8 s, far less than 50% of the damage dealt |
| 4 Reflection, ranged | **Doesn't reflect ranged attacks**: the Bowman lost nothing |
| 5 Area damage, Bowman | **Needs splash width**: with width 1 the neighbour took damage (19), with area damage alone it took none |
| 6 Area damage, swordsman | **Works on melee too, with splash width**: the neighbour took 84; area damage alone did nothing |
| 7 Bonus damage resistance 40% | **Works**: the resistant Cavalry had 97 HP when the control had 75, and lived ~4 s longer against Camel Riders |
| 8 Add attack type (161), then +50 vs buildings | **Works by trigger**: that House fell in ~15 s; the one only "set" +50 vs buildings (a class the Axeman lacks) took ~80 s. So a trigger *can* add an attack class: set 161 to the class first, then set the amount |
| 9 Dead unit | **Horse Archer → Bowman works** (your Bowmen went 3 → 4 when it died). The Camel Rider → Broad Swordsman made no Broad Swordsman (count stayed 0) |
| 10 Charge | **Type 1 works**: the first hit took 41 against the plain elephant's 11 (+30, the charge). Type 3 hit for 23 (+12, its charge) but splashed nothing, even with splash width 1 |

## Results, part 2 (`crucible mech-data-test`, 2026-11-09, data mod)

| Test | Result |
|---|---|
| Phalanx: the Chronicles Hoplite's count aura (+2 armour per Hoplite within 3, up to 8) copied onto RoR Hoplites | **Didn't work** (no armour change); the ported Chronicles Hoplites showed none either (their aura still names AoE2 unit ids 2110/2111, which the port doesn't remap) |
| Building aura: the Centurion's speed aura (mode 3) on the Town Center, retargeted to infantry (class 6), x1.5 | **Didn't work** |
| Loot: the Camel Raider's loot tasks on Axemen | **Didn't work** (gold never rose from kills) |
| HP transform: Short Swordsman becomes Long Swordsman below 50% (the Jian's task) | **Works** |
| Extra spawn on Clubmen | Not testable: an Iron Age start upgrades Clubmen to Axemen (the Axe tech), so no Clubmen to train |
| Mule Cart, ported, with a dropsites.json entry and listed by every villager job unit | **Works**: villagers dropped wood at it (wood climbed steadily), and it moves |
| Wonder techs | **All work**: 500 of everything; spawn 3 War Elephants at the Town Center (effect 7); curse, enemy infantry HP x0.5 (effect 25: the enemy Hoplite went 999 → 500); team gift +500 food (effect 11: both you and your ally got it) |

Ruled out for the auras and loot: unit upgrades (an Iron Age start doesn't upgrade Hoplites or Axemen) and the unit's
combat level (the same on RoR's units as on AoE2's aura units). Next: port the AoE2 units whole (Camel Raider,
Centurion, Chronicles Hoplite, with their task target ids remapped) to tell "copied wrong" from "RoR doesn't run
these tasks".

## Results, part 2 round 2 (2026-11-09, ran to 1:20, then the game crashed)

- **Out-of-combat regeneration by script works** (Mutalisk-style). `xsEffectAmount(cSetUnitAttribute, unit, 109,
  value, player)` changes one unit's regeneration. Taking 20 damage every 8 s, the scripted Cavalry (regen off for 5 s
  after each hit) gained only 1-2 HP per cycle, against +5 per 5 s for plain regeneration; the one damaged once
  regenerated steadily.
- **The crash** came at game time 1:20 (crash report WorldTime 80321), the moment the scripted Cavalry died (HP 0 in
  that sample). Most likely cause: `cSetUnitAttribute` on a dying unit, which still "exists". Fixed by skipping units
  at 0 HP; to be confirmed.
- **Logistics forced at 0:30 didn't lower the population** (69 before and after, with 10 Slingers and other infantry
  on the map): it may only apply to units made afterwards. The other half-pop routes weren't readable: the player
  deleted units to free population room (headroom was -66; RoR's cap comes from Houses), so round 2b adds Houses
  and +150 headroom.
- Loot: still no gold, but it's unclear the Camel Raiders got kills before the crash.
- The data mod's old HP overrides (Hoplite 999, Axeman 400) are retired.

## Results, part 2 round 2b (2026-11-09)

- **No crash**: skipping units at 0 HP fixed it (the game crashed when `cSetUnitAttribute` touched a dying unit).
- **Half a pop slot**:
  | Route | Result |
  |---|---|
  | RoR's Logistics (forced by trigger) on Slingers | **Works** for units trained after it (existing ones kept their full slot) |
  | Trigger Modify Attribute 110 = -0.5, as AoE2ScenarioParser writes it (integer field, -1) on Bowmen | **No** |
  | The same trigger with -0.5 forced into the float field, on Horse Archers | **No**: the game truncates it too, as aoe-editor's guard says |
  | XS `xsEffectAmount(cSetAttribute, Camel Rider, 110, -0.5, 1)` | **Works** |
  | Data: Karambit-style storages on Scouts (4 = -0.5, 11 = 0.5, 19 = 0.5) | **Works** |

  So for a campaign: half-pop by **XS** (or a data mod), never by a trigger. (Horse Archers and Camel Riders can't be
  trained by Greeks; checked by deleting them and watching the population.)
- **Loot doesn't work in RoR**, even on AoE2's own ported Camel Raider (gold never moved). Neither do **auras**: not
  the ported Centurion's, not the Chronicles Hoplite's phalanx pointed at itself. RoR's game mode doesn't seem to run
  tasks 154 and 155.
- **Extra spawn works**: an Axeman trained at the Barracks brings a second (the Blackwood archer's task 156).

Summary of AoE2 tasks in RoR: HP transform (158), extra spawn (156) and movable drop site (153) work; aura (155) and
loot (154) don't.

## Results, unit test (`crucible unit-test`, 2026-11-09): all work

| Test | Result |
|---|---|
| Chu Ko Nu: total/max missiles 3, secondary arrow 510 (trigger) | Works: the neighbour of the target took damage too |
| Kipchak: 3 arrows spread over a 1 x 1 area (data) | Works |
| Mangonel: catapult stone, splash width 1, blast level 2 on a Bowman (trigger) | Works: the neighbour took splash (50 → 17) |
| Manual mode: trait 8 + alternate unit (data) | Works: Bowmen get a switch button to a siege mode |
| Automatic switch: charge type 6 (Fire Archer, Hearth Troop ported; a Bowman given the Fire Archer's settings by trigger) | Works |
| Khmer farmers: player resource 33 = 50 (trigger) | Works: food arrived with no drop-off trips. Resource 33 switches hard-coded civ functions, so it can't be pointed at other resources |
| No drop-off for wood: XS moves `cUnitAttributeHeld` into the stockpile every second | Works. Quirk: when a tree runs out, lumberjacks still walk to the nearest drop site (holding nothing) and back. A script could send them straight to the next tree |
| Limited training: a unit costing 1 of resource 214, a Wonder tech giving the team 5 (effect 11) | Works: your ally got 5 too, and exactly 5 could be trained. Units honour a cost in a spare resource (techs don't) |

## Results, tower modes (`crucible tower-modes`, 2026-11-09)

- **No mode switch on buildings**: the towers got trait 8 and an alternate unit (the Immortal's way) but showed no
  switch button. Unit-only, apparently.
- **A charge-type-6 projectile is not a separate close-range weapon.** Both data towers (the Hearth Troop's charge
  settings, event 0 / target 127, and the Fire Archer's, event -4 / target 191) fired boulders and arrows at the far
  Clubmen and nothing at the close ones: the charge projectile goes at the current target and obeys the tower's
  minimum range. The control Sentry Tower (minimum range 2 by trigger) fired arrows at the far ones only, so
  **minimum range works on towers**.
- Next idea for "a boulder when enemies are close", and for the ballista mode too: swap the tower by trigger. A looping trigger watches an area
  around the tower; while enemies are inside, Replace Object turns it into a boulder variant (minimum range 0, range
  2, stone), and back to the arrow variant when the area is clear.

## Results, tower modes round 2 (2026-11-09): the over-the-top tower works natively

- **Boulder as the normal attack (range 2, no minimum) + arrows as a charge-type-6 projectile with its own range
  2-6 gives exactly the effect**: each of the three towers killed the close Clubmen with boulders (the neighbour took
  the splash: 44 → 13 → 0), then shot the far ones (5 tiles) with arrows. The Fire Lancer's (event 4, target 127),
  the Hearth Troop's (event 6, target 127) and the Fire Archer's (event -4, target 191, always full) charge settings
  all behaved the same; recharge 10/s (or the Fire Archer's huge rate) keeps the charge always ready.
- So **a charge projectile's own max range extends what the unit engages**, past its normal attack range. Its own
  min range doesn't hold it back the other way: the inverted tower (arrows normal 2-6, a boulder charge with range
  0-2) threw boulders at the far Clubmen and never touched the close ones (the arrows' minimum range blocks them).
- Ballista mode by repeatable techs (effect type 3, "Ballista mode" / "Arrow mode") on the tower.

## Results, map tricks (`crucible map-tricks`, 2026-11-09)

| Test | Result |
|---|---|
| Unbuildable line: Flags; a grass-tuft blocker with "can be built on" 0; the same invisible; a Rock 1 overlay layer | **All buildable.** Objects with "can be built on" 0 don't stop placement, and the overlay layer doesn't change the tile's rules (so it's visual only) |
| Safe zone A: looping trigger, Enable then Disable Unit Attackable by area | **Fails**: Hoplites inside took damage from about 0:45 (120 → 61-114) |
| Safe zone B: XS sets each Hoplite's `cUnitAttackable` by position every second | **Fails**, a little later (damage from about 1:00). "Unattackable" doesn't stop splash or hits already on the way |
| Doubled gold mine by trigger (Modify Object Attribute 21 = 1000 on a Gaia mine) | **No**: stayed 500 |
| Doubled gold mine by XS (`cUnitAttributeHeld` x 2) | **Works**: 1000 |
| Three decision popups at once | They stack, but the first (A/B) ended up under the menu options, and the others stay open: you can click several. (Whether the later picks' triggers fired despite being switched off: to check) |

Next ideas:
- Unbuildable line: reverse the layers. Base terrain an unbuildable walkable one (Rock 1, Quicksand), overlay layer
  the look you want (grass, dirt, desert).
- Safe zone: a fast script that restores the HP of units inside (`cUnitHitpoints` is settable), alone or with
  unattackable.
