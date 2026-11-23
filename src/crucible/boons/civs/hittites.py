"""Hittites: "Archer and Siege civilization" (RoR string 120155)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Rarity, Subject

BOONS = (
    Boon(
        civ=Civ.HITTITES,
        number=1,
        title="Archers: Attack",
        stat=Stat.ATTACK,
        groups=(Group.ARCHERS,),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.ARCHER,),
        buildings=(Building.ARCHERY_RANGE,),
        rarity=Rarity.LEGENDARY,
        effects=(flat(1),),
    ),
    Boon(
        civ=Civ.HITTITES,
        number=2,
        title="Stone Throwers: HP",
        stat=Stat.HP,
        targets=(
            "stone_thrower",
            "catapult",
            "heavy_catapult",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.SIEGE,),
        buildings=(Building.SIEGE_WORKSHOP,),
        rarity=Rarity.COMMON,
        effects=(pct(0.1),),
    ),
    Boon(
        civ=Civ.HITTITES,
        number=3,
        title="War ships: Range",
        stat=Stat.RANGE,
        targets=(
            "scout_ship",
            "war_galley",
            "trireme",
            "catapult_trireme",
            "juggernaut",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.SHIP,),
        buildings=(Building.DOCK,),
        rarity=Rarity.RARE,
        effects=(flat(1),),
    ),
    Boon(
        civ=Civ.HITTITES,
        number=6,
        title="Towers: Population room",
        stat=Stat.POPULATION,
        groups=(Group.TOWERS,),
        domain=Domain.DEFENCE,
        kind=Kind.POPULATION,
        subjects=(
            Subject.TOWER,
            Subject.BUILDING,
        ),
        flags=(Flag.TEAM,),
        rarity=Rarity.COMMON,
        effects=(flat(2),),
    ),
)
