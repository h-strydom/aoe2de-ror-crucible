# The hub

`assets/meta.aoe2scenario` is the camp between runs, made by hand in the editor (`crucible map save meta` /
`crucible map install meta`). `crucible campaign --install` builds it into `crucible_hub` and plays it as the first
mission of the Crucible campaign, before `crucible_run`.

## Players

- **1, the player** (purple): the Town Center and the Wonder, with only the hub's own buttons. Everything those
  buildings (and the Barracks) normally train or research is switched off.
- **2, purple but not the player**: what the next run starts with.
- **3 and up, gray**: what can still be bought. Several players so ages and architectures can be mixed.

Everyone is allied, and the computer players play the "Immobile AI" (the "None AI" explores). Only players who own
something are active: an empty one would be given a starting town. Workers look busy but gather nothing: the purple villagers on the berries (the run's first four),
the gray ones on the stone and gold, all at work rate 0.

## Upgrades

Bought on the Town Center, the Barracks and the Wonder; free and near instant (1 s: at 0 the game researches a tech by itself) for now. Each level turns one gray thing purple, and the run gives
the player one more of it.

| Upgrade | Button | Levels | In the hub | In the run |
|---|---|---|---|---|
| Villager | TC 1 | 6 | a gray villager turns purple | one more villager, just south of the four |
| House | TC 2 | 7 | a gray house turns purple (nearest the TC first) | one of the base's houses is yours, at full HP |
| Granary | TC 3 | 1 | the Granary turns purple | the base's Granary is yours |
| Storage Pit | TC 4 | 1 | the Storage Pit turns purple | the base's Storage Pit is yours |
| Barracks | TC 5 | 1 | the Barracks becomes the player's | the base's Barracks (nearest the TC) is yours |
| Clubmen | Barracks 5 | 1 | the Barracks and its 3 Clubmen turn purple | 3 Clubmen in the first melee slots |
| More boons | Wonder 1 | 4 | | each decision offers one more boon, up to 5 |
| Faster boons | Wonder 2 | 5 | | boons research faster: 48, 36, 24, 12 s, then 1 s (from 60) |
| Begin the Crucible | TC 11 | | ends the hub: the run starts | |

Kept buildings change hands at the start of the run, before the Allies' buildings drop to 1 HP. Starting soldiers
stand in slots by the Wonder (5 melee, 5 ranged, a scout, 3 cavalry, 1 siege); upgrades will fill more of them with
better units.

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
