"""Lac Viet: "Archer civilization" (RoR string 120166)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Rarity, Subject

BOONS = (
    Boon(
        civ=Civ.LAC_VIET,
        number=1,
        title="Villager: Work speed, Foraging",
        stat=Stat.WORK_RATE,
        groups=(Group.FORAGERS,),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(
            Subject.VILLAGER,
            Subject.FOOD,
        ),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.COMMON,
        effects=(pct(0.1),),
    ),
    Boon(
        civ=Civ.LAC_VIET,
        number=2,
        title="Military units: Training speed",
        stat=Stat.TRAINING_SPEED,
        groups=(Group.MILITARY,),
        domain=Domain.MILITARY,
        kind=Kind.PRODUCTION,
        subjects=(
            Subject.INFANTRY,
            Subject.ARCHER,
            Subject.CAVALRY,
        ),
        rarity=Rarity.LEGENDARY,
        effects=(pct(0.5),),
        levels=1,
    ),
    Boon(
        civ=Civ.LAC_VIET,
        number=3,
        title="Archery Range units, Ballistas: Melee armour",
        stat=Stat.MELEE_ARMOUR,
        targets=(
            "bowman",
            "improved_bowman",
            "composite_bowman",
            "chariot_archer",
            "horse_archer",
            "heavy_horse_archer",
            "elephant_archer",
            "ballista",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(
            Subject.ARCHER,
            Subject.SIEGE,
        ),
        buildings=(Building.ARCHERY_RANGE,),
        rarity=Rarity.RARE,
        effects=(flat(1),),
    ),
    Boon(
        civ=Civ.LAC_VIET,
        number=4,
        title="Houses, Farms: Build speed",
        stat=Stat.BUILD_SPEED,
        targets=(
            "house",
            "farm",
        ),
        domain=Domain.ECONOMY,
        kind=Kind.PRODUCTION,
        subjects=(
            Subject.BUILDING,
            Subject.FOOD,
        ),
        flags=(Flag.TEAM,),
        rarity=Rarity.LEGENDARY,
        effects=(pct(0.9),),
        levels=1,
    ),
)
