"""Sumerians: "Economic and Siege civilization" (RoR string 120157)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Kind, Rarity, Subject

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
        rarity=Rarity.COMMON,
        effects=(flat(5),),
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
        rarity=Rarity.RARE,
        effects=(pct(0.08),),
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
        rarity=Rarity.RARE,
        effects=(flat(50),),
    ),
)
