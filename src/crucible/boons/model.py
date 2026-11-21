"""Tiered boons: the redesign of the civ bonuses (docs/todo.md), kept here as the source of truth.

A boon covers a run of rarity tiers (usually three in a row); each tier it covers holds its effects: the first is the
boon's own stat on its own subject, any more are extras ("+60% work rate & +3 carry capacity"). Adding a tier is a
new Tier member; moving a boon is changing its first tier; combining effects is adding to a tier's list.

Tags come from fixed axes, so an offer can draw each choice from a different axis (catalogue.offer): Domain, Kind
(what it does), Subject, Building, the civ and its types, Team and Drawback.

Not compiled into the data mod yet: crucible.bonuses (one fixed value per boon) still is.
"""

from enum import IntEnum, StrEnum

from aoe2ed import tables
from pydantic import BaseModel, ConfigDict, model_validator

from crucible.bonuses.model import Change, Civ, Cost, Group, Icon, Stat


class Tier(IntEnum):
    """In order: a boon's tiers are consecutive members. Its lowest sets its price, so a higher roll is free."""

    POOR = 0
    COMMON = 1
    IMPROVED = 2
    MASTERCRAFTED = 3
    LEGENDARY = 4
    HEIRLOOM = 5  # the Legendary effect plus something extra

    @property
    def title(self) -> str:
        return self.name.title()


# What a boon costs, by its lowest tier (a higher roll costs the same): one place to tune every price.
TIER_COSTS: dict[Tier, Cost] = {
    Tier.POOR: Cost(food=150),
    Tier.COMMON: Cost(food=250),
    Tier.IMPROVED: Cost(food=200, gold=75),
    Tier.MASTERCRAFTED: Cost(food=250, gold=150),
    Tier.LEGENDARY: Cost(gold=300),
    Tier.HEIRLOOM: Cost(gold=400),
}
# The shop's roll for a better tier than a boon's lowest: (tiers up, chance in percent), checked in order.
TIER_UPS: tuple[tuple[int, int], ...] = ((2, 10), (1, 20))


class Domain(StrEnum):
    ECONOMY = "Economy"
    MILITARY = "Military"
    DEFENCE = "Defence"
    RESEARCH = "Research"


class Kind(StrEnum):
    """What a boon does."""

    COMBAT = "Combat"  # attack, attack speed, range, armour
    DURABILITY = "Durability"  # HP, HP regeneration
    SPEED = "Speed"  # movement
    GATHERING = "Gathering"  # work rate and carry capacity of gatherers
    PRODUCTION = "Production"  # work, training, build and research speed
    DISCOUNT = "Discount"  # any cost
    RESOURCES = "Resources"  # resources given or held
    VISION = "Vision"
    POPULATION = "Population"
    FAITH = "Faith"  # priests and conversion


class Subject(StrEnum):
    VILLAGER = "Villager"
    INFANTRY = "Infantry"
    HOPLITE = "Hoplite"
    SWORDSMAN = "Swordsman"
    ARCHER = "Archer"
    CAVALRY = "Cavalry"
    CHARIOT = "Chariot"
    ELEPHANT = "Elephant"
    CAMEL = "Camel"
    SIEGE = "Siege"
    PRIEST = "Priest"
    SHIP = "Ship"
    TRANSPORT = "Transport"
    BUILDING = "Building"
    TOWER = "Tower"
    WALL = "Wall"
    MARKET = "Market"
    STORAGE_PIT = "Storage Pit"
    GOVERNMENT_CENTER = "Government Center"
    TECHNOLOGY = "Technology"
    TRADE = "Trade"
    FOOD = "Food"
    WOOD = "Wood"
    STONE = "Stone"
    GOLD = "Gold"


class Building(StrEnum):
    """Where a boon's units or techs come from: "Stable boons"."""

    TOWN_CENTER = "Town Center"
    BARRACKS = "Barracks"
    ARCHERY_RANGE = "Archery Range"
    STABLE = "Stable"
    ACADEMY = "Academy"
    SIEGE_WORKSHOP = "Siege Workshop"
    TEMPLE = "Temple"
    DOCK = "Dock"
    MARKET = "Market"
    STORAGE_PIT = "Storage Pit"
    GOVERNMENT_CENTER = "Government Center"


class CivType(StrEnum):
    """RoR's civ descriptions ("Archer and Siege civilization"); tagged "Archer civ" so it doesn't clash with the
    subject."""

    ARCHER = "Archer civ"
    CAMEL = "Camel civ"
    CAVALRY = "Cavalry civ"
    CHARIOT = "Chariot civ"
    DEFENSIVE = "Defensive civ"
    ECONOMIC = "Economic civ"
    ELEPHANT = "Elephant civ"
    INFANTRY = "Infantry civ"
    NAVAL = "Naval civ"
    PRIEST = "Priest civ"
    SIEGE = "Siege civ"
    TOWER = "Tower civ"
    TRADING = "Trading civ"


class Flag(StrEnum):
    TEAM = "Team"  # was a team bonus
    DRAWBACK = "Drawback"  # makes something worse: for the enemy or a curse, never a normal offer


CIV_TYPES: dict[Civ, tuple[CivType, ...]] = {
    Civ.EGYPTIANS: (CivType.CHARIOT, CivType.PRIEST),
    Civ.GREEKS: (CivType.INFANTRY, CivType.NAVAL),
    Civ.BABYLONIANS: (CivType.DEFENSIVE,),
    Civ.ASSYRIANS: (CivType.ARCHER, CivType.SIEGE),
    Civ.MINOANS: (CivType.ARCHER, CivType.NAVAL),
    Civ.HITTITES: (CivType.ARCHER, CivType.SIEGE),
    Civ.PHOENICIANS: (CivType.ELEPHANT, CivType.NAVAL),
    Civ.SUMERIANS: (CivType.ECONOMIC, CivType.SIEGE),
    Civ.PERSIANS: (CivType.ELEPHANT, CivType.NAVAL),
    Civ.SHANG: (CivType.ECONOMIC, CivType.CAVALRY),
    Civ.YAMATO: (CivType.CAVALRY, CivType.NAVAL),
    Civ.CHOSON: (CivType.INFANTRY, CivType.TOWER),
    Civ.ROMANS: (CivType.INFANTRY,),
    Civ.CARTHAGINIANS: (CivType.ELEPHANT, CivType.CAMEL, CivType.NAVAL),
    Civ.PALMYRANS: (CivType.CAMEL, CivType.TRADING),
    Civ.MACEDONIANS: (CivType.INFANTRY,),
    Civ.LAC_VIET: (CivType.ARCHER,),
}

Axis = type[Domain] | type[Kind] | type[Subject] | type[Building] | type[Civ] | type[CivType] | type[Flag]
AXES: tuple[Axis, ...] = (Domain, Kind, Subject, Building, Civ, CivType, Flag)
Category = Domain | Kind | Subject | Building | Civ | CivType | Flag


class Effect(BaseModel):
    """One change. Without a stat or subject of its own it uses the boon's."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    change: Change
    stat: Stat | None = None
    targets: tuple[str, ...] | None = None
    groups: tuple[Group, ...] | None = None
    techs: tuple[str, ...] | None = None


def extra(change: Change, stat: Stat, **subject) -> Effect:
    """An effect beyond the boon's own: extra(flat(3), Stat.CARRY), or on another subject with targets=, groups=,
    techs=."""
    return Effect(change=change, stat=stat, **subject)


Level = Change | Effect | tuple[Change | Effect, ...]


def ladder(first: Tier, *levels: Level) -> dict[Tier, tuple[Effect, ...]]:
    """Tiers from `first` up, one per level: a Change is the boon's own stat, a tuple adds extras."""
    tiers = {}

    for n, level in enumerate(levels):
        items = level if isinstance(level, tuple) else (level,)
        tiers[Tier(first + n)] = tuple(i if isinstance(i, Effect) else Effect(change=i) for i in items)

    return tiers


class Boon(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    civ: Civ
    number: int
    title: str  # "Swordsman line: HP": what the button says
    stat: Stat
    targets: tuple[str, ...] = ()  # RoR object names
    groups: tuple[Group, ...] = ()
    techs: tuple[str, ...] = ()  # RoR tech names
    domain: Domain
    kind: Kind
    subjects: tuple[Subject, ...]
    buildings: tuple[Building, ...] = ()
    flags: tuple[Flag, ...] = ()
    tiers: dict[Tier, tuple[Effect, ...]]
    note: str = ""

    @model_validator(mode="after")
    def _valid(self) -> "Boon":
        found = sorted(self.tiers)

        if not found or found != list(range(found[0], found[-1] + 1)):
            raise ValueError(f"{self.id}: tiers must be consecutive, got {[t.name for t in found]}")

        if any(not effects for effects in self.tiers.values()):
            raise ValueError(f"{self.id}: a tier without effects")

        game = self.civ.game
        targets = {*self.targets, *(t for e in self._effects() for t in e.targets or ())}
        techs = {*self.techs, *(t for e in self._effects() for t in e.techs or ())}
        unknown = [t for t in targets if tables.object_id(t.upper(), game) is None]
        unknown += [t for t in techs if tables.tech_id(t.upper(), game) is None]

        if unknown:
            raise ValueError(f"{self.id}: unknown {game} names {unknown}")

        return self

    def _effects(self) -> list[Effect]:
        return [e for effects in self.tiers.values() for e in effects]

    @property
    def id(self) -> str:
        return f"{self.civ.value.replace(' ', '_')}_{self.number}"

    @property
    def lowest(self) -> Tier:
        """Sets the price."""
        return min(self.tiers)

    @property
    def highest(self) -> Tier:
        return max(self.tiers)

    @property
    def cost(self) -> Cost:
        return TIER_COSTS[self.lowest]

    @property
    def icon(self) -> Icon:
        """Its button picture: from its first subject or building with one ("Swordsman" is infantry)."""
        aliases = {Subject.HOPLITE: Icon.INFANTRY, Subject.SWORDSMAN: Icon.INFANTRY}
        names = {i.value: i for i in Icon}

        for tag in (*self.subjects, *self.buildings):
            if tag in aliases:
                return aliases[tag]

            if tag.value.lower() in names:
                return names[tag.value.lower()]

        return Icon.TECHNOLOGY

    @property
    def name(self) -> str:
        """"Choson 2"."""
        return f"{self.civ.value.title()} {self.number}"

    @property
    def civ_types(self) -> tuple[CivType, ...]:
        return CIV_TYPES[self.civ]

    @property
    def categories(self) -> tuple[Category, ...]:
        """Every tag, axis by axis."""
        return (self.domain, self.kind, *self.subjects, *self.buildings, self.civ, *self.civ_types, *self.flags)

    def in_category(self, category: Category) -> bool:
        """By identity: the axes share values as strings (Subject.MARKET == Building.MARKET == "Market")."""
        return any(c is category for c in self.categories)

    def text(self, tier: Tier) -> str:
        """A tier as text: "+60% & +3 carry capacity"."""
        parts = []

        for effect in self.tiers.get(tier, ()):
            words = [str(effect.change)]

            if effect.stat and effect.stat != self.stat:
                words.append(str(effect.stat))

            names = [*(effect.targets or ()), *(g.value for g in effect.groups or ()), *(effect.techs or ())]
            if names:
                words.append(f"({', '.join(n.replace('_', ' ') for n in names)})")

            parts.append(" ".join(words))

        return " & ".join(parts)
