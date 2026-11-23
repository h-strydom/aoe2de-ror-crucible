"""Shang: "Economic and Cavalry civilization" (RoR string 120159)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Rarity, Subject

BOONS = (
    Boon(
        civ=Civ.SHANG,
        number=1,
        title="Villager: Food cost",
        stat=Stat.FOOD_COST,
        groups=(Group.VILLAGERS,),
        domain=Domain.ECONOMY,
        kind=Kind.DISCOUNT,
        subjects=(Subject.VILLAGER,),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.COMMON,
        effects=(flat(-4),),
    ),
    Boon(
        civ=Civ.SHANG,
        number=4,
        title="Cavalry: Attack speed",
        stat=Stat.ATTACK_SPEED,
        targets=(
            "cavalry",
            "heavy_cavalry",
            "cataphract",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.CAVALRY,),
        buildings=(Building.STABLE,),
        rarity=Rarity.RARE,
        effects=(pct(0.06),),
    ),
    Boon(
        civ=Civ.SHANG,
        number=5,
        title="Town Center: Population room",
        stat=Stat.POPULATION,
        targets=("town_center",),
        domain=Domain.ECONOMY,
        kind=Kind.POPULATION,
        subjects=(Subject.BUILDING,),
        buildings=(Building.TOWN_CENTER,),
        flags=(Flag.TEAM,),
        rarity=Rarity.RARE,
        effects=(flat(3),),
    ),
)
