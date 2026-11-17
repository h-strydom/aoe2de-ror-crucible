"""Meta upgrades: bought in the hub, kept in the campaign bank, applied at the start of every run.

In the hub, each level turns one gray thing purple (player 2, or the player for the Barracks): the hub shows what the
run will start with. In the run, each level gives the player one more of it: a villager, or one of the base's
buildings kept by the player (not handed to the Allies, not at 1 HP), or Clubmen.
"""

from dataclasses import dataclass

TOWN_CENTER, BARRACKS, WONDER = 109, 12, 276


@dataclass(frozen=True)
class Upgrade:
    key: str  # the bank key, the trigger variable and the data mod's manifest key (hub_<key>)
    title: str
    description: str
    building: int  # where it's researched in the hub
    button: int
    levels: int  # how many times it can be bought

    @property
    def tech(self) -> str:
        return f"hub_{self.key}"


VILLAGERS = Upgrade(
    "meta_villagers",
    "Villager",
    "Start each run with one more villager.",
    TOWN_CENTER,
    1,
    6,
)
HOUSES = Upgrade(
    "meta_houses",
    "House",
    "Start each run with one more of your base's houses: yours, at full health.",
    TOWN_CENTER,
    2,
    7,
)
GRANARY = Upgrade(
    "meta_granary",
    "Granary",
    "Start each run with your base's Granary: yours, at full health.",
    TOWN_CENTER,
    3,
    1,
)
STORAGE_PIT = Upgrade(
    "meta_storage_pit",
    "Storage Pit",
    "Start each run with your base's Storage Pit: yours, at full health.",
    TOWN_CENTER,
    4,
    1,
)
BARRACKS_UPGRADE = Upgrade(
    "meta_barracks",
    "Barracks",
    "Start each run with a Barracks: yours, at full health.",
    TOWN_CENTER,
    5,
    1,
)
CLUBMEN = Upgrade(
    "meta_clubmen",
    "Clubmen",
    "Start each run with 3 Clubmen by your Barracks.",
    BARRACKS,
    5,
    1,
)
BOON_SLOTS = Upgrade(
    "meta_boon_slots",
    "More boons",
    "Each decision offers one more boon (up to 5).",
    WONDER,
    1,
    4,
)
BOON_SPEED = Upgrade(
    "meta_boon_speed",
    "Faster boons",
    "Boons research faster: instant at the fifth level.",
    WONDER,
    2,
    5,
)
UPGRADES = (VILLAGERS, HOUSES, GRANARY, STORAGE_PIT, BARRACKS_UPGRADE, CLUBMEN, BOON_SLOTS, BOON_SPEED)

BEGIN = "hub_begin"  # the data mod's manifest key of "Begin the Crucible"
BEGIN_BUTTON = 11  # on the Town Center
CLUBMEN_PER_LEVEL = 3
