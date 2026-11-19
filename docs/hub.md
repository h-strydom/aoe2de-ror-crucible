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
  mark (the Town Center and the Wonder stay the player's: Begin the Crucible and the boons live there).
- Each upgrade's button counts it: the icon shows "4/10" and the name "Villager (4/10)". The count icons are the data
  mod's own pictures (`datamod/count_icons.py`), swapped in by Change Technology Icon as each level comes on offer.
- The Wonder's caption counts towards the next tier: "(!)" over "0/5 until Tier 2", then "0/10 until Tier 3".
- **Tier 2** opens once 5 tier 1 levels are bought; tier 3 (nothing yet) at 10 tier 2 levels.
- An XS rule works out what's on offer every second and signals changes through trigger variables to looping
  triggers (XS can't enable techs, change owners or captions).

| Upgrade | Tier | Place, button | Levels | In the hub | In the run |
|---|---|---|---|---|---|
| Villager | 1 | TC 1 | 6 | a gray villager turns purple | one more villager, just south of the four |
| House | 1 | TC 2 | 7 | a gray house turns purple | one of the base's houses is yours, at full HP |
| Granary | 1 | TC 3 | 1 | the Granary is bought (a place) | the base's Granary is yours |
| Storage Pit | 1 | TC 4 | 1 | the Storage Pit is bought (a place) | the base's Storage Pit is yours |
| Barracks | 1 | TC 5 | 1 | the Barracks is bought (a place) | the base's Barracks (nearest the TC) is yours |
| Clubmen | 1 | Barracks 5 | 1 | 3 Clubmen turn purple | 3 Clubmen in the first melee slots |
| More boons | 1 | Wonder 1 | 4 | | each decision offers one more boon, up to 5 |
| Faster boons | 1 | Wonder 2 | 5 | | boons research faster: 48, 36, 24, 12 s, then 1 s |
| Bronze Age | 2 | tier 2 TC 1 | 1 | | Bronze Age can be researched |
| Second Barracks | 2 | tier 2 TC 2 | 1 | the second Barracks is bought | the base's second Barracks is yours |
| Market | 2 | tier 2 TC 3 | 1 | the Market is bought | the base's Market is yours |
| Archery Range | 2 | tier 2 TC 4 | 1 | the Archery Range is bought | the base's Archery Range is yours |
| Stable | 2 | tier 2 TC 5 | 1 | the Stable is bought | the base's Stable is yours |
| Axe | 2 | second Barracks 1 | 1 | | Axe can be researched |
| Axemen | 2 | second Barracks 2 | 2 | the Clubmen become 3 Axemen, then 2 more | Axemen instead of the Clubmen, then 2 more |
| Market upgrades | 2 | Market 1 | 1 | | the Market's techs can be researched |
| Bowmen | 2 | Archery Range 1 | 3 | 3, 1, 1 Bowmen turn purple | Bowmen in the ranged slots |
| Scout | 2 | Stable 1 | 1 | the Scout turns purple | a Scout in its slot |
| Storage Pit upgrades | 2 | Storage Pit 1 | 1 | | Tool Working and the three Leather Armors |
| Watch Tower | 2 | Granary 1 | 1 | | the base's towers are yours, and Watch Towers can be built |
| Walls | 2 | Granary 2 | 1 | | the base's walls are yours, still damaged |
| Begin the Crucible | | TC 11 | | ends the hub: the run starts | |

Axemen needs the Clubmen. An unlocked tech still waits for its own prerequisites (its age, its building). Kept buildings change hands at the start of the run, before the Allies' buildings drop to
1 HP. Starting soldiers stand in slots by the Wonder (5 melee, 5 ranged, a scout, 3 cavalry, 1 siege).

A decision at every start offers to reset all progress: it clears the bank at once and shows from the next start
(restart the mission).

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
