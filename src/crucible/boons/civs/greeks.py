"""Greeks: "Infantry and Naval civilization" (RoR string 120151)."""

from crucible.bonuses.model import Civ, Group, Stat, pct
from crucible.boons.model import Boon, Building, Domain, Kind, Rarity, Subject

BOONS = (
    Boon(
        civ=Civ.GREEKS,
        number=1,
        title="Town Center: Work speed",
        stat=Stat.WORK_RATE,
        targets=("town_center",),
        domain=Domain.ECONOMY,
        kind=Kind.PRODUCTION,
        subjects=(
            Subject.VILLAGER,
            Subject.BUILDING,
        ),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.LEGENDARY,
        effects=(pct(0.3),),
        levels=1,
    ),
    Boon(
        civ=Civ.GREEKS,
        number=2,
        title="Hoplites: Movement speed",
        stat=Stat.SPEED,
        targets=(
            "hoplite",
            "phalangite",
            "centurion",
        ),
        domain=Domain.MILITARY,
        kind=Kind.SPEED,
        subjects=(
            Subject.INFANTRY,
            Subject.HOPLITE,
        ),
        buildings=(Building.ACADEMY,),
        rarity=Rarity.COMMON,
        effects=(pct(0.06),),
    ),
    Boon(
        civ=Civ.GREEKS,
        number=3,
        title="Hoplites: Cost",
        stat=Stat.COST,
        targets=(
            "hoplite",
            "phalangite",
            "centurion",
        ),
        domain=Domain.MILITARY,
        kind=Kind.DISCOUNT,
        subjects=(
            Subject.INFANTRY,
            Subject.HOPLITE,
        ),
        buildings=(Building.ACADEMY,),
        rarity=Rarity.COMMON,
        effects=(pct(-0.06),),
    ),
    Boon(
        civ=Civ.GREEKS,
        number=4,
        title="Ships: Movement speed",
        stat=Stat.SPEED,
        groups=(Group.SHIPS,),
        domain=Domain.MILITARY,
        kind=Kind.SPEED,
        subjects=(Subject.SHIP,),
        buildings=(Building.DOCK,),
        rarity=Rarity.COMMON,
        effects=(pct(0.05),),
    ),
)
