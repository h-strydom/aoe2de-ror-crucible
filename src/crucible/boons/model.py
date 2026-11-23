"""Boons: the redesign of the civ bonuses (docs/todo.md), kept here as the source of truth.

A boon has a rarity (how good it is: its price) and the effects one level of it adds: the first is the boon's own stat
on its own subject, any more are extras ("+10% work rate & +2 carry capacity"). Each level is its own upgrade and they
stack: a stat boon can be bought LEVELS times, a big one (a production or research speed-up) once (playtest
2026-11-23: the six tiers were trimmed to these).

Tags come from fixed axes, so an offer can draw each choice from a different axis (catalogue.offer): Domain, Kind
(what it does), Subject and Building (OFFER_AXES), each tag only with enough boons to choose from. The civ, its types
and the flags are tags too, but never a choice (playtest 2026-11-23).
"""

from enum import StrEnum

from aoe2ed import tables
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from crucible.bonuses.model import Change, Civ, Cost, Group, Icon, Mode, Rarity, Stat, flat, pct

LEVELS = 5  # how many times a stat boon can be bought

# What one level of a boon costs, by rarity: the same for every level (playtest 2026-11-23). Prices are placeholders.
RARITY_COSTS: dict[Rarity, Cost] = {
    Rarity.COMMON: Cost(food=200),
    Rarity.RARE: Cost(food=300, gold=200),
    Rarity.LEGENDARY: Cost(food=400, gold=400),
}


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
# Where a percentage stops: cuts (negative) at -100% unless listed, speeds (positive) only where listed. Discounts
# stop at 75%; research time at 1 s ("instant"); other production speeds at +90% (playtest 2026-11-23).
DISCOUNT_CAP, SPEED_CAP = -0.75, 0.9
CAPS = {
    Stat.COST: DISCOUNT_CAP,
    Stat.FOOD_COST: DISCOUNT_CAP,
    Stat.WOOD_COST: DISCOUNT_CAP,
    Stat.TRIBUTE_TAX: DISCOUNT_CAP,
    Stat.RESEARCH_TIME: -1.0,
    Stat.TRAINING_SPEED: SPEED_CAP,
    Stat.BUILD_SPEED: SPEED_CAP,
    Stat.RESEARCH_SPEED: SPEED_CAP,
}
# What each level past a capped cut adds instead (costs: Boon._overshoot picks research time or training/build speed)
OVERSHOOT = {
    Stat.RESEARCH_TIME: (Stat.COST, pct(-0.05)),  # research time at 1 s: research costs 5% less a level
    Stat.TRIBUTE_TAX: (Stat.ALL_RESOURCES, flat(25)),
    Stat.RESEARCH_SPEED: (Stat.ALL_RESOURCES, flat(25)),  # no stat for every tech's cost
}
OFFER_AXES: tuple[Axis, ...] = (Domain, Kind, Subject, Building)  # what a choice can be
MIN_CATEGORY = 4  # boons a tag needs to be a choice: no odd categories with two boons (playtest 2026-11-23)
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
    rarity: Rarity
    effects: tuple[Effect, ...]  # what each level adds: a Change is the boon's own stat
    levels: int = LEVELS
    note: str = ""

    @field_validator("effects", mode="before")
    @classmethod
    def _effects_of(cls, value):
        return tuple(i if isinstance(i, Effect) else Effect(change=i) for i in value)

    @model_validator(mode="after")
    def _valid(self) -> "Boon":
        if not self.effects:
            raise ValueError(f"{self.id}: no effects")

        if not 1 <= self.levels <= LEVELS:
            raise ValueError(f"{self.id}: {self.levels} levels, not 1 to {LEVELS}")

        game = self.civ.game
        targets = {*self.targets, *(t for e in self.effects for t in e.targets or ())}
        techs = {*self.techs, *(t for e in self.effects for t in e.techs or ())}
        unknown = [t for t in targets if tables.object_id(t.upper(), game) is None]
        unknown += [t for t in techs if tables.tech_id(t.upper(), game) is None]

        if unknown:
            raise ValueError(f"{self.id}: unknown {game} names {unknown}")

        return self

    @property
    def id(self) -> str:
        return f"{self.civ.value.replace(' ', '_')}_{self.number}"

    @staticmethod
    def _key(effect: Effect) -> tuple:
        return effect.stat, effect.targets, effect.groups, effect.techs

    def _overshoot(self, effect: Effect) -> Effect:
        """What a level past a capped cut adds: OVERSHOOT's extra for its stat, on the same subject."""
        stat = effect.stat or self.stat

        if stat == Stat.COST and (effect.techs or (effect.techs is None and self.techs)):
            stat, change = Stat.RESEARCH_TIME, pct(-0.1)  # a research cost capped: faster research
        elif stat in (Stat.TRAINING_SPEED, Stat.BUILD_SPEED):
            stat, change = Stat.COST, pct(-0.05)  # as fast as it gets: cheaper
        elif stat in (Stat.COST, Stat.FOOD_COST, Stat.WOOD_COST):
            buildings = Subject.BUILDING in self.subjects
            stat, change = (Stat.BUILD_SPEED if buildings else Stat.TRAINING_SPEED), pct(0.05)
        else:
            stat, change = OVERSHOOT[stat]

        return effect.model_copy(update={"stat": stat, "change": change})

    @property
    def steps(self) -> dict[int, tuple[Effect, ...]]:
        """Each level, 1 to `levels`: its effects. A percentage stops at its cap (CAPS: discounts at 75%, production
        speeds at +90%, other cuts at 100%); every level after it adds the overshoot extra instead (OVERSHOOT)."""
        found: dict[int, tuple[Effect, ...]] = {}
        running: dict[tuple, float] = {}  # each percentage's total so far

        for level in range(1, self.levels + 1):
            step = []

            for effect in self.effects:
                key, amount = self._key(effect), effect.change.amount
                stat = effect.stat or self.stat
                cap = CAPS.get(stat, -1.0 if amount < 0 else None)

                if effect.change.mode is Mode.PERCENT and cap is not None and amount * cap > 0:  # towards its cap
                    left = round(cap - running.get(key, 0.0), 6)
                    amount = max(amount, left) if amount < 0 else min(amount, left)

                    if amount * cap <= 0:  # capped already: the overshoot's extra instead
                        step.append(self._overshoot(effect))
                        continue

                    running[key] = running.get(key, 0.0) + amount
                    effect = effect.model_copy(update={"change": Change(amount=amount, mode=Mode.PERCENT)})

                step.append(effect)

            found[level] = tuple(step)

        return found

    def total(self, level: int) -> tuple[Effect, ...]:
        """Every level up to `level` added together (what a player with each of them has)."""
        summed: dict[tuple, Effect] = {}

        for n, step in self.steps.items():
            if n > level:
                break

            for effect in step:
                old = summed.get(self._key(effect))

                if old is None or old.change.mode is not effect.change.mode:
                    summed[self._key(effect)] = effect
                else:
                    amount = round(old.change.amount + effect.change.amount, 6)
                    change = Change(amount=amount, mode=effect.change.mode)
                    summed[self._key(effect)] = effect.model_copy(update={"change": change})

        return tuple(summed.values())

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

    def text(self, level: int) -> str:
        """What a level adds, as text: "+10% & +2 carry capacity"."""
        parts = []

        for effect in self.steps.get(level, ()):
            words = [str(effect.change)]

            if effect.stat and effect.stat != self.stat:
                words.append(str(effect.stat))

            names = [*(effect.targets or ()), *(g.value for g in effect.groups or ()), *(effect.techs or ())]
            if names:
                words.append(f"({', '.join(n.replace('_', ' ') for n in names)})")

            parts.append(" ".join(words))

        return " & ".join(parts)
