"""Assyrians: "Archer and Siege civilization" (RoR string 120153)."""

from crucible.bonuses.model import Civ, Group, Stat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Subject, Tier, extra, ladder

BOONS = (
    Boon(
        civ=Civ.ASSYRIANS,
        number=1,
        title="Villager: Movement speed",
        stat=Stat.SPEED,
        groups=(Group.VILLAGERS,),
        domain=Domain.ECONOMY,
        kind=Kind.SPEED,
        subjects=(Subject.VILLAGER,),
        buildings=(Building.TOWN_CENTER,),
        tiers=ladder(Tier.IMPROVED, pct(0.1), pct(0.2), pct(0.3)),
    ),
    Boon(
        civ=Civ.ASSYRIANS,
        number=2,
        title="Archers: Attack speed",
        stat=Stat.ATTACK_SPEED,
        groups=(Group.ARCHERS,),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.ARCHER,),
        buildings=(Building.ARCHERY_RANGE,),
        tiers=ladder(Tier.COMMON, pct(0.11), pct(0.22), pct(0.33)),
    ),
    Boon(
        civ=Civ.ASSYRIANS,
        number=3,
        title="Siege: Research Cost",
        stat=Stat.COST,
        techs=(
            "catapult",
            "heavy_catapult",
            "helepolis",
            "balista",
        ),
        domain=Domain.RESEARCH,
        kind=Kind.DISCOUNT,
        subjects=(Subject.SIEGE,),
        buildings=(Building.SIEGE_WORKSHOP,),
        tiers=ladder(Tier.MASTERCRAFTED, pct(-0.5), pct(-0.75), (pct(-1), extra(pct(-1), Stat.RESEARCH_TIME))),
    ),
    Boon(
        civ=Civ.ASSYRIANS,
        number=4,
        title="Siege Workshop: Work speed",
        stat=Stat.WORK_RATE,
        targets=("siege_workshop",),
        domain=Domain.MILITARY,
        kind=Kind.PRODUCTION,
        subjects=(
            Subject.SIEGE,
            Subject.BUILDING,
        ),
        buildings=(Building.SIEGE_WORKSHOP,),
        flags=(Flag.TEAM,),
        tiers=ladder(Tier.COMMON, pct(0.2), pct(0.4), pct(0.6)),
    ),
)
