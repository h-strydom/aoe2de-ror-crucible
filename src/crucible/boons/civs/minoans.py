"""Minoans: "Archer and Naval civilization" (RoR string 120154)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Kind, Rarity, Subject

BOONS = (
    Boon(
        civ=Civ.MINOANS,
        number=1,
        title="Ships: Cost",
        stat=Stat.COST,
        groups=(Group.SHIPS,),
        domain=Domain.MILITARY,
        kind=Kind.DISCOUNT,
        subjects=(Subject.SHIP,),
        buildings=(Building.DOCK,),
        rarity=Rarity.COMMON,
        effects=(pct(-0.07),),
    ),
    Boon(
        civ=Civ.MINOANS,
        number=2,
        title="Improved, Composite Bowmen: Range",
        stat=Stat.RANGE,
        targets=(
            "improved_bowman",
            "composite_bowman",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.ARCHER,),
        buildings=(Building.ARCHERY_RANGE,),
        rarity=Rarity.RARE,
        effects=(flat(1),),
    ),
    Boon(
        civ=Civ.MINOANS,
        number=3,
        title="Villager: Work speed, Farming",
        stat=Stat.WORK_RATE,
        groups=(Group.FARMERS,),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(
            Subject.VILLAGER,
            Subject.FOOD,
        ),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.RARE,
        effects=(pct(0.08),),
    ),
)
