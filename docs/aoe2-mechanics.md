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
