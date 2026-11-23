"""Macedonians: "Infantry civilization" (RoR string 120165)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Kind, Rarity, Subject

BOONS = (
    Boon(
        civ=Civ.MACEDONIANS,
        number=2,
        title="Hoplites: Pierce armour",
        stat=Stat.PIERCE_ARMOUR,
        targets=(
            "hoplite",
            "phalangite",
            "centurion",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(
            Subject.INFANTRY,
            Subject.HOPLITE,
        ),
        buildings=(Building.ACADEMY,),
        rarity=Rarity.RARE,
        effects=(flat(1),),
    ),
    Boon(
        civ=Civ.MACEDONIANS,
        number=3,
        title="Siege: Cost",
        stat=Stat.COST,
        targets=(
            "stone_thrower",
            "catapult",
            "heavy_catapult",
            "ballista",
            "helepolis",
        ),
        domain=Domain.MILITARY,
        kind=Kind.DISCOUNT,
        subjects=(Subject.SIEGE,),
        buildings=(Building.SIEGE_WORKSHOP,),
        rarity=Rarity.COMMON,
        effects=(pct(-0.08),),
    ),
    Boon(
        civ=Civ.MACEDONIANS,
        number=4,
        title="All units: Conversion resistance",
        stat=Stat.CONVERSION_RESISTANCE,
        groups=(Group.ALL_UNITS,),
        domain=Domain.MILITARY,
        kind=Kind.FAITH,
        subjects=(Subject.PRIEST,),
        rarity=Rarity.COMMON,
        effects=(pct(1),),
    ),
)
