"""What each wave of crucible_run brings (docs/waves.md): by difficulty, the Legion's age and each group's size; by
archetype, which units.

A wave is one group per lane: the Capital's two lanes, or one from each City State; wave 0 is the Capital's, and wave
9 (and any after it, fighting on) all four. A group is its main units (about 70%), the other units (the rest, at least
one; wave 0 is Clubmen only) and siege. Each lane rolls an archetype at the start of a run (no two the same); it
picks the units from the Legion's Tool Age on, and before that every group is Clubmen and Slingers.

Struggling is the point: the Legion ages on its own clock, and the player keeps up through the meta and the boons.
"""

from dataclasses import dataclass
from enum import IntEnum

from aoe2ed import tables

WAVES = 10  # 0 to 9; to defeat for victory
ALL_LANES_FROM = 9  # this wave and after: every lane
MAIN_SHARE = 0.7


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


# The game's difficulty constants (xsGetDifficulty) to ours: Easiest and Standard are Standard; Hard, Hardest and
# Extreme are Hard.
GAME_DIFFICULTY = {4: Difficulty.STANDARD, 3: Difficulty.STANDARD, 2: Difficulty.MODERATE, 1: Difficulty.HARD}
FALLBACK = Difficulty.HARD  # 0 (Hardest), -1 (Extreme)

# The wave at which the Legion reaches each age.
LEGION_AGES = {
    Difficulty.STANDARD: {Age.TOOL: 4, Age.BRONZE: 6, Age.IRON: 8, Age.POST_IRON: 9},
    Difficulty.MODERATE: {Age.TOOL: 3, Age.BRONZE: 5, Age.IRON: 7, Age.POST_IRON: 9},
    Difficulty.HARD: {Age.TOOL: 2, Age.BRONZE: 4, Age.IRON: 6, Age.POST_IRON: 8},
}


@dataclass(frozen=True)
class Group:
    main: int
    other: int
    siege: int = 0

    @property
    def units(self) -> int:
        return self.main + self.other + self.siege


def mix(main: int, other: int) -> Group:
    """Exact numbers (the Stone waves: Clubmen, Slingers)."""
    return Group(main, other)


def units(count: int, siege: int = 0) -> Group:
    """`count` units split about 70/30 by the archetype, at least one of each, and `siege`."""
    main = min(max(round(count * MAIN_SHARE), 1), count - 1)

    return Group(main, count - main, siege)


# Per group, waves 0 to 9.
GROUPS = {
    Difficulty.STANDARD: (
        mix(3, 0),  # wave 0: melee only
        mix(3, 1),
        mix(3, 1),
        units(5),
        units(6),
        units(7),
        units(8, 1),
        units(9, 1),
        units(10, 2),
        units(11, 3),
    ),
    Difficulty.MODERATE: (
        mix(4, 0),
        mix(4, 1),
        mix(4, 2),
        units(7),
        units(8),
        units(9, 1),
        units(10, 1),
        units(11, 2),
        units(13, 2),
        units(15, 3),
    ),
    Difficulty.HARD: (
        mix(5, 0),
        mix(4, 2),
        units(7),
        units(8),
        units(10, 1),
        units(11, 1),
        units(13, 2),
        units(14, 2),
        units(16, 3),
        units(18, 4),
    ),
}

# One Priest per group from this age on.
PRIESTS = {Difficulty.MODERATE: Age.IRON, Difficulty.HARD: Age.BRONZE}

STONE = (("clubman",), ("slinger",))  # every group before the Legion's Tool Age: main, other

# Siege by age, taken in turn.
SIEGE = {
    Age.BRONZE: ("stone_thrower",),
    Age.IRON: ("catapult", "ballista"),
    Age.POST_IRON: ("heavy_catapult", "helepolis"),
}


@dataclass(frozen=True)
class Archetype:
    name: str
    ages: dict[Age, tuple[tuple[str, ...], tuple[str, ...]]]  # Tool on: (main units, other units), one at random


ARCHETYPES = (
    Archetype(
        "Swordsmen",
        {
            Age.TOOL: (("axeman",), ("bowman",)),
            Age.BRONZE: (("short_swordsman", "broad_swordsman"), ("improved_bowman",)),
            Age.IRON: (("long_swordsman",), ("composite_bowman",)),
            Age.POST_IRON: (("legionary",), ("composite_bowman",)),
        },
    ),
    Archetype(
        "Phalanx",
        {
            Age.TOOL: (("axeman",), ("slinger",)),
            Age.BRONZE: (("hoplite",), ("slinger", "improved_bowman")),
            Age.IRON: (("phalangite",), ("composite_bowman",)),
            Age.POST_IRON: (("centurion",), ("composite_bowman",)),
        },
    ),
    Archetype(
        "Cavalry",
        {
            Age.TOOL: (("scout",), ("bowman",)),
            Age.BRONZE: (("cavalry", "camel_rider"), ("chariot_archer",)),
            Age.IRON: (("heavy_cavalry",), ("horse_archer",)),
            Age.POST_IRON: (("cataphract",), ("heavy_horse_archer",)),
        },
    ),
    Archetype(
        "Elephants",
        {
            Age.TOOL: (("scout",), ("bowman",)),
            Age.BRONZE: (("chariot",), ("improved_bowman",)),
            Age.IRON: (("war_elephant",), ("elephant_archer",)),
            Age.POST_IRON: (("armored_elephant",), ("elephant_archer",)),
        },
    ),
    Archetype(
        "Bowmen",
        {
            Age.TOOL: (("bowman", "slinger"), ("axeman",)),
            Age.BRONZE: (("improved_bowman", "composite_bowman"), ("short_swordsman",)),
            Age.IRON: (("composite_bowman", "elephant_archer"), ("long_swordsman",)),
            Age.POST_IRON: (("composite_bowman", "elephant_archer"), ("legionary",)),
        },
    ),
    Archetype(
        "Horse archers",
        {
            Age.TOOL: (("bowman",), ("scout",)),
            Age.BRONZE: (("chariot_archer",), ("cavalry",)),
            Age.IRON: (("horse_archer",), ("heavy_cavalry",)),
            Age.POST_IRON: (("heavy_horse_archer",), ("cataphract",)),
        },
    ),
    Archetype(
        "Chariots",
        {
            Age.TOOL: (("scout",), ("bowman",)),
            Age.BRONZE: (("chariot",), ("chariot_archer",)),
            Age.IRON: (("scythe_chariot",), ("chariot_archer",)),
            Age.POST_IRON: (("scythe_chariot",), ("elephant_archer",)),
        },
    ),
)


def legion_age(difficulty: Difficulty, wave: int) -> Age:
    reached = [age for age, at in LEGION_AGES[difficulty].items() if wave >= at]

    return max(reached, default=Age.STONE)


def group(difficulty: Difficulty, wave: int) -> Group:
    """The group size of `wave`; waves after the last repeat it."""
    groups = GROUPS[difficulty]

    return groups[min(wave, len(groups) - 1)]


def choices(archetype: Archetype, age: Age) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return STONE if age == Age.STONE else archetype.ages[age]


def unit_id(name: str) -> int:
    return tables.object_id(name.upper(), "ror")
