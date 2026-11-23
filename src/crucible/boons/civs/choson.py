"""Choson: "Infantry and Tower civilization" (RoR string 120161)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Kind, Rarity, Subject

BOONS = (
    Boon(
        civ=Civ.CHOSON,
        number=2,
        title="Swordsman line: HP",
        stat=Stat.HP,
        targets=(
            "short_swordsman",
            "broad_swordsman",
            "long_swordsman",
            "legionary",
        ),
        domain=Domain.MILITARY,
        kind=Kind.DURABILITY,
        subjects=(
            Subject.INFANTRY,
            Subject.SWORDSMAN,
        ),
        buildings=(Building.BARRACKS,),
        rarity=Rarity.RARE,
        effects=(flat(8),),
    ),
    Boon(
        civ=Civ.CHOSON,
        number=4,
        title="Towers: Range",
        stat=Stat.RANGE,
        groups=(Group.TOWERS,),
        domain=Domain.DEFENCE,
        kind=Kind.COMBAT,
        subjects=(
            Subject.TOWER,
            Subject.BUILDING,
        ),
        rarity=Rarity.RARE,
        effects=(flat(1),),
    ),
    Boon(
        civ=Civ.CHOSON,
        number=5,
        title="Priest: Cost",
        stat=Stat.COST,
        targets=("priest",),
        domain=Domain.MILITARY,
        kind=Kind.DISCOUNT,
        subjects=(Subject.PRIEST,),
        buildings=(Building.TEMPLE,),
        rarity=Rarity.COMMON,
        effects=(pct(-0.08),),
    ),
)
