> **Superseded (2026-11-22):** the hub is now built on `assets/metaprogression.aoe2scenario` as planned in
> docs/meta-v2.md (tiers on players 2-6, the currency, the Wonder's global upgrades). This page describes the old hub.

# The hub

`assets/meta.aoe2scenario` is the camp between runs, made by hand in the editor (`crucible map save meta` /
`crucible map install meta`). `crucible campaign --install` builds it into `crucible_hub` and plays it as the first
mission of the Crucible campaign, before `crucible_run`.

## Players

- **1, the player** (purple): the Town Center and the Wonder, with only the hub's own buttons. Everything those
  buildings (and the Barracks) normally train or research is switched off.
- **2, purple but not the player**: what the next run starts with.
- **3, gray**: tier 1 still to buy. **4, gray, Tool Age**: tier 2 still to buy (its Town Center and Barracks are
  swapped at the start for the data mod's copies, so they show only their own buttons).

Everyone is allied, and the computer players play the "Immobile AI" (the "None AI" explores). Only players who own
something are active: an empty one would be given a starting town. Workers look busy but gather nothing: the purple villagers on the berries (the run's first four),
the gray ones on the stone and gold, all at work rate 0.

## Upgrades

Researched at places: buildings of the player's. Free and near instant (1 s: at 0 the game researches a tech by
itself) for now.

- A place is the player's, marked **(!)**, while it has an upgrade on offer; with none it turns purple and loses the
  mark (the Town Center and the Wonder stay the player's: a player owning nothing is defeated).
- Each upgrade's button counts its levels: the icon shows "2/6" and the name "Villager (2/6)". The count icons are the data
  mod's own pictures (`datamod/count_icons.py`), swapped in by Change Technology Icon as each level comes on offer.
- An objective counts towards the next tier: "0/5 upgrades until Tier 2"; once met, "0/10 more upgrades until Tier 3"
  starts. The counts live in players 3 and 4's relics (objective text can show a player's resource, not a variable).
- Reaching **tier 3** gives the Bronze Age (it can be researched in the run): not bought, stored by the tier 3
  objective.
- **Tier 2** opens once 5 levels are bought; tier 3 (nothing yet) at 10 more, from any tier.
- An XS rule works out what's on offer every second and signals changes through trigger variables to looping
  triggers (XS can't enable techs, change owners or captions).

| Upgrade | Tier | Place, button | Levels | In the hub | In the run |
|---|---|---|---|---|---|
| Villager | 1 | TC 1 | 6 | a gray villager turns purple | one more villager, just south of the four |
| House | 1 | TC 2 | 5 | a gray house turns purple | one more of the base's houses is yours, at full HP (2 always are) |
| Granary | 1 | TC 3 | 1 | the Granary is bought (a place) | the base's Granary is yours |
| Storage Pit | 1 | TC 4 | 1 | the Storage Pit is bought (a place) | the base's Storage Pit is yours |
| Barracks | 1 | TC 5 | 1 | the Barracks is bought (a place) | the base's Barracks (nearest the TC) is yours |
| Clubmen | 1 | Barracks 5 | 1 | 3 Clubmen turn purple | 3 Clubmen in the first melee slots |
| More boons | 1 | Wonder 1 | 4 | | each decision offers one more boon, up to 5 |
| Faster boons | 1 | Wonder 2 | 5 | | boons research faster: 48, 36, 24, 12 s, then 1 s |
| Second Barracks | 2 | tier 2 TC 2 | 1 | the second Barracks is bought | the base's second Barracks is yours |
| Market | 2 | tier 2 TC 3 | 1 | the Market is bought | the base's Market is yours |
| Archery Range | 2 | tier 2 TC 4 | 1 | the Archery Range is bought | the base's Archery Range is yours |
| Stable | 2 | tier 2 TC 5 | 1 | the Stable is bought | the base's Stable is yours |
| Axemen upgrade | 2 | second Barracks 1 | 1 | the Clubmen become 3 Axemen | Axe can be researched; Axemen instead of the Clubmen |
| Axemen | 2 | second Barracks 2 | 1 | 2 more Axemen turn purple | 2 more Axemen |
| Market upgrades | 2 | Market 1 | 1 | | the Market's Tool Age techs can be researched (Bronze Age ones: later) |
| Bowmen | 2 | Archery Range 1 | 2 | 3, then 2 Bowmen turn purple | Bowmen in the ranged slots |
| Scout | 2 | Stable 1 | 1 | the Scout turns purple | a Scout in its slot |
| Storage Pit upgrades | 2 | Storage Pit 1 | 1 | | Tool Working and the three Leather Armors |
| Watch Tower | 2 | Granary 1 | 1 | | the base's towers are yours, and Watch Towers can be built |
| Walls | 2 | Granary 2 | 1 | | the base's Small Walls are yours, still damaged (the Fortified Walls stay the Allies') |
| Ballista Towers | 5 | Zenobia's Tower 1 | 1 | | the Granary's Siege Towers (after Ballistics) lets villagers build Ballista Towers (slot 12) |
| Catapult Towers | 5 | Zenobia's Tower 2 | 1 | | the same for Catapult Towers (slot 13) |

Tier 5 also has the Colosseum (prestige: expensive, game-changing upgrades that start you over; empty for now) and
Zenobia's Tower (added 2026-11-25). The siege towers are their siege line in a tower: the Ballista or Stone Thrower's
attacks, ranges, reload and blast, upgraded with it (Helepolis; Catapult, Heavy Catapult) and by siege techs and
boons (not their cost cuts), plus building and tower upgrades; no Guard Tower attack or range (datamod/siege_towers).
Ballista Tower: 200 stone, 300 gold; Catapult Tower: 300 stone, 200 gold.

The Axemen upgrade needs the Clubmen; Axemen need the Axemen upgrade. An unlocked tech still waits for its own prerequisites (its age, its building). Kept buildings change hands at the start of the run; 3 seconds in the Allies' other
buildings but walls and towers are removed. Starting soldiers stand in slots by the Wonder (5 melee, 5 ranged, a scout, 3 cavalry, 1 siege).

A decision at every start stays open while the player shops: **Reset everything** clears the bank at once and shows
from the next start (restart the mission; a one-button decision still offers to save and win), **Save and win** ends
the hub in a victory, which starts the run (purchases are stored as they're made). No Begin button.

## Prices (first pass, 2026-11-26)

`meta.PRICES`: food, wood, gold and stone a level, from a simulation (`_Workspace/crucible-wave-sim`: `node ages.js`
samples the Legion's age at each wave, `prices.py` plays campaigns of runs on it and searches the prices). Each
defeated wave pays the difficulty's factor (1, 2, 3) of its Legion age's resource: Stone food, Tool wood, Bronze
gold, Iron and later stone. A Moderate run pays about 10 food, 20 wood from wave 15, 28 gold from wave 22, and stone
only past wave 28, so a tier is priced in what the player earns while buying it: tier 1 food and wood, tier 2 adds
a little gold, tier 3 wood and gold, tiers 4 and 5 gold with some stone; the Trade Workshop's extras wood, gold
and stone.

Assumed players (waves defeated a run, with nothing bought to everything bought, +-25%): average on Moderate 10 to
40, good on Hard 12 to 32 (struggles even with most upgrades). Results: the average Moderate player has everything
after about 30 runs (10-90%: 23-40), tiers 2-5 opening around runs 1, 3, 4, 11; the good Hard player after about
18 (15-24). A casual Standard player (14 to 40 waves, a factor of 1) would need about 140 runs. Everything costs
about 155 food, 317 wood, 242 gold, 54 stone. For scale: 2026-11-25's testing (every upgrade free) collected 133
food, 119 wood, 148 gold, 107 stone.

## The bank

Upgrades are stored in the campaign bank (keys `meta_villagers`, `meta_houses`, ...), only inside the Crucible
campaign: a standalone hub or run neither keeps nor sees them. The hub loads them at the start, so coming back shows
everything bought so far. Replaying the hub asks "save your choices?": No throws away that visit's buys.

## Open

- what upgrades cost (currency earned in runs)
- getting back to the hub after a run

## The data mod

A scenario doesn't record its data mod, so the player picks Crucible as the Data Mod on the campaign screen; it
stays loaded from the hub into the run. Without it the hub's and the run's techs don't exist: both maps then say to
pick it and, 5 seconds later, kill everything of the player's, which loses the mission.
