# To do

Parked work, roughly in order. Move an item into its own doc once it's being built.

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
