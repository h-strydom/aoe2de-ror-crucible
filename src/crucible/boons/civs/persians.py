"""Persians: "Elephant and Naval civilization" (RoR string 120158)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Rarity, Subject, extra

BOONS = (
    Boon(
        civ=Civ.PERSIANS,
        number=1,
        title="Hunters: Work rate, carry capacity",
        stat=Stat.WORK_RATE,
        groups=(Group.HUNTERS,),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(
            Subject.VILLAGER,
            Subject.FOOD,
        ),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.COMMON,
        effects=(
            pct(0.1),
            extra(flat(2), Stat.CARRY),
        ),
        note="Merged: persians_2",
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
        rarity=Rarity.COMMON,
        effects=(pct(0.06),),
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
        rarity=Rarity.RARE,
        effects=(pct(0.08),),
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
        rarity=Rarity.LEGENDARY,
        effects=(pct(0.6),),
        levels=1,
    ),
)
