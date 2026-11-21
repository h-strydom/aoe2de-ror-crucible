"""How the waves of crucible_run evolve (docs/evolving-waves.md): no set sizes or ages, an army per lane that takes a
step each time it's about to spawn.

Units come in families (Swordsmen: Short, Broad, Long Swordsman, Legionary), each slot moving up its family's lines by
swaps (playtest 2026-11-21: shared line upgrades made the Bronze Age jump too far at once). Each lane rolls an
archetype at the start (no two the same): a main path for one slot and a support path for the other, each a chain of
families ("Clubmen, Swordsmen"); where a path has a choice ("Bowmen, then Chariot Archers or not") it's rolled once, at
the start. A lane's slot holds a family on its path, the line of it it's on, and a count.

A step: first the age-up roll (AGE_UP_START percent, + AGE_UP_STEP for every step without one, back after one), else
one of STEPS by weight:
- grow: units to the main slot (MAIN_SHARE percent of the time) or the support;
- upgrade: the Legion's (shared by every lane): a stat tech, but only one that improves a unit some lane fields (or
  siege and Priests, once the Legion can bring them);
- swap: a slot moves one step up: its family's next line if the Legion's age has opened it (Short to Broad Swordsmen,
  Improved to Composite Bowmen: the waves just spawn the better unit), else its path's next family, from that
  family's first line. A support slot never fields a Post-Iron line (MAIN_ONLY), so it stops a line short. With
  MOVE_ON (off since a playtest: one or two waves into the Bronze Age the lanes had jumped to Hoplites and Composite
  Bowmen), an age up also moves every main slot on as far as the new age opens.
Siege fields the furthest line its age has opened.
Each is done `scale` times: 1, plus 1 every SCALE_EVERY waves, times that step's own scale (GROW_SCALE, UPGRADE_SCALE,
SWAP_SCALE: what curses can raise later). An upgrade or swap that can't happen grows instead. Once the upgrades have
run out for good (none left in any age), the Legion takes boons instead (one that improves something it fields, its
tier rising with the scale).

Upgrades also count the Legion's own towers, walls and buildings (its bases): tower and wall lines, Architecture.

Support units (siege, Priests) come in support slots: one per WAVES_PER_SUPPORT waves. For each slot the wave's lanes
(in a random order) each roll their archetype's supports in its order of preference (SUPPORT_CHANCE each, once the
Legion's age has opened it); the first that comes up takes the slot, and a slot no lane fills stays empty.
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
    SIEGE = 2  # families the Legion brings by chance, not in a lane's slots


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


class Support(IntEnum):
    PRIEST = 0
    CATAPULT = 1  # the Stone Thrower family: Stone Thrower, Catapult, Heavy Catapult
    BALLISTA = 2  # Ballista, Helepolis


WAVES_PER_SUPPORT = 10  # a support slot per this many waves
SUPPORT_CHANCE = {Support.PRIEST: 30, Support.CATAPULT: 30, Support.BALLISTA: 30}  # percent, each roll
SUPPORT_FAMILY = {Support.CATAPULT: "Stone Throwers", Support.BALLISTA: "Ballistas"}  # the Priest is a unit
AGE_UP_START = 1  # percent
AGE_UP_STEP = 1  # percent more for every step without an age up
MAX_STEPS = 8  # a lane's steps in one go at most (AGAIN can chain)
MAIN_SHARE = 65  # percent: a grown unit goes to the archetype's main slot
SCALE_EVERY = 10  # waves: the scale goes up by 1
GROW_SCALE = 1  # units per grow, times the scale
UPGRADE_SCALE = 1  # upgrades per upgrade step, times the scale
SWAP_SCALE = 1  # families moved on per swap step, times the scale
MAIN_ONLY = Age.POST_IRON  # lines of this age (Legionaries, Centurions, Cataphracts...) only in a main slot
MOVE_ON = False  # an age up moves each lane's main slot on as far as the new age opens (off: Bronze came too fast)
START_COUNT = 2  # units in each slot before a lane's first step

TIER_UP_PER_WAVE = 1  # percent added to each tier-up chance in the shop per wave defeated
DOUBLE_EVERY = 5  # every this many waves defeated: two boon choices


@dataclass(frozen=True)
class Line:
    unit: str
    age: Age  # when the Legion can field it
    tech: int = -1  # the tech that upgrades the family to it (-1: the family's first)

    @property
    def title(self) -> str:
        return self.unit.replace("_", " ").title()


@dataclass(frozen=True)
class Family:
    name: str
    slot: Slot
    lines: tuple[Line, ...]

    @property
    def age(self) -> Age:
        return self.lines[0].age


# RoR's line-upgrade techs (read from the data: each upgrades one of these units into the next).
FAMILIES = (
    Family("Clubmen", Slot.MELEE, (Line("clubman", Age.STONE), Line("axeman", Age.TOOL, 63))),
    Family(
        "Swordsmen",
        Slot.MELEE,
        (
            Line("short_swordsman", Age.BRONZE),
            Line("broad_swordsman", Age.BRONZE, 65),
            Line("long_swordsman", Age.IRON, 66),
            Line("legionary", Age.POST_IRON, 77),
        ),
    ),
    Family(
        "Hoplites",
        Slot.MELEE,
        (Line("hoplite", Age.BRONZE), Line("phalangite", Age.IRON, 73), Line("centurion", Age.POST_IRON, 79)),
    ),
    Family("Scouts", Slot.MELEE, (Line("scout", Age.TOOL),)),
    Family(
        "Cavalry",
        Slot.MELEE,
        (Line("cavalry", Age.BRONZE), Line("heavy_cavalry", Age.IRON, 71), Line("cataphract", Age.POST_IRON, 78)),
    ),
    Family("Camel Riders", Slot.MELEE, (Line("camel_rider", Age.BRONZE),)),
    Family("Chariots", Slot.MELEE, (Line("chariot", Age.BRONZE), Line("scythe_chariot", Age.IRON, 126))),
    Family("Elephants", Slot.MELEE, (Line("war_elephant", Age.IRON), Line("armored_elephant", Age.POST_IRON, 125))),
    Family("Slingers", Slot.RANGED, (Line("slinger", Age.STONE),)),
    Family(
        "Bowmen",
        Slot.RANGED,
        # Bowmen from the Bronze Age, not the Tool: Slingers (which beat the player's archers) hold until then, and
        # Improved and Composite come by line upgrades, not as one jump (playtests 2026-11-21)
        (
            Line("bowman", Age.BRONZE),
            Line("improved_bowman", Age.BRONZE, 56),
            Line("composite_bowman", Age.BRONZE, 57),
        ),
    ),
    Family("Chariot Archers", Slot.RANGED, (Line("chariot_archer", Age.BRONZE),)),
    Family(
        "Horse Archers",
        Slot.RANGED,
        (Line("horse_archer", Age.IRON), Line("heavy_horse_archer", Age.POST_IRON, 38)),
    ),
    Family("Elephant Archers", Slot.RANGED, (Line("elephant_archer", Age.IRON),)),
    Family(
        "Stone Throwers",
        Slot.SIEGE,
        (Line("stone_thrower", Age.BRONZE), Line("catapult", Age.IRON, 54), Line("heavy_catapult", Age.POST_IRON, 36)),
    ),
    Family("Ballistas", Slot.SIEGE, (Line("ballista", Age.IRON), Line("helepolis", Age.POST_IRON, 27))),
)
BY_NAME = {family.name: family for family in FAMILIES}
PRIEST = "priest"
PRIEST_AGE = Age.BRONZE
# The Legion's own buildings an upgrade or boon can improve (its bases): ids, as the units table lacks some names.
STRUCTURES = {
    "watch_tower": 79,
    "sentry_tower": 234,
    "guard_tower": 235,
    "ballista_tower": 236,
    "small_wall": 72,
    "medium_wall": 117,
    "fortified_wall": 155,
    "barracks": 12,  # stands for every building (Architecture's class)
}

# A path: stages in order, each a choice of families rolled at the start (None: the path ends there).
Path = tuple[tuple[str | None, ...], ...]
MELEE_LEGION: Path = (("Clubmen",), ("Swordsmen",))
MELEE_CHARIOTS: Path = (("Clubmen",), ("Scouts",), ("Chariots",), (None, "Camel Riders"))
RANGED_BOWMEN: Path = (("Slingers",), ("Bowmen",))
RANGED_SUPPORT: Path = (("Slingers",), ("Bowmen",), (None, "Chariot Archers"))  # Composite, or Chariot Archers
MELEE_SUPPORTS: tuple[Path, ...] = (  # for the ranged archetypes; in a support slot no Post-Iron line (MAIN_ONLY)
    MELEE_CHARIOTS,
    MELEE_LEGION,
    (("Clubmen",), ("Hoplites",)),
    (("Clubmen",), ("Scouts",), ("Cavalry",)),
)


@dataclass(frozen=True)
class Archetype:
    name: str
    main: Slot
    paths: dict[Slot, tuple[Path, ...]]  # each slot's paths: one rolled at the start
    supports: tuple[Support, ...] = (Support.PRIEST, Support.CATAPULT, Support.BALLISTA)  # in order of preference


ARCHETYPES = (
    Archetype("Legion", Slot.MELEE, {Slot.MELEE: (MELEE_LEGION,), Slot.RANGED: (RANGED_SUPPORT,)}),
    Archetype(
        "Phalanx",
        Slot.MELEE,
        {Slot.MELEE: ((("Clubmen",), ("Hoplites",)),), Slot.RANGED: (RANGED_SUPPORT,)},
        (Support.BALLISTA, Support.CATAPULT, Support.PRIEST),
    ),
    Archetype(
        "Cavalry",
        Slot.MELEE,
        {Slot.MELEE: ((("Clubmen",), ("Scouts",), ("Cavalry",)),), Slot.RANGED: (RANGED_SUPPORT,)},
    ),
    Archetype(
        "Chariots",
        Slot.MELEE,
        {
            Slot.MELEE: ((("Clubmen",), ("Scouts",), ("Chariots",)),),
            Slot.RANGED: ((("Slingers",), ("Bowmen",), ("Chariot Archers",)),),
        },
    ),
    Archetype(
        "Elephants",
        Slot.MELEE,
        {
            Slot.MELEE: ((("Clubmen",), ("Scouts",), ("Chariots",), ("Elephants",)),),
            Slot.RANGED: ((("Slingers",), ("Bowmen",), ("Chariot Archers",), ("Elephant Archers",)),),
        },
    ),
    Archetype(
        "Archers",
        Slot.RANGED,
        {Slot.RANGED: (RANGED_BOWMEN,), Slot.MELEE: MELEE_SUPPORTS},
        (Support.CATAPULT, Support.BALLISTA, Support.PRIEST),
    ),
    Archetype(
        "Mounted Archers",
        Slot.RANGED,
        {
            Slot.RANGED: (
                (("Slingers",), ("Bowmen",), ("Chariot Archers",), ("Horse Archers", "Elephant Archers")),
            ),
            Slot.MELEE: MELEE_SUPPORTS,
        },
        (Support.CATAPULT, Support.BALLISTA, Support.PRIEST),
    ),
)



@dataclass(frozen=True)
class Upgrade:
    name: str
    tech: int
    age: Age
    requires: int = -1  # an upgrade's tech that must come first


AGE_TECHS = {Age.TOOL: 101, Age.BRONZE: 102, Age.IRON: 103}  # the Post-Iron Age has none: its lines only
UPGRADES = (  # stat techs; line upgrades come from FAMILIES
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
    # the Legion's bases
    Upgrade("Sentry Tower", 12, Age.BRONZE),
    Upgrade("Guard Tower", 15, Age.IRON, 12),
    Upgrade("Ballista Tower", 2, Age.IRON, 15),
    Upgrade("Medium Wall", 13, Age.BRONZE),
    Upgrade("Fortified Wall", 14, Age.IRON, 13),
    Upgrade("Architecture", 112, Age.BRONZE),
)

STAT_EFFECTS = (0, 4, 5)  # set, add, multiply an attribute: an effect command a unit feels
UPGRADE_UNIT = 3  # an effect command that turns one unit into another (a tower or wall line)


def unit_id(name: str) -> int:
    return STRUCTURES[name] if name in STRUCTURES else tables.object_id(name.upper(), "ror")


def units() -> list[str]:
    """Every unit an upgrade can improve, in index order: each family's lines, the Priest, then the Legion's
    structures."""
    return [line.unit for family in FAMILIES for line in family.lines] + [PRIEST, *STRUCTURES]


def structures_from() -> int:
    """The index in units() of the first structure."""
    return units().index(next(iter(STRUCTURES)))


def line_upgrades() -> list[tuple[int, int]]:
    """(family index, line index) of every line upgrade, in order."""
    return [(f, n) for f, family in enumerate(FAMILIES) for n in range(1, len(family.lines))]


def improves_by(commands, data, unit: str) -> bool:
    """Effect commands change a stat of `unit` (by its id or its class), or turn it into another."""
    uid = unit_id(unit)
    klass = data.civs[1].units[uid].class_
    triples = [c[:3] if isinstance(c, tuple) else (c.type, c.a, c.b) for c in commands]  # a boon's are tuples

    return any(
        (kind in STAT_EFFECTS and (a == uid or (a == -1 and b == klass))) or (kind == UPGRADE_UNIT and a == uid)
        for kind, a, b in triples
    )


def improves(data, upgrade: Upgrade, unit: str) -> bool:
    """`upgrade`'s tech changes `unit`, read from the data."""
    tech = data.techs[upgrade.tech]

    return tech.effect_id >= 0 and improves_by(data.effects[tech.effect_id].effect_commands, data, unit)
