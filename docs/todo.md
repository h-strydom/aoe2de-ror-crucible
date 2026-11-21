# To do

Parked work, roughly in order. Move an item into its own doc once it's being built.

## Boons

- **Boon test map**: a check scenario that hands out every boon and shows its effect in game (the unit, building or
  tech it changes, before and after), so each modifier's effect can be confirmed once instead of by chance in runs.
- **Tiered boons** (drafted in `src/crucible/boons/`, one module per civ: the source of truth, kept as Python to
  build the data mod from): six tiers (Poor to Heirloom), each boon a run of them with a list of effects per tier
  (extras combine, a new tier is a new `Tier` member). The lowest tier sets the price, so a higher roll is free.
  Still to do: fold into the data mod (replacing `crucible.bonuses`' fixed values), prices per tier, compile the new
  stats (HP regeneration, conversion speed).
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
