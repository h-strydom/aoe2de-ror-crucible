# To do

Parked work, roughly in order. Move an item into its own doc once it's being built.

## To confirm in game

Built but not yet seen working in a playtest. Strike each off once confirmed.

- Artifact in a tower (Guard Tower bounty): towers regenerate about 30 HP a minute an artifact (attribute 15; 60
  showed as 2 HP a second, so the attribute may count double: check the rate).
- Artifact in a Granary or Storage Pit (Guard Tower bounty): 2 food or wood a second per building, 20 at most.
- Artifact in a Town Center (Guard Tower bounty): 1 gold and 1 stone a second per Town Center, 10 each at most.
- Composite Bowmen trainable once Composite Bow is researched (upgrade-only units no longer locked: also Broad and
  Long Swordsmen, Heavy Cavalry, later towers and the rest).
- Improved Bowmen trainable after Improved Bow, Catapult Triremes after Trireme with Catapult (and Juggernaughts):
  a trigger switches on each unit a tech enables.
- No boon shows as Spies (new techs skip id 408).
- An artifact the Legion captures goes back to Gaia, and can be captured again.
- Two artifacts in one building type boost it twice; the artifact regenerates 120 HP a minute; with the bounty,
  units garrisoned in its building type heal 15 HP a minute an artifact, now by XS (the garrison heal rate healed no
  Cataphracts in a Stable): Cataphracts in a Stable with an artifact heal.
- A ruin gives 25 population room (was 50).
- Trade Workshop (hub, by the Wonder): Rerolls (5 levels) and Spies. In the run, the Wonder's button 13 rerolls the
  boon categories on offer (free per level, then 500 gold); button 14, Spies (5000 gold), shows the whole map.
  Spies is now instant. Rerolls were slow to research too: their time is 1 s, cause unknown.
- A reroll weighs the categories it turned down less; a category with fewer boons left than the slots weighs less;
  each Legion base destroyed gives a free reroll more (with Rerolls).
- Outposts phase 5 (docs/outposts.md): markers, units out of buildings, wander and patrol, rounds, difficulty
  scaling, transports to the Kings with escorts, removed at the sea markers.
- Outposts phase 6 (docs/outposts.md): turtled 2 minutes; faster turns (much faster on Hard); everything grows with
  time and with each outpost destroyed; raids on villagers outside the base; a party at once to a spot the player
  is on; spots better guarded; attack waves twice as big, the first at 10 minutes on Hard (12.5 Moderate, 15
  Standard); units swap to a better line at once, one for one.
- Hard waves: siege more often, the age-up chance grows four times as fast (Moderate twice): past Slingers well
  before 36 minutes.
- No wall upgrades: the base's walls are the Allies', heavily damaged, about a third destroyed.
- Trade Workshop's Tribute (3 levels): the Wonder gives 0.5 of each resource a second a level.
- The boon All units: Line of sight (+5, one level, legendary).
- With one boon left a choice offers it (rolls kept in range; a choice that offers nothing comes back; choices with
  nothing to offer wait instead of being dropped).

## Boons

- **Tiered boons** (drafted in `src/crucible/boons/`, one module per civ: the source of truth, kept as Python to
  build the data mod from): six tiers (Poor to Heirloom), each boon a run of them with a list of effects per tier
  (extras combine, a new tier is a new `Tier` member). Each tier costs its own price, rolled up or not.
  In the shop since 2026-11-21 (prices in `TIER_COSTS`). Still to do: compile the new stats (HP
  regeneration, conversion speed); retire `crucible.bonuses`' fixed values (only its compilers are still used).
- **Offers**: each choice from a different tag axis (domain, effect, subject, building, civ, civ type), then a boon
  at random with that tag (`catalogue.offer`). Later: picking a group more often makes it likelier.
- Custom coloured icons per tier.

## Hub and run

- Pregame slides with a tutorial.
- Custom icons for all upgrades.
- Achievements, with bonuses.
- Hotkeys for our upgrades.
- A buildable wonder with unique bonuses.
- A prestige mode.
- Possible: the Legion gets +1 damage against buildings every 10 levels, against tower spam.
- Possible: defeating an outpost's wave gives a minor bonus (resources, a reroll, something).
- Tower upgrades raising the tower start level (future tiers).
- Legion ageing (its techs follow the wave clock: docs/waves.md).
- Meta currency and upgrade costs.
- Returning to the hub after a run.
