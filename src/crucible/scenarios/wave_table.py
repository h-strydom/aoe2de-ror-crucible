"""How the waves of crucible_run evolve (docs/evolving-waves.md): no set sizes or ages, an army per lane that takes a
step each time it's about to spawn.

Each lane has two slots, melee and ranged, each a unit line and a count; its archetype (rolled at the start, no two
the same) says which lines it may swap to and which slot is its main kind. The Legion's age and its upgrades are
shared: one lane's step can age up or upgrade every lane's units, and that lane doesn't grow that time.

A step: first the age-up roll (AGE_UP_START percent, + AGE_UP_STEP for every step without one, back after one), else
one of STEPS by weight. An upgrade is only rolled if it improves a unit some lane fields (or siege and priests, once
the Legion can bring them); a swap prefers a slot whose line is behind the Legion's age. Siege and Priests come and go:
each wave a lane may bring them, by chance per age.
"""

from dataclasses import dataclass
from enum import IntEnum

from aoe2ed import tables


class Difficulty(IntEnum):
    STANDARD = 0
    MODERATE = 1
    HARD = 2


class Age(IntEnum):
    STONE = 0
    TOOL = 1
    BRONZE = 2
    IRON = 3
    POST_IRON = 4

    @property
    def title(self) -> str:
        return "Post-Iron Age" if self == Age.POST_IRON else f"{self.name.title()} Age"


class Slot(IntEnum):
    MELEE = 0
    RANGED = 1


class Step(IntEnum):
    GROW = 0
    UPGRADE = 1
    SWAP = 2
    NOTHING = 3
    AGAIN = 4  # two more steps (each may be AGAIN again)


# The game's difficulty constants (xsGetDifficulty) to ours: Easiest and Standard are Standard; Hard, Hardest and
# Extreme are Hard.
GAME_DIFFICULTY = {4: Difficulty.STANDARD, 3: Difficulty.STANDARD, 2: Difficulty.MODERATE, 1: Difficulty.HARD}
FALLBACK = Difficulty.HARD  # 0 (Hardest), -1 (Extreme)
SEND_TIMES = {Difficulty.STANDARD: 300, Difficulty.MODERATE: 180, Difficulty.HARD: 120}  # seconds between waves

STEPS = {Step.GROW: 45, Step.UPGRADE: 30, Step.SWAP: 25, Step.NOTHING: 0, Step.AGAIN: 0}  # weights
AGE_UP_START = 2  # percent
AGE_UP_STEP = 2  # percent more for every step without an age up
MAX_STEPS = 8  # a lane's steps in one go at most (AGAIN can chain)
MAIN_SHARE = 65  # percent: a grown unit goes to the archetype's main slot
GROW_PER = 6  # a step grows the army by 1 per this many units (at least 1)
START = {Slot.MELEE: ("clubman", 2), Slot.RANGED: ("slinger", 2)}  # every lane's army before its first step

TIER_UP_PER_WAVE = 1  # percent added to each tier-up chance in the shop per wave defeated
DOUBLE_EVERY = 5  # every this many waves defeated: two boon choices


@dataclass(frozen=True)
class Line:
    unit: str
    slot: Slot
    age: Age

    @property
    def title(self) -> str:
        return self.unit.replace("_", " ").title()


LINES = (
    Line("clubman", Slot.MELEE, Age.STONE),
    Line("axeman", Slot.MELEE, Age.TOOL),
    Line("scout", Slot.MELEE, Age.TOOL),
    Line("short_swordsman", Slot.MELEE, Age.BRONZE),
    Line("broad_swordsman", Slot.MELEE, Age.BRONZE),
    Line("hoplite", Slot.MELEE, Age.BRONZE),
    Line("cavalry", Slot.MELEE, Age.BRONZE),
    Line("camel_rider", Slot.MELEE, Age.BRONZE),
    Line("chariot", Slot.MELEE, Age.BRONZE),
    Line("long_swordsman", Slot.MELEE, Age.IRON),
    Line("phalangite", Slot.MELEE, Age.IRON),
    Line("heavy_cavalry", Slot.MELEE, Age.IRON),
    Line("war_elephant", Slot.MELEE, Age.IRON),
    Line("scythe_chariot", Slot.MELEE, Age.IRON),
    Line("legionary", Slot.MELEE, Age.POST_IRON),
    Line("centurion", Slot.MELEE, Age.POST_IRON),
    Line("cataphract", Slot.MELEE, Age.POST_IRON),
    Line("armored_elephant", Slot.MELEE, Age.POST_IRON),
    Line("slinger", Slot.RANGED, Age.STONE),
    Line("bowman", Slot.RANGED, Age.TOOL),
    Line("improved_bowman", Slot.RANGED, Age.BRONZE),
    Line("composite_bowman", Slot.RANGED, Age.BRONZE),
    Line("chariot_archer", Slot.RANGED, Age.BRONZE),
    Line("horse_archer", Slot.RANGED, Age.IRON),
    Line("elephant_archer", Slot.RANGED, Age.IRON),
    Line("heavy_horse_archer", Slot.RANGED, Age.POST_IRON),
)
BY_UNIT = {line.unit: line for line in LINES}


@dataclass(frozen=True)
class Archetype:
    name: str
    main: Slot
    lines: tuple[str, ...]  # what its slots may hold (each slot the lines of its kind)


ARCHETYPES = (
    Archetype(
        "Swordsmen",
        Slot.MELEE,
        ("clubman", "axeman", "short_swordsman", "broad_swordsman", "long_swordsman", "legionary")
        + ("slinger", "bowman", "improved_bowman", "composite_bowman"),
    ),
    Archetype(
        "Phalanx",
        Slot.MELEE,
        ("clubman", "axeman", "hoplite", "phalangite", "centurion")
        + ("slinger", "bowman", "improved_bowman", "composite_bowman"),
    ),
    Archetype(
        "Cavalry",
        Slot.MELEE,
        ("clubman", "scout", "cavalry", "camel_rider", "heavy_cavalry", "cataphract")
        + ("slinger", "bowman", "chariot_archer", "horse_archer", "heavy_horse_archer"),
    ),
    Archetype(
        "Elephants",
        Slot.MELEE,
        ("clubman", "scout", "cavalry", "war_elephant", "armored_elephant")
        + ("slinger", "bowman", "improved_bowman", "elephant_archer"),
    ),
    Archetype(
        "Chariots",
        Slot.MELEE,
        ("clubman", "scout", "chariot", "scythe_chariot") + ("slinger", "bowman", "chariot_archer"),
    ),
    Archetype(
        "Bowmen",
        Slot.RANGED,
        ("clubman", "axeman", "short_swordsman", "long_swordsman", "legionary")
        + ("slinger", "bowman", "improved_bowman", "composite_bowman", "elephant_archer"),
    ),
    Archetype(
        "Horse archers",
        Slot.RANGED,
        ("clubman", "scout", "cavalry", "heavy_cavalry", "cataphract")
        + ("slinger", "bowman", "chariot_archer", "horse_archer", "heavy_horse_archer"),
    ),
)

# Siege and Priests: each wave, each lane brings them by chance (percent) from the Bronze Age.
SIEGE = {
    Age.BRONZE: ("stone_thrower",),
    Age.IRON: ("catapult", "ballista"),
    Age.POST_IRON: ("heavy_catapult", "helepolis"),
}
SIEGE_CHANCE = {Age.BRONZE: 20, Age.IRON: 30, Age.POST_IRON: 40}
PRIEST_CHANCE = {Age.BRONZE: 10, Age.IRON: 20, Age.POST_IRON: 25}
PRIEST = "priest"


@dataclass(frozen=True)
class Upgrade:
    name: str
    tech: int
    age: Age
    requires: int = -1  # an upgrade's tech that must come first


AGE_TECHS = {Age.TOOL: 101, Age.BRONZE: 102, Age.IRON: 103}  # the Post-Iron Age has none: its lines only
UPGRADES = (
    Upgrade("Tool Working", 46, Age.TOOL),
    Upgrade("Leather Armor (soldiers)", 40, Age.TOOL),
    Upgrade("Leather Armor (archers)", 41, Age.TOOL),
    Upgrade("Leather Armor (mounted)", 42, Age.TOOL),
    Upgrade("Metal Working", 51, Age.BRONZE, 46),
    Upgrade("Scale Armor (soldiers)", 43, Age.BRONZE, 40),
    Upgrade("Scale Armor (archers)", 44, Age.BRONZE, 41),
    Upgrade("Scale Armor (cavalry)", 45, Age.BRONZE, 42),
    Upgrade("Bronze Shield", 47, Age.BRONZE),
    Upgrade("Nobility", 34, Age.BRONZE),
    Upgrade("Mysticism", 21, Age.BRONZE),
    Upgrade("Astrology", 22, Age.BRONZE),
    Upgrade("Chain Mail (soldiers)", 48, Age.IRON, 43),
    Upgrade("Chain Mail (archers)", 49, Age.IRON, 44),
    Upgrade("Chain Mail (cavalry)", 50, Age.IRON, 45),
    Upgrade("Iron Shield", 117, Age.IRON, 47),
    Upgrade("Tower Shield", 122, Age.IRON, 117),
    Upgrade("Alchemy", 37, Age.IRON),
    Upgrade("Craftsmanship", 110, Age.IRON),
    Upgrade("Aristocracy", 113, Age.IRON),
    Upgrade("Engineering", 35, Age.IRON),
    Upgrade("Siege Craft", 111, Age.IRON),
    Upgrade("Afterlife", 18, Age.IRON),
)

STAT_EFFECTS = (0, 4, 5)  # set, add, multiply an attribute: an effect command a unit feels


def unit_id(name: str) -> int:
    return tables.object_id(name.upper(), "ror")


def specials() -> list[str]:
    """The units outside the slots an upgrade may help: siege of every age, and the Priest."""
    return [unit for units in SIEGE.values() for unit in units] + [PRIEST]


def improves(data, upgrade: Upgrade, unit: str) -> bool:
    """`upgrade`'s tech changes a stat of `unit` (by its id or its class), read from the data."""
    tech = data.techs[upgrade.tech]

    if tech.effect_id < 0:
        return False

    uid = unit_id(unit)
    klass = data.civs[1].units[uid].class_

    return any(
        command.type in STAT_EFFECTS and (command.a == uid or (command.a == -1 and command.b == klass))
        for command in data.effects[tech.effect_id].effect_commands
    )
