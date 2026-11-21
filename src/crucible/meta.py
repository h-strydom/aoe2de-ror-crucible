"""Meta upgrades: bought in the hub, kept in the campaign bank, applied at the start of every run.

Out of the box the run's player has the Stone Age and part of the Tool Age (run_rules: no techs but Tool Age, few
units); everything else is bought here. Upgrades come in tiers: a tier opens once enough upgrades are bought, from
any tier (TIERS).

Each upgrade is researched at a place in the hub: a building of the player's (the Town Center, the Wonder) or one
bought by another upgrade (the Granary, the second Barracks). In the run, a level gives the player one more of
something (a villager, a kept building, starting soldiers) or unlocks techs.
"""

from dataclasses import dataclass

TOWN_CENTER, BARRACKS, WONDER, GRANARY, STORAGE_PIT = 109, 12, 276, 68, 562
MARKET, ARCHERY_RANGE, STABLE = 84, 87, 101
TOWN_CENTER_AGE2, BARRACKS_AGE2 = 71, 498  # what the hub's tier 2 copies look like (Tool Age)
TIERS = (5, 10)  # more levels bought (from any tier) to open each tier after the first: 5 for tier 2, 10 more for 3


@dataclass(frozen=True)
class Place:
    """Where upgrades are researched in the hub. `unit` is the type placed in the hub map; the second Town Center and
    Barracks become copies of their own (`copy_of`, made by the data mod), so they show only their own buttons."""

    key: str
    unit: int
    owner: str  # "player": the player's from the start; "gray": gray until bought (tier 1); "tier2": gray, tier 2
    opened_by: str = ""  # the upgrade that buys it; none: open from the start ("player") or with its tier
    copy_of: int = -1

    @property
    def copy_key(self) -> str:
        return f"hub_unit_{self.key}"  # the data mod's manifest key of the copy


@dataclass(frozen=True)
class Upgrade:
    key: str  # the bank key, the trigger variable and the data mod's manifest key (hub_<key>)
    title: str
    description: str
    place: str  # a Place's key
    button: int
    levels: int  # how many times it can be bought: the button counts levels ("0/2"), not what they give
    tier: int = 1
    label: str = ""  # a short name for trigger names
    amounts: tuple[int, ...] = ()  # soldiers: how many each level adds
    requires: tuple[tuple[str, int], ...] = ()  # (upgrade, level) bought first

    @property
    def tech(self) -> str:
        return f"hub_{self.key}"


PLACES = (
    Place("town_center", TOWN_CENTER, "player"),
    Place("wonder", WONDER, "player"),
    Place("barracks", BARRACKS, "gray", "meta_barracks"),
    Place("granary", GRANARY, "gray", "meta_granary"),
    Place("storage_pit", STORAGE_PIT, "gray", "meta_storage_pit"),
    Place("town_center_2", TOWN_CENTER, "tier2", copy_of=TOWN_CENTER_AGE2),
    Place("barracks_2", BARRACKS, "tier2", "meta_barracks_2", copy_of=BARRACKS_AGE2),
    Place("market", MARKET, "tier2", "meta_market"),
    Place("archery_range", ARCHERY_RANGE, "tier2", "meta_archery_range"),
    Place("stable", STABLE, "tier2", "meta_stable"),
)

# tier 1: a bigger start
VILLAGERS = Upgrade(
    "meta_villagers",
    "Villager",
    "Start each run with one more villager.",
    "town_center",
    1,
    6,
    label="villagers",
)
STARTING_HOUSES = 2  # of the base's houses, the player's in every run (and in the hub)
HOUSES = Upgrade(
    "meta_houses",
    "House",
    f"Start each run with one more of your base's houses (you always have {STARTING_HOUSES}): yours, at full health.",
    "town_center",
    2,
    5,
    label="houses",
)
GRANARY_UPGRADE = Upgrade(
    "meta_granary",
    "Granary",
    "Start each run with your base's Granary: yours, at full health.",
    "town_center",
    3,
    1,
    label="Granary",
)
STORAGE_PIT_UPGRADE = Upgrade(
    "meta_storage_pit",
    "Storage Pit",
    "Start each run with your base's Storage Pit: yours, at full health.",
    "town_center",
    4,
    1,
    label="Storage Pit",
)
BARRACKS_UPGRADE = Upgrade(
    "meta_barracks",
    "Barracks",
    "Start each run with a Barracks: yours, at full health.",
    "town_center",
    5,
    1,
    label="Barracks",
)
CLUBMEN = Upgrade(
    "meta_clubmen",
    "Clubmen",
    "Start each run with 3 Clubmen by your Barracks.",
    "barracks",
    5,
    1,
    label="Clubmen",
    amounts=(3,),
)
BOON_SLOTS = Upgrade(
    "meta_boon_slots",
    "More boons",
    "Each decision offers one more boon (up to 5).",
    "wonder",
    1,
    4,
    label="boons per decision",
)
BOON_SPEED = Upgrade(
    "meta_boon_speed",
    "Faster boons",
    "Boons research faster: instant at the fifth level.",
    "wonder",
    2,
    5,
    label="boon speed",
)

# tier 2: a full Tool Age (without walls)
SECOND_BARRACKS = Upgrade(
    "meta_barracks_2",
    "Second Barracks",
    "Start each run with your base's second Barracks: yours, at full health.",
    "town_center_2",
    2,
    1,
    tier=2,
    label="second Barracks",
)
MARKET_UPGRADE = Upgrade(
    "meta_market",
    "Market",
    "Start each run with your base's Market: yours, at full health.",
    "town_center_2",
    3,
    1,
    tier=2,
    label="Market",
)
ARCHERY_RANGE_UPGRADE = Upgrade(
    "meta_archery_range",
    "Archery Range",
    "Start each run with your base's Archery Range: yours, at full health.",
    "town_center_2",
    4,
    1,
    tier=2,
    label="Archery Range",
)
STABLE_UPGRADE = Upgrade(
    "meta_stable",
    "Stable",
    "Start each run with your base's Stable: yours, at full health.",
    "town_center_2",
    5,
    1,
    tier=2,
    label="Stable",
)
AXE = Upgrade(
    "meta_axe",
    "Axemen upgrade",
    "Axe (Clubmen to Axemen) can be researched at the Barracks, and your 3 starting Clubmen are Axemen.",
    "barracks_2",
    1,
    1,
    tier=2,
    label="Axe",
    amounts=(3,),
    requires=(("meta_clubmen", 1),),
)
AXEMEN = Upgrade(
    "meta_axemen",
    "Axemen",
    "Start each run with 2 more Axemen.",
    "barracks_2",
    2,
    1,
    tier=2,
    label="Axemen",
    amounts=(2,),
    requires=(("meta_axe", 1),),
)
MARKET_TECHS = Upgrade(
    "meta_market_techs",
    "Market upgrades",
    "The Market's Tool Age upgrades can be researched: Wood Working, Domestication, Stone and Gold Mining.",
    "market",
    1,
    1,
    tier=2,
    label="Market upgrades",
)
BOWMEN = Upgrade(
    "meta_bowmen",
    "Bowmen",
    "Start each run with 3 Bowmen; the second level adds 2 more.",
    "archery_range",
    1,
    2,
    tier=2,
    label="Bowmen",
    amounts=(3, 2),
)
SCOUT = Upgrade(
    "meta_scout",
    "Scout",
    "Start each run with a Scout.",
    "stable",
    1,
    1,
    tier=2,
    label="Scout",
)
STORAGE_PIT_TECHS = Upgrade(
    "meta_storage_pit_techs",
    "Storage Pit upgrades",
    "The Storage Pit's Tool Age upgrades can be researched: Tool Working and the Leather Armors.",
    "storage_pit",
    1,
    1,
    tier=2,
    label="Storage Pit upgrades",
)
TOWER = Upgrade(
    "meta_tower",
    "Watch Tower",
    "Start each run with your base's towers, and Watch Towers can be built.",
    "granary",
    1,
    1,
    tier=2,
    label="Watch Tower",
)
WALLS = Upgrade(
    "meta_walls",
    "Walls",
    "Start each run with your base's walls: yours, still damaged.",
    "granary",
    2,
    1,
    tier=2,
    label="walls",
)

UPGRADES = (  # Clubmen before the Axemen upgrade: the hub swaps the Clubmen for Axemen
    VILLAGERS,
    HOUSES,
    GRANARY_UPGRADE,
    STORAGE_PIT_UPGRADE,
    BARRACKS_UPGRADE,
    CLUBMEN,
    BOON_SLOTS,
    BOON_SPEED,
    SECOND_BARRACKS,
    MARKET_UPGRADE,
    ARCHERY_RANGE_UPGRADE,
    STABLE_UPGRADE,
    AXE,
    AXEMEN,
    MARKET_TECHS,
    BOWMEN,
    SCOUT,
    STORAGE_PIT_TECHS,
    TOWER,
    WALLS,
)


@dataclass(frozen=True)
class Reward:
    """Given, not bought: reaching `tier` stores 1 under `key` (the hub's tier objective does it)."""

    key: str
    title: str
    tier: int


BRONZE_AGE = Reward("meta_bronze_age", "Bronze Age", 3)  # the Bronze Age can be researched in the run
REWARDS = (BRONZE_AGE,)
KEYS = tuple(k.key for k in (*UPGRADES, *REWARDS))  # everything kept in the bank
TITLES = {k.key: k.title for k in (*UPGRADES, *REWARDS)}

CLUBMEN_PER_LEVEL = 3


def place(key: str) -> Place:
    return next(p for p in PLACES if p.key == key)


def location(p: Place, techs: dict[str, int]) -> int:
    """The type a place's techs are researched at: its copy's for the second Town Center and Barracks."""
    return techs[p.copy_key] if p.copy_of >= 0 else p.unit
