"""Macedonians: "Infantry civilization" (RoR string 120165)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Subject, Tier, ladder

BOONS = (
    Boon(
        civ=Civ.MACEDONIANS,
        number=1,
        title="Non-ranged units: Line of sight",
        stat=Stat.LINE_OF_SIGHT,
        groups=(Group.NON_RANGED,),
        domain=Domain.MILITARY,
        kind=Kind.VISION,
        subjects=(
            Subject.INFANTRY,
            Subject.CAVALRY,
        ),
        tiers=ladder(Tier.POOR, flat(1), flat(2), flat(3)),
    ),
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
        tiers=ladder(Tier.IMPROVED, flat(1), flat(2), flat(3)),
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
        tiers=ladder(Tier.COMMON, pct(-0.15), pct(-0.25), pct(-0.4)),
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
        tiers=ladder(Tier.COMMON, pct(1), pct(3), pct(6)),
    ),
    Boon(
        civ=Civ.MACEDONIANS,
        number=5,
        title="Houses: HP",
        stat=Stat.HP,
        targets=("house",),
        domain=Domain.DEFENCE,
        kind=Kind.DURABILITY,
        subjects=(Subject.BUILDING,),
        flags=(Flag.TEAM,),
        tiers=ladder(Tier.POOR, flat(50), flat(100), flat(200)),
    ),
)
