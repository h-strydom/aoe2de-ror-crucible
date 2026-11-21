"""Persians: "Elephant and Naval civilization" (RoR string 120158)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Subject, Tier, ladder

BOONS = (
    Boon(
        civ=Civ.PERSIANS,
        number=1,
        title="Villager: Work speed, Hunting",
        stat=Stat.WORK_RATE,
        groups=(Group.HUNTERS,),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(
            Subject.VILLAGER,
            Subject.FOOD,
        ),
        buildings=(Building.TOWN_CENTER,),
        tiers=ladder(Tier.POOR, pct(0.15), pct(0.3), pct(0.5)),
    ),
    Boon(
        civ=Civ.PERSIANS,
        number=2,
        title="Villager: Capacity, hunting",
        stat=Stat.CARRY,
        groups=(Group.HUNTERS,),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(
            Subject.VILLAGER,
            Subject.FOOD,
        ),
        buildings=(Building.TOWN_CENTER,),
        tiers=ladder(Tier.POOR, flat(3), flat(6), flat(9)),
    ),
    Boon(
        civ=Civ.PERSIANS,
        number=3,
        title="Elephants: Movement speed",
        stat=Stat.SPEED,
        targets=(
            "war_elephant",
            "armored_elephant",
            "elephant_archer",
        ),
        domain=Domain.MILITARY,
        kind=Kind.SPEED,
        subjects=(Subject.ELEPHANT,),
        buildings=(
            Building.STABLE,
            Building.ARCHERY_RANGE,
        ),
        tiers=ladder(Tier.COMMON, pct(0.15), pct(0.25), pct(0.35)),
    ),
    Boon(
        civ=Civ.PERSIANS,
        number=4,
        title="War ships: Attack speed",
        stat=Stat.ATTACK_SPEED,
        targets=(
            "scout_ship",
            "war_galley",
            "trireme",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.SHIP,),
        buildings=(Building.DOCK,),
        tiers=ladder(Tier.COMMON, pct(0.15), pct(0.33), pct(0.5)),
    ),
    Boon(
        civ=Civ.PERSIANS,
        number=5,
        title="Walls: HP regeneration",
        stat=Stat.HP_REGENERATION,
        groups=(Group.WALLS,),
        domain=Domain.DEFENCE,
        kind=Kind.DURABILITY,
        subjects=(
            Subject.WALL,
            Subject.BUILDING,
        ),
        tiers=ladder(Tier.POOR, flat(10), flat(20), flat(40)),
        note="HP a minute",
    ),
    Boon(
        civ=Civ.PERSIANS,
        number=6,
        title="Stable: Work speed",
        stat=Stat.WORK_RATE,
        targets=("stable",),
        domain=Domain.MILITARY,
        kind=Kind.PRODUCTION,
        subjects=(
            Subject.CAVALRY,
            Subject.BUILDING,
        ),
        buildings=(Building.STABLE,),
        flags=(Flag.TEAM,),
        tiers=ladder(Tier.POOR, pct(0.2), pct(0.4), pct(0.6)),
    ),
)
