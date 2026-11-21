"""Minoans: "Archer and Naval civilization" (RoR string 120154)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Subject, Tier, ladder

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
        tiers=ladder(Tier.COMMON, pct(-0.15), pct(-0.3), pct(-0.45)),
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
        tiers=ladder(Tier.IMPROVED, flat(1), flat(2), flat(3)),
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
        tiers=ladder(Tier.IMPROVED, pct(0.1), pct(0.2), pct(0.3)),
    ),
    Boon(
        civ=Civ.MINOANS,
        number=4,
        title="Dock: Cost",
        stat=Stat.COST,
        targets=("dock",),
        domain=Domain.ECONOMY,
        kind=Kind.DISCOUNT,
        subjects=(
            Subject.SHIP,
            Subject.BUILDING,
        ),
        buildings=(Building.DOCK,),
        flags=(Flag.TEAM,),
        tiers=ladder(Tier.POOR, pct(-0.2), pct(-0.4), pct(-0.6)),
    ),
)
