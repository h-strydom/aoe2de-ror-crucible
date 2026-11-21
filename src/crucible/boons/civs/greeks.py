"""Greeks: "Infantry and Naval civilization" (RoR string 120151)."""

from crucible.bonuses.model import Civ, Group, Stat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Subject, Tier, ladder

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
        tiers=ladder(Tier.IMPROVED, pct(0.1), pct(0.2), pct(0.3)),
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
        tiers=ladder(Tier.COMMON, pct(0.1), pct(0.2), pct(0.3)),
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
        tiers=ladder(Tier.COMMON, pct(-0.1), pct(-0.2), pct(-0.3)),
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
        tiers=ladder(Tier.POOR, pct(0.1), pct(0.2), pct(0.3)),
    ),
    Boon(
        civ=Civ.GREEKS,
        number=5,
        title="Polytheism, Astrology: Research cost",
        stat=Stat.COST,
        techs=(
            "polytheism",
            "astrology",
        ),
        domain=Domain.RESEARCH,
        kind=Kind.DISCOUNT,
        subjects=(Subject.PRIEST,),
        buildings=(Building.TEMPLE,),
        tiers=ladder(Tier.POOR, pct(-0.5), pct(-0.75), pct(-1)),
    ),
    Boon(
        civ=Civ.GREEKS,
        number=6,
        title="Market: Cost",
        stat=Stat.COST,
        targets=("market",),
        domain=Domain.ECONOMY,
        kind=Kind.DISCOUNT,
        subjects=(
            Subject.MARKET,
            Subject.BUILDING,
        ),
        buildings=(Building.MARKET,),
        flags=(Flag.TEAM,),
        tiers=ladder(Tier.POOR, pct(-0.25), pct(-0.5), pct(-1)),
    ),
)
