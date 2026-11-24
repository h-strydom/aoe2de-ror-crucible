"""Meta upgrades (docs/meta-v2.md): bought in the hub with the currency the runs earn, kept in the campaign bank,
applied at the start of every run.

The hub map (assets/metaprogression) has a player per tier: 2 the Stone Age, 3 the Tool, 4 the Bronze, 5 the Iron, 6
the Post-Iron; player 1, the player, has the Wonder (global upgrades). A tier opens once enough upgrades are bought,
from any tier (TIERS); opening it hands its buildings to the player (TIER_GIVEN). Each upgrade is researched at a place:
one of a tier player's buildings, the player's once its tier is open (and, for some, once an upgrade has bought it).
Buying a level can also hand over units of the place's player (`shows`): the villagers, Clubmen and Axemen the run will
start with.

In the run, a level gives the player one more of something (a villager, a kept building, starting soldiers) or
unlocks units and techs; what each new upgrade does in the run comes in later steps of the plan.
"""

from dataclasses import dataclass

TOWN_CENTER, BARRACKS, WONDER, GRANARY, STORAGE_PIT = 109, 12, 276, 68, 562
MARKET, ARCHERY_RANGE, STABLE = 84, 87, 101
ACADEMY, GOVERNMENT_CENTER, SIEGE_WORKSHOP, TEMPLE, HOUSE, DOCK = 103, 209, 49, 104, 70, 45
VILLAGER_TYPES = (83, 293)
CLUBMAN, AXEMAN, BOWMAN, SCOUT = 281, 531, 4, 448
SHORT_SWORDSMAN, BROAD_SWORDSMAN, LONG_SWORDSMAN, LEGIONARY = 74, 75, 77, 473
IMPROVED_BOWMAN, COMPOSITE_BOWMAN, HORSE_ARCHER, HEAVY_HORSE_ARCHER, ELEPHANT_ARCHER = 24, 492, 39, 474, 873
CAVALRY, HEAVY_CAVALRY, CATAPHRACT, WAR_ELEPHANT, ARMORED_ELEPHANT, SCYTHE_CHARIOT = 38, 283, 569, 1132, 1134, 1372
CENTURION, HEAVY_CATAPULT, HELEPOLIS = 359, 588, 542
WATCH_TOWER, SENTRY_TOWER, GUARD_TOWER = 79, 234, 235
SMALL_WALL, MEDIUM_WALL, FORTIFIED_WALL = 72, 117, 155
TRADE_WORKSHOP = 110  # the player's, by the Wonder (added to the hub 2026-11-24)

TIERS = (5, 10, 20, 20)  # more levels bought (from any tier) to open tiers 2, 3, 4, 5
TIER_PLAYERS = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}  # tier -> its player in the hub map
TIER_AGES = {1: 0, 2: 1, 3: 2, 4: 3, 5: 3}  # tier -> the age its buildings look (Stone 0 to Iron 3)
# Opening a tier hands over its player's buildings of these types. Its other buildings are places that open only if
# the tier before had theirs (a Bronze Age Stable once the Tool Age Stable is bought: playtest 2026-11-22).
TIER_GIVEN = {
    2: (TOWN_CENTER, GRANARY, STORAGE_PIT),
    3: (TOWN_CENTER, GRANARY, STORAGE_PIT),
    4: (TOWN_CENTER, GRANARY, STORAGE_PIT),
    5: (),
}
START_GIVEN = {TOWN_CENTER: 1, HOUSE: 2}  # tier 1's, the player's from the start (and 4 villagers: START_VILLAGERS)
START_VILLAGERS = 4

# The currency (docs/meta-v2.md): each wave defeated pays 1 of its Legion age's resource, banked under these keys.
CURRENCY = ("meta_food", "meta_wood", "meta_gold", "meta_stone")
CURRENCY_NAMES = ("Food", "Wood", "Gold", "Stone")
CURRENCY_BY_AGE = (0, 1, 2, 3, 3)  # Stone, Tool, Bronze, Iron, Post-Iron -> a CURRENCY index


@dataclass(frozen=True)
class Place:
    """Where upgrades are researched: a building of tier `tier`'s player (`unit`, the nth of its type: `nth`), the
    player's once the tier is open and, with `opened_by`, once that upgrade is bought. Each has its own copy of its
    building in the data mod (`copy`), aged to its tier, so it shows only its own buttons."""

    key: str
    unit: int
    tier: int  # 0: the Wonder, the player's own
    opened_by: str = ""
    copy: bool = True

    @property
    def player(self) -> int:
        return TIER_PLAYERS.get(self.tier, 1)

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
    levels: int = 1  # how many times it can be bought: the button counts levels ("0/2"), not what they give
    tier: int = 0  # when it's on offer: its place's tier if 0
    label: str = ""  # a short name for trigger names
    amounts: tuple[int, ...] = ()  # soldiers: how many each level adds (the run)
    requires: tuple[tuple[str, int], ...] = ()  # (upgrade, level) bought first
    shows: tuple[int, ...] = ()  # unit types of the place's player handed over in the hub, `per` a level
    per: tuple[int, ...] = ()  # how many of `shows` each level hands over (default: one each, or all at once)
    caps: tuple[tuple[int, int], ...] = ()  # (tier, levels on offer once it's open): the Wonder's, which grow
    cost: tuple[int, int, int, int] = (0, 0, 0, 0)  # food, wood, gold, stone a level (placeholders: free)
    texts: tuple[str, ...] = ()  # the tooltip by levels bought (0 to `levels`), set live: what the next adds

    @property
    def tech(self) -> str:
        return f"hub_{self.key}"


PLACES = (
    Place("wonder", WONDER, 0, copy=False),
    Place("trade_workshop", TRADE_WORKSHOP, 0),
    Place("town_center_1", TOWN_CENTER, 1),
    Place("barracks_1", BARRACKS, 1, "meta_barracks"),
    Place("town_center_2", TOWN_CENTER, 2),
    Place("granary_2", GRANARY, 2),
    Place("storage_pit_2", STORAGE_PIT, 2),
    Place("barracks_2", BARRACKS, 2, "meta_barracks_2"),
    Place("market_2", MARKET, 2, "meta_market"),
    Place("archery_range_2", ARCHERY_RANGE, 2, "meta_archery_range"),
    Place("stable_2", STABLE, 2, "meta_stable"),
    Place("town_center_3", TOWN_CENTER, 3),
    Place("granary_3", GRANARY, 3),
    Place("storage_pit_3", STORAGE_PIT, 3),
    Place("market_3", MARKET, 3, "meta_market"),
    Place("barracks_3", BARRACKS, 3, "meta_barracks_2"),
    Place("archery_range_3", ARCHERY_RANGE, 3, "meta_archery_range"),
    Place("stable_3", STABLE, 3, "meta_stable"),
    Place("government_center_3", GOVERNMENT_CENTER, 3, "meta_government_center"),
    Place("tower_2", WATCH_TOWER, 2, "meta_tower"),  # ruin and artifact stages (playtest 2026-11-23)
    Place("tower_3", SENTRY_TOWER, 3, "meta_sentry_tower"),
    Place("tower_4", GUARD_TOWER, 4, "meta_guard_tower"),
    Place("temple_3", TEMPLE, 3, "meta_temple"),
    Place("town_center_4", TOWN_CENTER, 4),
    Place("granary_4", GRANARY, 4),
    Place("storage_pit_4", STORAGE_PIT, 4),
    Place("market_4", MARKET, 4, "meta_market"),
    Place("barracks_4", BARRACKS, 4, "meta_barracks_2"),
    Place("archery_range_4", ARCHERY_RANGE, 4, "meta_archery_range"),
    Place("stable_4", STABLE, 4, "meta_stable"),
    Place("academy_4", ACADEMY, 4, "meta_academy"),
    Place("siege_workshop_4", SIEGE_WORKSHOP, 4, "meta_siege_workshop"),
    Place("government_center_4", GOVERNMENT_CENTER, 4, "meta_government_center"),
    Place("temple_4", TEMPLE, 4, "meta_temple"),
    Place("barracks_5", BARRACKS, 5, "meta_barracks_2"),
    Place("archery_range_5", ARCHERY_RANGE, 5, "meta_archery_range"),
    Place("stable_5", STABLE, 5, "meta_stable"),
    Place("academy_5", ACADEMY, 5, "meta_academy"),
    Place("siege_workshop_5", SIEGE_WORKSHOP, 5, "meta_siege_workshop"),
)

# ---- the Wonder: global upgrades, more as the tiers open ----
STARTING_RESOURCES = Upgrade(
    "meta_starting_resources",
    "Starting resources",
    "Start each run with 50 more food and wood, 20 more gold and stone.",
    "wonder",
    1,
    5,
    tier=1,
    label="starting resources",
)
TOWN_CENTER_SPEEDS = 5  # percent faster a level (took in Quick villagers' +10% x 5, playtest 2026-11-23)
TOWN_CENTER_SPEED = Upgrade(
    "meta_town_center_speed",
    "Busy Town Centers",
    f"Town Centers work {TOWN_CENTER_SPEEDS}% faster a level: training and research.",
    "wonder",
    2,
    10,
    tier=1,
    label="town center speed",
    caps=((1, 5), (4, 10)),
    texts=tuple(
        f"Town Centers work {TOWN_CENTER_SPEEDS * (n + 1)}% faster with the next level (now {TOWN_CENTER_SPEEDS * n}%)."
        for n in range(10)
    )
    + (f"Town Centers work {TOWN_CENTER_SPEEDS * 10}% faster: every level bought.",),
)
BOON_SLOTS = Upgrade(
    "meta_boon_slots",
    "More boons",
    "Each decision offers one more boon.",
    "wonder",
    3,
    4,
    tier=3,
    label="boons per decision",
    caps=((3, 2), (4, 3), (5, 4)),
)
BOON_SPEED = Upgrade(
    "meta_boon_speed",
    "Faster boons",
    "Boons research faster: 1 second at the fifth level.",
    "wonder",
    4,
    5,
    tier=3,
    label="boon speed",
)
FOOD_DENSITY = Upgrade(
    "meta_food_density", "Rich hunting", "Food and fish last twice as long.", "wonder", 5, tier=3
)
WOOD_DENSITY = Upgrade("meta_wood_density", "Rich forests", "Trees last twice as long.", "wonder", 6, tier=3)
MINING_DENSITY = Upgrade(
    "meta_mining_density", "Rich mines", "Gold and stone mines last twice as long.", "wonder", 7, tier=3
)
VILLAGER_COST = Upgrade("meta_villager_cost", "Cheap villagers", "Villagers cost 5 food less.", "wonder", 9, 5, tier=4)
BOON_DISCOUNTS = (15, 12, 10, 9, 8, 6, 5, 4, 3, 3)  # percent off boons each level adds: 75% at the tenth
BOON_DISCOUNT = Upgrade(
    "meta_boon_discount",
    "Cheaper boons",
    "Boons cost less: 15% off at the first level, 75% at the tenth.",
    "wonder",
    10,
    len(BOON_DISCOUNTS),
    tier=1,
    label="boon discount",
    texts=tuple(
        f"The next level takes {BOON_DISCOUNTS[n]}% more off boons: {sum(BOON_DISCOUNTS[: n + 1])}% off in all "
        f"(now {sum(BOON_DISCOUNTS[:n])}%)."
        for n in range(len(BOON_DISCOUNTS))
    )
    + (f"Boons cost {sum(BOON_DISCOUNTS)}% less: every level bought.",),
)
RUIN_SPOTS, ARTIFACT_SPOTS = 7, 5  # on the arena: a level keeps one more, at random
RUINS = Upgrade(
    "meta_ruins",
    "Ruins",
    f"One more ruin on the map each run (of {RUIN_SPOTS}, at random). The towers' upgrades make ruins pay.",
    "wonder",
    11,
    RUIN_SPOTS,
    tier=2,
    label="ruins",
)
ARTIFACTS = Upgrade(
    "meta_artifacts",
    "Artifacts",
    f"One more artifact on the map each run (of {ARTIFACT_SPOTS}, at random). Garrison one in a building: the towers' "
    "upgrades boost every building of its type.",
    "wonder",
    12,
    ARTIFACT_SPOTS,
    tier=2,
    label="artifacts",
)

# ---- the towers: what ruins and artifacts do, a stage a tower (playtest 2026-11-23) ----
RUIN_TRICKLE_RATE = 0.5  # of each resource a second, a ruin
RUIN_ROOM_EACH = 25  # population room a ruin (50 was too much, playtest 2026-11-24)
RUIN_CAP_EACH = 20  # population limit a ruin
ARTIFACT_SPEED_PERCENT = 15
ARTIFACT_DISCOUNT_PERCENT = 20
ARTIFACT_TRICKLES = {"Granary": (("food", 2, 20),), "Storage Pit": (("wood", 2, 20),)}  # a second: each, at most
ARTIFACT_TRICKLES["Town Center"] = (("gold", 1, 10), ("stone", 1, 10))
# The regeneration attribute (109) looks to show as twice its value a minute: 60 on towers gave 2 HP a second
# (playtest 2026-11-24; to confirm). The HP a minute below are what shows; the attribute gets half.
REGENERATION_SHOWN = 2
ARTIFACT_REGENERATION = 30  # tower HP a minute an artifact (a quarter of the 120 that showed)
ARTIFACT_UNIT_REGENERATION = 15  # HP a minute an artifact gives the units its building type trains
ARTIFACT_CART_REGENERATION = 120  # the artifact's own HP a minute (of 5000)
RUIN_TRICKLE = Upgrade(
    "meta_ruin_trickle",
    "Ruin trickle",
    f"Each ruin you hold gives {RUIN_TRICKLE_RATE} food, wood, gold and stone a second.",
    "tower_2",
    1,
    requires=(("meta_ruins", 1),),
)
ARTIFACT_SPEED = Upgrade(
    "meta_artifact_speed",
    "Artifact: production",
    f"An artifact garrisoned in a building makes every building of its type work {ARTIFACT_SPEED_PERCENT}% faster.",
    "tower_2",
    2,
    requires=(("meta_artifacts", 1),),
)
RUIN_ROOM = Upgrade(
    "meta_ruin_room",
    "Ruin housing",
    f"Each ruin you hold gives {RUIN_ROOM_EACH} population room.",
    "tower_3",
    1,
    requires=(("meta_ruin_trickle", 1),),
)
ARTIFACT_COST = Upgrade(
    "meta_artifact_cost",
    "Artifact: discount",
    f"The units and techs of a building type with an artifact garrisoned cost {ARTIFACT_DISCOUNT_PERCENT}% less.",
    "tower_3",
    2,
    requires=(("meta_artifact_speed", 1),),
)
RUIN_CAP = Upgrade(
    "meta_ruin_cap",
    "Ruin population",
    f"Each ruin you hold raises your population limit by {RUIN_CAP_EACH}.",
    "tower_4",
    1,
    requires=(("meta_ruin_room", 1),),
)
ARTIFACT_SPECIAL = Upgrade(
    "meta_artifact_special",
    "Artifact: bounty",
    "An artifact in a Granary: each Granary gives 2 food a second (20 at most); in a Storage Pit: 2 wood (20); in a "
    f"Town Center: 1 gold and 1 stone (10 each); in a tower: towers regenerate {ARTIFACT_REGENERATION} HP a minute. "
    f"The units a building of its type trains regenerate {ARTIFACT_UNIT_REGENERATION} HP a minute (Barracks: "
    "infantry; Dock: ships; Town Center: villagers). Each artifact adds more.",
    "tower_4",
    2,
    requires=(("meta_artifact_cost", 1),),
)

# ---- tier 1, player 2: a bigger start ----
VILLAGERS_UPGRADE = Upgrade(
    "meta_villagers",
    "Villager",
    "Start each run with one more villager.",
    "town_center_1",
    1,
    6,
    label="villagers",
    shows=VILLAGER_TYPES,
)
STARTING_HOUSES = START_GIVEN[HOUSE]  # of the base's houses, the player's in every run (and in the hub)
HOUSES = Upgrade(
    "meta_houses",
    "House",
    f"Start each run with one more of your base's houses (you always have {STARTING_HOUSES}): yours, at full health.",
    "town_center_1",
    2,
    5,
    label="houses",
    shows=(HOUSE,),
)
GRANARY_UPGRADE = Upgrade(
    "meta_granary",
    "Granary",
    "Start each run with your base's Granary.",
    "town_center_1",
    3,
    label="Granary",
    shows=(GRANARY,),
)
STORAGE_PIT_UPGRADE = Upgrade(
    "meta_storage_pit",
    "Storage Pit",
    "Start each run with your base's Storage Pit.",
    "town_center_1",
    4,
    label="Storage Pit",
    shows=(STORAGE_PIT,),
)
BARRACKS_UPGRADE = Upgrade(
    "meta_barracks",
    "Barracks",
    "Start each run with a Barracks.",
    "town_center_1",
    5,
    label="Barracks",
    shows=(BARRACKS,),
)
CLUBMEN_PER_LEVEL = 3
CLUBMEN = Upgrade(
    "meta_clubmen",
    "Clubmen",
    "Start each run with 3 Clubmen by your Barracks.",
    "barracks_1",
    1,
    label="Clubmen",
    amounts=(CLUBMEN_PER_LEVEL,),
    shows=(CLUBMAN,),
    per=(CLUBMEN_PER_LEVEL,),
)

# ---- tier 2, player 3: a full Tool Age ----
SECOND_BARRACKS = Upgrade(
    "meta_barracks_2",
    "Second Barracks",
    "Start each run with your base's second Barracks.",
    "town_center_2",
    1,
    label="second Barracks",
    shows=(BARRACKS,),
)
MARKET_UPGRADE = Upgrade(
    "meta_market",
    "Market",
    "Start each run with your base's Market.",
    "town_center_2",
    2,
    label="Market",
    shows=(MARKET,),
)
ARCHERY_RANGE_UPGRADE = Upgrade(
    "meta_archery_range",
    "Archery Range",
    "Start each run with your base's Archery Range.",
    "town_center_2",
    3,
    label="Archery Range",
    shows=(ARCHERY_RANGE,),
)
STABLE_UPGRADE = Upgrade(
    "meta_stable",
    "Stable",
    "Start each run with your base's Stable.",
    "town_center_2",
    4,
    label="Stable",
    shows=(STABLE,),
)
AXE = Upgrade(
    "meta_axe",
    "Axemen upgrade",
    "Axe (Clubmen to Axemen) can be researched at the Barracks, and your 3 starting Clubmen are Axemen.",
    "barracks_2",
    1,
    label="Axe",
    amounts=(3,),
    requires=(("meta_clubmen", 1),),
    shows=(AXEMAN,),
    per=(3,),
)
AXEMEN = Upgrade(
    "meta_axemen",
    "Axemen",
    "Start each run with 2 more Axemen.",
    "barracks_2",
    2,
    label="Axemen",
    amounts=(2,),
    requires=(("meta_axe", 1),),
    shows=(AXEMAN,),
    per=(2,),
)
MARKET_TECHS = Upgrade(
    "meta_market_techs",
    "Market upgrades",
    "The Market's Tool Age upgrades can be researched.",
    "market_2",
    1,
    label="Market upgrades",
)
BOWMEN = Upgrade(
    "meta_bowmen",
    "Bowmen",
    "Start each run with 3 Bowmen; the second level adds 2 more.",
    "archery_range_2",
    1,
    2,
    label="Bowmen",
    amounts=(3, 2),
    shows=(BOWMAN,),
    per=(3, 2),
)
SCOUT = Upgrade("meta_scout", "Scout", "Start each run with a Scout.", "stable_2", 1, label="Scout", shows=(SCOUT,))
STORAGE_PIT_TECHS = Upgrade(
    "meta_storage_pit_techs",
    "Storage Pit upgrades",
    "The Storage Pit's Tool Age upgrades can be researched.",
    "storage_pit_2",
    1,
    label="Storage Pit upgrades",
)
TOWER = Upgrade(
    "meta_tower",
    "Watch Tower",
    "Start each run with your base's towers, and Watch Towers can be researched.",
    "granary_2",
    1,
    label="Watch Tower",
)
# No wall upgrades (playtest 2026-11-24: walls wrecked the waves' pathing and made them trivial): the base's walls
# are the Allies', heavily damaged or broken in places (run_xs.WALL_STATES).

# ---- tier 3, player 4: the Bronze Age ----
ACADEMY_UPGRADE = Upgrade(
    "meta_academy",
    "Academy",
    "Start each run with an Academy; Hoplites can be trained.",
    "town_center_3",
    1,
    shows=(ACADEMY,),
)
GOVERNMENT_CENTER_UPGRADE = Upgrade(
    "meta_government_center",
    "Government Center",
    "Start each run with a Government Center.",
    "town_center_3",
    2,
    shows=(GOVERNMENT_CENTER,),
)
SIEGE_WORKSHOP_UPGRADE = Upgrade(
    "meta_siege_workshop",
    "Siege Workshop",
    "Siege Workshops can be built, and Stone Throwers trained.",
    "town_center_3",
    3,
    shows=(SIEGE_WORKSHOP,),
)
TEMPLE_UPGRADE = Upgrade("meta_temple", "Temple", "Start each run with a Temple.", "town_center_3", 4, shows=(TEMPLE,))
SENTRY_TOWER = Upgrade(
    "meta_sentry_tower",
    "Sentry Tower",
    "Your starting towers are Sentry Towers, and Sentry Tower can be researched.",
    "granary_3",
    1,
    requires=(("meta_tower", 1),),
)
STORAGE_PIT_TECHS_2 = Upgrade(
    "meta_storage_pit_techs_2", "Storage Pit upgrades II", "The Storage Pit's Bronze Age upgrades.", "storage_pit_3", 1
)
MARKET_TECHS_2 = Upgrade(
    "meta_market_techs_2", "Market upgrades II", "The Market's Bronze Age upgrades.", "market_3", 1
)
WHEEL = Upgrade("meta_wheel", "Wheel", "Wheel, and Chariots can be trained.", "market_3", 2)
SHORT_SWORD = Upgrade(
    "meta_short_sword",
    "Short Swordsmen",
    "Your starting melee are Short Swordsmen, and Short Swordsmen can be trained.",
    "barracks_3",
    1,
    requires=(("meta_axe", 1),),
    shows=(SHORT_SWORDSMAN,),
)
BROAD_SWORD = Upgrade(
    "meta_broad_sword",
    "Broad Swordsmen",
    "Your starting melee are Broad Swordsmen, and Broad Sword can be researched.",
    "barracks_3",
    2,
    requires=(("meta_short_sword", 1),),
    shows=(BROAD_SWORDSMAN,),
)
IMPROVED_BOW = Upgrade(
    "meta_improved_bow",
    "Improved Bowmen",
    "Your starting Bowmen are Improved Bowmen, and Improved Bow can be researched.",
    "archery_range_3",
    1,
    requires=(("meta_bowmen", 1),),
    shows=(IMPROVED_BOWMAN,),
)
COMPOSITE_BOW = Upgrade(
    "meta_composite_bow",
    "Composite Bowmen",
    "Your starting Bowmen are Composite Bowmen, and Composite Bow can be researched.",
    "archery_range_3",
    2,
    requires=(("meta_improved_bow", 1),),
    shows=(COMPOSITE_BOWMAN,),
)
CAMEL = Upgrade("meta_camel", "Camel Riders", "Camel Riders can be trained.", "stable_3", 1)
CAVALRY_UPGRADE = Upgrade(
    "meta_cavalry",
    "Cavalry",
    "Cavalry can be trained, and each level starts each run with one more.",
    "stable_3",
    2,
    3,
    shows=(CAVALRY,),
)
GOVERNMENT_TECHS = Upgrade(
    "meta_government_techs",
    "Government upgrades",
    "The Government Center's Bronze Age upgrades.",
    "government_center_3",
    1,
)
TEMPLE_TECHS = Upgrade("meta_temple_techs", "Temple upgrades", "The Temple's Bronze Age upgrades.", "temple_3", 1)
# the Dock's rows at the Town Centers (the hub map has no Dock); the Tool Age has none: its ships come free
DOCK_TECHS = Upgrade("meta_dock_techs", "Dock upgrades", "The Dock's Bronze Age upgrades.", "town_center_3", 5)

# ---- tier 4, player 5: the Iron Age ----
GUARD_TOWER = Upgrade(
    "meta_guard_tower",
    "Guard Tower",
    "Your starting towers are Guard Towers, and Guard Tower can be researched.",
    "granary_4",
    1,
    requires=(("meta_sentry_tower", 1),),
)
STORAGE_PIT_TECHS_3 = Upgrade(
    "meta_storage_pit_techs_3", "Storage Pit upgrades III", "The Storage Pit's Iron Age upgrades.", "storage_pit_4", 1
)
MARKET_TECHS_3 = Upgrade("meta_market_techs_3", "Market upgrades III", "The Market's Iron Age upgrades.", "market_4", 1)
LONG_SWORD = Upgrade(
    "meta_long_sword",
    "Long Swordsmen",
    "Your starting melee are Long Swordsmen, and Long Sword can be researched.",
    "barracks_4",
    1,
    requires=(("meta_broad_sword", 1),),
    shows=(LONG_SWORDSMAN,),
)
HORSE_ARCHERS = Upgrade(
    "meta_horse_archer",
    "Horse Archers",
    "Your starting Bowmen are Horse Archers, and Horse Archers can be trained.",
    "archery_range_4",
    1,
    shows=(HORSE_ARCHER,),
)
HEAVY_CAVALRY_UPGRADE = Upgrade(
    "meta_heavy_cavalry",
    "Heavy Cavalry",
    "Your starting Cavalry are Heavy Cavalry, and Heavy Cavalry can be researched.",
    "stable_4",
    1,
    requires=(("meta_cavalry", 1),),
    shows=(HEAVY_CAVALRY,),
)
PHALANGITE = Upgrade(
    "meta_phalangite", "Phalangites", "Phalanx (Hoplites to Phalangites) can be researched.", "academy_4", 1
)
CATAPULT_UPGRADE = Upgrade("meta_catapult", "Catapults", "Catapults can be researched.", "siege_workshop_4", 1)
BALLISTA_UPGRADE = Upgrade("meta_ballista", "Ballistas", "Ballistas can be trained.", "siege_workshop_4", 2)
GOVERNMENT_TECHS_2 = Upgrade(
    "meta_government_techs_2",
    "Government upgrades II",
    "The Government Center's Iron Age upgrades.",
    "government_center_4",
    1,
)
TEMPLE_TECHS_2 = Upgrade("meta_temple_techs_2", "Temple upgrades II", "The Temple's Iron Age upgrades.", "temple_4", 1)
DOCK_TECHS_2 = Upgrade(
    "meta_dock_techs_2", "Dock upgrades II", "The Dock's Iron Age upgrades.", "town_center_4", 1
)

# ---- tier 5, player 6: the last units (they don't upgrade your starting units) ----
LEGIONARY_UPGRADE = Upgrade(
    "meta_legionary",
    "Legionaries",
    "Legion can be researched.",
    "barracks_5",
    1,
    requires=(("meta_long_sword", 1),),
    shows=(LEGIONARY,),
)
HEAVY_HORSE_ARCHERS = Upgrade(
    "meta_heavy_horse_archer",
    "Heavy Horse Archers",
    "Heavy Horse Archer can be researched.",
    "archery_range_5",
    1,
    requires=(("meta_horse_archer", 1),),
    shows=(HEAVY_HORSE_ARCHER,),
)
ELEPHANT_ARCHERS = Upgrade(
    "meta_elephant_archer",
    "Elephant Archers",
    "Elephant Archers can be trained.",
    "archery_range_5",
    2,
    shows=(ELEPHANT_ARCHER,),
)
CATAPHRACTS = Upgrade(
    "meta_cataphract",
    "Cataphracts",
    "Cataphracts can be researched.",
    "stable_5",
    1,
    requires=(("meta_heavy_cavalry", 1),),
    shows=(CATAPHRACT,),
)
WAR_ELEPHANTS = Upgrade(
    "meta_war_elephant", "War Elephants", "War Elephants can be trained.", "stable_5", 2, shows=(WAR_ELEPHANT,)
)
ARMORED_ELEPHANTS = Upgrade(
    "meta_armored_elephant",
    "Armored Elephants",
    "Armored Elephants can be researched.",
    "stable_5",
    3,
    requires=(("meta_war_elephant", 1),),
    shows=(ARMORED_ELEPHANT,),
)
SCYTHE_CHARIOTS = Upgrade(
    "meta_scythe_chariot",
    "Scythe Chariots",
    "Heavy Chariots can be researched.",
    "stable_5",
    4,
    requires=(("meta_wheel", 1),),
    shows=(SCYTHE_CHARIOT,),
)
CENTURIONS = Upgrade(
    "meta_centurion",
    "Centurions",
    "Centurion can be researched.",
    "academy_5",
    1,
    requires=(("meta_phalangite", 1),),
    shows=(CENTURION,),
)
HEAVY_CATAPULTS = Upgrade(
    "meta_heavy_catapult",
    "Heavy Catapults",
    "Heavy Catapult can be researched.",
    "siege_workshop_5",
    1,
    requires=(("meta_catapult", 1),),
    shows=(HEAVY_CATAPULT,),
)
HELEPOLISES = Upgrade(
    "meta_helepolis",
    "Helepolises",
    "Helepolis can be researched.",
    "siege_workshop_5",
    2,
    requires=(("meta_ballista", 1),),
    shows=(HELEPOLIS,),
)

# ---- the Trade Workshop: the run's extras (on the Wonder in the run: datamod/shop.py) ----
REROLL_GOLD = 500  # a reroll's price once the run's free ones are spent
REROLLS = Upgrade(
    "meta_rerolls",
    "Rerolls",
    "Each level is one free reroll a run: the Wonder rerolls the two boon categories on offer. Once they're spent, a "
    f"reroll costs {REROLL_GOLD} gold.",
    "trade_workshop",
    1,
    5,
    label="rerolls",
)
SPIES_GOLD = 5000
SPIES = Upgrade(
    "meta_spies",
    "Spies",
    f"The Wonder can research Spies in the run ({SPIES_GOLD} gold): the whole map visible.",
    "trade_workshop",
    2,
    label="spies",
)

WONDER_TRICKLE_RATE = 0.5  # of each resource a second, a level (a ruin's worth)
WONDER_TRICKLE = Upgrade(
    "meta_wonder_trickle",
    "Tribute",
    f"While your Wonder stands, it gives {WONDER_TRICKLE_RATE} food, wood, gold and stone a second in the run, "
    "more each level.",
    "trade_workshop",
    3,
    3,
    label="Wonder trickle",
    texts=tuple(
        f"Your Wonder gives {WONDER_TRICKLE_RATE * (n + 1)} of each resource a second with the next level (now "
        f"{WONDER_TRICKLE_RATE * n})."
        for n in range(3)
    )
    + (f"Your Wonder gives {WONDER_TRICKLE_RATE * 3} of each resource a second: every level bought.",),
)

UPGRADES = (  # Clubmen before the Axemen upgrade: the hub swaps the Clubmen for Axemen
    STARTING_RESOURCES,
    TOWN_CENTER_SPEED,
    BOON_SLOTS,
    BOON_SPEED,
    FOOD_DENSITY,
    WOOD_DENSITY,
    MINING_DENSITY,
    VILLAGER_COST,
    BOON_DISCOUNT,
    RUINS,
    ARTIFACTS,
    VILLAGERS_UPGRADE,
    HOUSES,
    GRANARY_UPGRADE,
    STORAGE_PIT_UPGRADE,
    BARRACKS_UPGRADE,
    CLUBMEN,
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
    ACADEMY_UPGRADE,
    GOVERNMENT_CENTER_UPGRADE,
    SIEGE_WORKSHOP_UPGRADE,
    TEMPLE_UPGRADE,
    SENTRY_TOWER,
    STORAGE_PIT_TECHS_2,
    MARKET_TECHS_2,
    WHEEL,
    SHORT_SWORD,
    BROAD_SWORD,
    IMPROVED_BOW,
    COMPOSITE_BOW,
    CAMEL,
    CAVALRY_UPGRADE,
    GOVERNMENT_TECHS,
    TEMPLE_TECHS,
    DOCK_TECHS,
    GUARD_TOWER,
    STORAGE_PIT_TECHS_3,
    MARKET_TECHS_3,
    LONG_SWORD,
    HORSE_ARCHERS,
    HEAVY_CAVALRY_UPGRADE,
    PHALANGITE,
    CATAPULT_UPGRADE,
    BALLISTA_UPGRADE,
    GOVERNMENT_TECHS_2,
    TEMPLE_TECHS_2,
    DOCK_TECHS_2,
    LEGIONARY_UPGRADE,
    HEAVY_HORSE_ARCHERS,
    ELEPHANT_ARCHERS,
    CATAPHRACTS,
    WAR_ELEPHANTS,
    ARMORED_ELEPHANTS,
    SCYTHE_CHARIOTS,
    CENTURIONS,
    HEAVY_CATAPULTS,
    HELEPOLISES,
    RUIN_TRICKLE,
    ARTIFACT_SPEED,
    RUIN_ROOM,
    ARTIFACT_COST,
    RUIN_CAP,
    ARTIFACT_SPECIAL,
    REROLLS,
    SPIES,
    WONDER_TRICKLE,
)
VILLAGERS = VILLAGERS_UPGRADE  # the name the run knows it by (the unit types are VILLAGER_TYPES)


@dataclass(frozen=True)
class Reward:
    """Given, not bought: reaching `tier` stores 1 under `key` (the hub's tier objective does it)."""

    key: str
    title: str
    tier: int


BRONZE_AGE = Reward("meta_bronze_age", "Bronze Age", 3)  # the Bronze Age can be researched in the run
IRON_AGE = Reward("meta_iron_age", "Iron Age", 4)  # the Iron Age can be researched in the run
REWARDS = (BRONZE_AGE, IRON_AGE)
KEYS = tuple(k.key for k in (*UPGRADES, *REWARDS))  # everything kept in the bank
TITLES = {k.key: k.title for k in (*UPGRADES, *REWARDS)}


def place(key: str) -> Place:
    return next(p for p in PLACES if p.key == key)


def tier_of(upgrade: Upgrade) -> int:
    """The tier an upgrade is on offer from: its own, or its place's."""
    return upgrade.tier or max(place(upgrade.place).tier, 1)


def location(p: Place, techs: dict[str, int]) -> int:
    """The type a place's techs are researched at: its copy's (the Wonder's own type)."""
    return techs[p.copy_key] if p.copy else p.unit
