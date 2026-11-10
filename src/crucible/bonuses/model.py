"""What a bonus is: one modifier, decomposed by hand from a civ's bonus text.

A civ's text ("Academy units and elephant units +25% hit points, Camel Riders +15% hit points") becomes one
modifier per group of targets that share a change, so each can be handed out, retuned or widened on its own.
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
    SIEGE_WORKSHOP = "siege workshop"
    STABLE = "stable"
    TEMPLE = "temple"
    TOWN_CENTER = "town center"
    # What the targets are
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
    VILLAGER = "villager"
    # Broad themes
    ECONOMY = "economy"
    DEFENCE = "defence"


class Icon(StrEnum):
    """The generic upgrade icon: what the bonus is about. Mapped to RoR tech icon ids when compiling."""

    # Economy
    FARM = "farm"
    FOOD = "food"
    WOOD = "wood"
    STONE = "stone"
    GOLD = "gold"
    VILLAGER = "villager"
    # Where the targets are made
    ACADEMY = "academy"
    ARCHERY_RANGE = "archery range"
    BARRACKS = "barracks"
    DOCK = "dock"
    GOVERNMENT_CENTER = "government center"
    SIEGE_WORKSHOP = "siege workshop"
    STABLE = "stable"
    TEMPLE = "temple"
    TOWN_CENTER = "town center"
    # One kind of unit
    CAMEL = "camel"
    CHARIOT = "chariot"
    ELEPHANT = "elephant"
    PRIEST = "priest"
    SHIP = "ship"
    TRANSPORT = "transport"
    # Defence
    TOWER = "tower"
    WALL = "wall"


class Stat(StrEnum):
    HP = "hp"
    ATTACK = "attack"
    SPEED = "speed"
    WORK_RATE = "work rate"
    START_RESOURCES = "start resources"
    TECH_COST = "tech cost"


class Kind(StrEnum):
    CIV = "civ"
    TEAM = "team"


class Mode(StrEnum):
    PERCENT = "x"  # +0.25x: 25% more
    FLAT = "+"  # +50: fifty more


class Change(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: float
    mode: Mode

    def __str__(self) -> str:
        return f"{self.amount:+g}{'x' if self.mode is Mode.PERCENT else ''}"


def pct(amount: float) -> Change:
    """A relative change: pct(0.25) is +25%, pct(-1) makes something free."""
    return Change(amount=amount, mode=Mode.PERCENT)


def flat(amount: float) -> Change:
    """An absolute change: flat(50) is +50."""
    return Change(amount=amount, mode=Mode.FLAT)


class Modifier(BaseModel):
    """One bonus, which becomes one upgrade (a hidden tech) to hand out: to the player, the enemy, as
    metaprogression or a boon.

    `targets` are RoR object names (units, buildings), or tech names for `Stat.TECH_COST`; empty for player-wide
    changes. They're checked against the game's tables when the modifier is made. `name` is the upgrade's title
    ("Carthaginians 1"), `description` what it does, `icon` its button picture.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    change: Change
    stat: Stat
    targets: tuple[str, ...]
    tags: tuple[Tag, ...]
    civ: Civ
    name: str
    description: str
    icon: Icon
    kind: Kind = Kind.CIV

    @model_validator(mode="after")
    def _targets_exist(self) -> "Modifier":
        lookup = tables.tech_id if self.stat is Stat.TECH_COST else tables.object_id
        unknown = [t for t in self.targets if lookup(t.upper(), self.civ.game) is None]
        if unknown:
            raise ValueError(f"{self.name}: unknown {self.civ.game} targets {unknown}")
        return self

    @property
    def id(self) -> str:
        """Stable key from the name: "Carthaginians 1" is "carthaginians_1"."""
        return self.name.lower().replace(" ", "_")

    def __str__(self) -> str:
        on = ", ".join(self.targets) or "player"
        return (
            f"{self.name}: {self.description} | {self.change} {self.stat} [{on}] [{', '.join(self.tags)}] "
            f"{self.icon} icon ({self.kind})"
        )
