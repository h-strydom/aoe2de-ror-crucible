"""Phoenicians: "Elephant and Naval civilization" (RoR string 120156)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Kind, Rarity, Subject, extra

BOONS = (
    Boon(
        civ=Civ.PHOENICIANS,
        number=1,
        title="Woodcutters: Work rate, carry capacity",
        stat=Stat.WORK_RATE,
        groups=(Group.WOODCUTTERS,),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(
            Subject.VILLAGER,
            Subject.WOOD,
        ),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.RARE,
        effects=(
            pct(0.1),
            extra(flat(2), Stat.CARRY),
        ),
        note="Merged: phoenicians_2",
    ),
    Boon(
        civ=Civ.PHOENICIANS,
        number=3,
        title="Elephants: Cost",
        stat=Stat.COST,
        targets=(
            "war_elephant",
            "armored_elephant",
            "elephant_archer",
        ),
        domain=Domain.MILITARY,
        kind=Kind.DISCOUNT,
        subjects=(Subject.ELEPHANT,),
        buildings=(
            Building.STABLE,
            Building.ARCHERY_RANGE,
        ),
        rarity=Rarity.COMMON,
        effects=(pct(-0.07),),
    ),
    Boon(
        civ=Civ.PHOENICIANS,
        number=4,
        title="Catapult Triremes: Attack speed",
        stat=Stat.ATTACK_SPEED,
        targets=(
            "catapult_trireme",
            "juggernaut",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(
            Subject.SHIP,
            Subject.SIEGE,
        ),
        buildings=(Building.DOCK,),
        rarity=Rarity.COMMON,
        effects=(pct(0.08),),
    ),
)
