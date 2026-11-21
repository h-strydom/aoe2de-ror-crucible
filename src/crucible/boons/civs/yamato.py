"""Yamato: "Cavalry and Naval civilization" (RoR string 120160)."""

from crucible.bonuses.model import Civ, Group, Stat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Subject, Tier, extra, ladder

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
        tiers=ladder(Tier.POOR, pct(0.2), pct(0.35), pct(0.5)),
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
        tiers=ladder(Tier.IMPROVED, pct(-0.15), pct(-0.25), pct(-0.35)),
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
        tiers=ladder(Tier.POOR, pct(0.15), pct(0.25), pct(0.4)),
    ),
    Boon(
        civ=Civ.YAMATO,
        number=4,
        title="Stable, Archery Range: Research cost",
        stat=Stat.COST,
        techs=(
            "chariot",
            "cavalry",
            "war_elephant",
            "heavy_cavalry",
            "cataphract",
            "armored_elephant",
            "heavy_chariots",
            "advanced_horse_archer",
            "improved_bow",
            "composite_bow",
            "chariot_archer",
            "horse_archer",
            "elephant_archer",
        ),
        domain=Domain.RESEARCH,
        kind=Kind.DISCOUNT,
        subjects=(
            Subject.CAVALRY,
            Subject.ARCHER,
        ),
        buildings=(
            Building.STABLE,
            Building.ARCHERY_RANGE,
        ),
        tiers=ladder(Tier.MASTERCRAFTED, pct(-0.3), pct(-0.5), (pct(-0.75), extra(pct(-0.5), Stat.RESEARCH_TIME))),
    ),
    Boon(
        civ=Civ.YAMATO,
        number=5,
        title="Stable, Archery Range: Wood cost",
        stat=Stat.WOOD_COST,
        targets=(
            "stable",
            "archery_range",
        ),
        domain=Domain.ECONOMY,
        kind=Kind.DISCOUNT,
        subjects=(Subject.BUILDING,),
        buildings=(
            Building.STABLE,
            Building.ARCHERY_RANGE,
        ),
        flags=(Flag.TEAM,),
        tiers=ladder(Tier.POOR, pct(-0.33), pct(-0.5), pct(-0.75)),
    ),
)
