"""Yamato: "Cavalry and Naval civilization" (RoR string 120160)."""

from crucible.bonuses.model import Civ, Group, Stat, pct
from crucible.boons.model import Boon, Building, Domain, Kind, Rarity, Subject

BOONS = (
    Boon(
        civ=Civ.YAMATO,
        number=1,
        title="Fishing Boats: Work speed",
        stat=Stat.WORK_RATE,
        targets=(
            "fishing_boat",
            "fishing_ship",
        ),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(
            Subject.SHIP,
            Subject.FOOD,
        ),
        buildings=(Building.DOCK,),
        rarity=Rarity.COMMON,
        effects=(pct(0.1),),
    ),
    Boon(
        civ=Civ.YAMATO,
        number=2,
        title="Cavalry, Horse Archers: Cost",
        stat=Stat.COST,
        targets=(
            "horse_archer",
            "heavy_horse_archer",
        ),
        groups=(Group.CAVALRY,),
        domain=Domain.MILITARY,
        kind=Kind.DISCOUNT,
        subjects=(
            Subject.CAVALRY,
            Subject.ARCHER,
        ),
        buildings=(
            Building.STABLE,
            Building.ARCHERY_RANGE,
        ),
        rarity=Rarity.COMMON,
        effects=(pct(-0.07),),
    ),
    Boon(
        civ=Civ.YAMATO,
        number=3,
        title="Ships: HP",
        stat=Stat.HP,
        groups=(Group.SHIPS,),
        domain=Domain.MILITARY,
        kind=Kind.DURABILITY,
        subjects=(Subject.SHIP,),
        buildings=(Building.DOCK,),
        rarity=Rarity.COMMON,
        effects=(pct(0.08),),
    ),
)
