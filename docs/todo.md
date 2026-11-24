# To do

Parked work, roughly in order. Move an item into its own doc once it's being built.

## To confirm in game

Built but not yet seen working in a playtest. Strike each off once confirmed.

- Artifact in a tower (Guard Tower bounty): towers regenerate 60 HP a minute.
- Artifact in a Granary or Storage Pit (Guard Tower bounty): 2 food or wood a second per building, 20 at most.
- Artifact in a Town Center (Guard Tower bounty): 1 gold and 1 stone a second per Town Center, 10 each at most.
- Hub: "Reset everything" and "Save and win" each ask for confirmation; "No, go back" asks again.
- Composite Bowmen trainable once Composite Bow is researched (upgrade-only units no longer locked: also Broad and
  Long Swordsmen, Heavy Cavalry, later towers and the rest).
- An artifact the Legion captures goes back to Gaia, and can be captured again.
- Trade Workshop (hub, by the Wonder): Rerolls (5 levels) and Spies. In the run, the Wonder's button 13 rerolls the
  boon categories on offer (free per level, then 500 gold); button 14, Spies (5000 gold), shows the whole map.

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

- Tower upgrades raising the tower start level (future tiers).
- Legion ageing (its techs follow the wave clock: docs/waves.md); raids.
- Meta currency and upgrade costs.
- Returning to the hub after a run.
