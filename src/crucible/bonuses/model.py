"""What a bonus is: one modifier, decomposed by hand from a civ's bonus text.

A civ's text ("Academy units and elephant units +25% hit points, Camel Riders +15% hit points") becomes one
modifier per group of targets that share a change, so each can be handed out, retuned or widened on its own.
Values that grow with the ages ("+2/+3 range in Bronze/Iron Age") use the Iron Age value; the civ module's
docstring keeps the original text.
"""

from enum import StrEnum

from aoe2ed import tables
from pydantic import BaseModel, ConfigDict, model_validator


class Game(StrEnum):
    """The game mode a civ comes from."""

    DE = "de"
    ROR = "ror"
    CHRONICLES = "chronicles"


class Civ(StrEnum):
    EGYPTIANS = "egyptians"
    GREEKS = "greeks"
    BABYLONIANS = "babylonians"
    ASSYRIANS = "assyrians"
    MINOANS = "minoans"
    HITTITES = "hittites"
    PHOENICIANS = "phoenicians"
    SUMERIANS = "sumerians"
    PERSIANS = "persians"
    SHANG = "shang"
    YAMATO = "yamato"
    CHOSON = "choson"
    ROMANS = "romans"
    CARTHAGINIANS = "carthaginians"
    PALMYRANS = "palmyrans"
    MACEDONIANS = "macedonians"
    LAC_VIET = "lac viet"

    @property
    def game(self) -> Game:
        return CIV_GAMES[self]


CIV_GAMES: dict[Civ, Game] = {civ: Game.ROR for civ in Civ}


class Tag(StrEnum):
    """What hand-outs group modifiers by ("pick a stable upgrade"). Add members as civs need them."""

    # Where the targets are made
    ACADEMY = "academy"
    ARCHERY_RANGE = "archery range"
    BARRACKS = "barracks"
    DOCK = "dock"
    GOVERNMENT_CENTER = "government center"
    GRANARY = "granary"
    MARKET = "market"
    SIEGE_WORKSHOP = "siege workshop"
    STABLE = "stable"
    STORAGE_PIT = "storage pit"
    TEMPLE = "temple"
    TOWN_CENTER = "town center"
    # What the targets are
    ARCHER = "archer"
    BUILDING = "building"
    CAMEL = "camel"
    CAVALRY = "cavalry"
    CHARIOT = "chariot"
    ELEPHANT = "elephant"
    HOPLITE = "hoplite"
    INFANTRY = "infantry"
    PRIEST = "priest"
    SHIP = "ship"
    SIEGE = "siege"
    SWORDSMAN = "swordsman"
    TECHNOLOGY = "technology"
    TOWER = "tower"
    TRANSPORT = "transport"
    UNIT = "unit"
    VILLAGER = "villager"
    WALL = "wall"
    # Resources
    FOOD = "food"
    WOOD = "wood"
    STONE = "stone"
    GOLD = "gold"
    # Broad themes
    DEFENCE = "defence"
    ECONOMY = "economy"
    TRADE = "trade"
    # Where it came from, or what to watch out for
    TEAM = "team"  # was a team bonus (there's no team in Crucible: it applies to you)
    DRAWBACK = "drawback"  # makes something worse; better for the enemy or a curse


class Group(StrEnum):
    """Targets named as a whole: unit classes, and villager jobs (a male and a female unit each). The value is how
    descriptions say it. Resolved to the game's classes and units when compiling."""

    ARCHERS = "Archers"
    CAVALRY = "Cavalry"
    INFANTRY = "Infantry"
    PRIESTS = "Priests"
    SHIPS = "Ships"
    SIEGE = "Siege weapons"
    VILLAGERS = "Villagers"
    MILITARY = "Military units"
    NON_RANGED = "Non-ranged units"
    ALL_UNITS = "All units"
    BUILDINGS = "Buildings"
    TOWERS = "Towers"
    WALLS = "Walls"
    BUILDERS = "Builders"
    FARMERS = "Farmers"
    FORAGERS = "Foragers"
    GOLD_MINERS = "Gold Miners"
    HUNTERS = "Hunters"
    STONE_MINERS = "Stone Miners"
    WOODCUTTERS = "Woodcutters"


class Icon(StrEnum):
    """The generic upgrade icon: what the bonus is about. Mapped to RoR tech icon ids when compiling."""

    # Economy
    FARM = "farm"
    FISH = "fish"
    FOOD = "food"
    WOOD = "wood"
    STONE = "stone"
    GOLD = "gold"
    VILLAGER = "villager"
    TRADE = "trade"
    TECHNOLOGY = "technology"
    # Where the targets are made
    ACADEMY = "academy"
    ARCHERY_RANGE = "archery range"
    BARRACKS = "barracks"
    DOCK = "dock"
    GOVERNMENT_CENTER = "government center"
    MARKET = "market"
    SIEGE_WORKSHOP = "siege workshop"
    STABLE = "stable"
    STORAGE_PIT = "storage pit"
    TEMPLE = "temple"
    TOWN_CENTER = "town center"
    # One kind of unit
    ARCHER = "archer"
    CAMEL = "camel"
    CAVALRY = "cavalry"
    CHARIOT = "chariot"
    ELEPHANT = "elephant"
    INFANTRY = "infantry"
    PRIEST = "priest"
    SHIP = "ship"
    SIEGE = "siege"
    TRANSPORT = "transport"
    # Buildings and defence
    BUILDING = "building"
    HOUSE = "house"
    TOWER = "tower"
    WALL = "wall"


class Stat(StrEnum):
    """What a modifier changes; the value is how descriptions say it."""

    HP = "HP"
    ATTACK = "attack"
    ATTACK_SPEED = "attack speed"
    MELEE_ARMOUR = "melee armour"
    PIERCE_ARMOUR = "pierce armour"
    RANGE = "range"
    SPEED = "speed"
    LINE_OF_SIGHT = "line of sight"
    WORK_RATE = "work rate"
    CARRY = "carry capacity"
    COST = "cost"
    FOOD_COST = "food cost"
    WOOD_COST = "wood cost"
    TRAINING_SPEED = "training speed"
    BUILD_SPEED = "build speed"
    RESEARCH_SPEED = "research speed"
    RESEARCH_TIME = "research time"
    HEAL_SPEED = "heal speed"
    REJUVENATION = "faith regeneration"
    CONVERSION_RESISTANCE = "conversion resistance"
    POPULATION = "population room"
    FOOD = "food"  # food held, e.g. by Farms
    ALL_RESOURCES = "all resources"  # at the start
    STARTING_FOOD = "starting food"
    TRADE_GOLD = "trade gold"
    TRIBUTE_TAX = "tribute tax"


class Mode(StrEnum):
    PERCENT = "%"  # pct(0.25): 25% more
    FLAT = "+"  # flat(50): fifty more


class Change(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: float
    mode: Mode

    def __str__(self) -> str:
        """How descriptions say it: "+25%", "-100%", "+500"."""
        if self.mode is Mode.PERCENT:
            return f"{self.amount * 100:+g}%"

        return f"{self.amount:+g}"


def pct(amount: float) -> Change:
    """A relative change: pct(0.25) is +25%, pct(-1) makes something free."""
    return Change(amount=amount, mode=Mode.PERCENT)


def flat(amount: float) -> Change:
    """An absolute change: flat(50) is +50."""
    return Change(amount=amount, mode=Mode.FLAT)


UNCOUNTABLE = ("cavalry",)


def plural(target: str) -> str:
    """A target name as descriptions say it: "war_elephant" is "War Elephants", "academy" is "Academies",
    "axeman" is "Axemen", "heavy_cavalry" stays "Heavy Cavalry"."""
    words = target.replace("_", " ").title()

    if words.lower().endswith(UNCOUNTABLE):
        return words

    if words.endswith("man"):
        return words[:-3] + "men"

    if words.endswith("y") and words[-2:-1].lower() not in "aeiou":  # galley -> galleys
        return words[:-1] + "ies"

    return words + ("es" if words.endswith("s") else "s")


Category = Tag | Civ | Stat | Group
"""Anything a hand-out can offer as a choice: "a cavalry upgrade" (tag), "a Greek upgrade" (civ), "an HP upgrade"
(stat), "an archer upgrade" (group)."""


class Modifier(BaseModel):
    """One bonus, which becomes one upgrade (a hidden tech) to hand out: to the player, the enemy, as
    metaprogression or a boon.

    What it applies to: `targets` (RoR object names: units, buildings), `groups` (classes and villager jobs) and
    `techs` (RoR tech names); all empty for player-wide changes. Names are checked against the game's tables when
    the modifier is made. `name` is the upgrade's title ("Carthaginians 1") and `icon` its button picture; the
    description is written from the definition, so it follows any change to the numbers or targets. `subject`
    names a long list in short ("Storage Pit technologies") for the description; the change and stat stay live.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    change: Change
    stat: Stat
    targets: tuple[str, ...] = ()
    groups: tuple[Group, ...] = ()
    techs: tuple[str, ...] = ()
    tags: tuple[Tag, ...]
    civ: Civ
    name: str
    icon: Icon
    subject: str | None = None

    @model_validator(mode="after")
    def _names_exist(self) -> "Modifier":
        game = self.civ.game

        unknown = [t for t in self.targets if tables.object_id(t.upper(), game) is None]
        unknown += [t for t in self.techs if tables.tech_id(t.upper(), game) is None]

        if unknown:
            raise ValueError(f"{self.name}: unknown {game} names {unknown}")

        return self

    @property
    def id(self) -> str:
        """Stable key from the name: "Carthaginians 1" is "carthaginians_1"."""
        return self.name.lower().replace(" ", "_")

    @property
    def description(self) -> str:
        """E.g. "Hoplites, Phalangites, Centurions +25% HP", "Archers +1 attack", "+500 all resources". Techs
        aren't plural: "Nobility -100% cost"."""
        if self.subject:
            names = [self.subject]
        else:
            names = [g.value for g in self.groups] + [plural(t) for t in self.targets]
            names += [t.replace("_", " ").title() for t in self.techs]

        who = f"{', '.join(names)} " if names else ""

        return f"{who}{self.change} {self.stat}"

    def in_category(self, category: Category) -> bool:
        if isinstance(category, Tag):
            return category in self.tags

        if isinstance(category, Civ):
            return category is self.civ

        if isinstance(category, Stat):
            return category is self.stat

        return category in self.groups

    def __str__(self) -> str:
        return f"{self.name}: {self.description} [{', '.join(self.tags)}] {self.icon} icon"
