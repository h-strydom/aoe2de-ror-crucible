"""Sumerians: "Economic and Siege civilization" (RoR string 120157)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Subject, Tier, ladder

BOONS = (
    Boon(
        civ=Civ.SUMERIANS,
        number=1,
        title="Villager: HP",
        stat=Stat.HP,
        groups=(Group.VILLAGERS,),
        domain=Domain.ECONOMY,
        kind=Kind.DURABILITY,
        subjects=(Subject.VILLAGER,),
        buildings=(Building.TOWN_CENTER,),
        tiers=ladder(Tier.COMMON, flat(5), flat(10), flat(15)),
    ),
    Boon(
        civ=Civ.SUMERIANS,
        number=2,
        title="Stone Throwers: Attack speed",
        stat=Stat.ATTACK_SPEED,
        targets=(
            "stone_thrower",
            "catapult",
            "heavy_catapult",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.SIEGE,),
        buildings=(Building.SIEGE_WORKSHOP,),
        tiers=ladder(Tier.COMMON, pct(0.15), pct(0.3), pct(0.45)),
    ),
    Boon(
        civ=Civ.SUMERIANS,
        number=3,
        title="Farms: Food",
        stat=Stat.FOOD,
        targets=("farm",),
        domain=Domain.ECONOMY,
        kind=Kind.RESOURCES,
        subjects=(
            Subject.FOOD,
            Subject.BUILDING,
        ),
        tiers=ladder(Tier.COMMON, flat(75), flat(125), flat(200)),
    ),
    Boon(
        civ=Civ.SUMERIANS,
        number=4,
        title="Camel Riders: Pierce armour",
        stat=Stat.PIERCE_ARMOUR,
        targets=("camel_rider",),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(
            Subject.CAMEL,
            Subject.CAVALRY,
        ),
        buildings=(Building.STABLE,),
        tiers=ladder(Tier.POOR, flat(1), flat(2), flat(3)),
    ),
    Boon(
        civ=Civ.SUMERIANS,
        number=5,
        title="Town Center: Cost",
        stat=Stat.COST,
        targets=("town_center",),
        domain=Domain.ECONOMY,
        kind=Kind.DISCOUNT,
        subjects=(Subject.BUILDING,),
        buildings=(Building.TOWN_CENTER,),
        flags=(Flag.TEAM,),
        tiers=ladder(Tier.POOR, pct(-0.25), pct(-0.5), pct(-0.75)),
    ),
)
