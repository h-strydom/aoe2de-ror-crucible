# To do

Parked work, roughly in order. Move an item into its own doc once it's being built.

## Boons

- **Tiered boons** (drafted in `src/crucible/boons/`, one module per civ: the source of truth, kept as Python to
  build the data mod from): six tiers (Poor to Heirloom), each boon a run of them with a list of effects per tier
  (extras combine, a new tier is a new `Tier` member). The lowest tier sets the price, so a higher roll is free.
  In the shop since 2026-11-21 (prices in `TIER_COSTS`, a first guess). Still to do: compile the new stats (HP
  regeneration, conversion speed); retire `crucible.bonuses`' fixed values (only its compilers are still used).
- **Offers**: each choice from a different tag axis (domain, effect, subject, building, civ, civ type), then a boon
  at random with that tag (`catalogue.offer`). Later: picking a group more often makes it likelier.
- **Wave 0**: an instant wave at the start; killing it gives random Poor boons for free. Waves 1 on stay as they are,
  and victory becomes defeating 10 waves.
- Custom coloured icons per tier.

## Hub and run

- Tower upgrades raising the tower start level (future tiers).
- Wave table and Legion ageing; raids.
- Meta currency and upgrade costs.
- Returning to the hub after a run.
