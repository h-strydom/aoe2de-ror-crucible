"""Assyrians: "Archer and Siege civilization" (RoR string 120153)."""

from crucible.bonuses.model import Civ, Group, Stat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Rarity, Subject

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
        rarity=Rarity.RARE,
        effects=(pct(0.05),),
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
        rarity=Rarity.LEGENDARY,
        effects=(pct(0.08),),
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
        rarity=Rarity.LEGENDARY,
        effects=(pct(0.6),),
        levels=1,
    ),
)
