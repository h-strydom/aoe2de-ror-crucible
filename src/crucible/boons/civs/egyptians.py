"""Egyptians: "Chariot and Priest civilization" (RoR string 120150)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Kind, Rarity, Subject, extra

BOONS = (
    Boon(
        civ=Civ.EGYPTIANS,
        number=2,
        title="Gold miners: Work rate, carry capacity",
        stat=Stat.WORK_RATE,
        groups=(Group.GOLD_MINERS,),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(
            Subject.VILLAGER,
            Subject.GOLD,
        ),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.COMMON,
        effects=(
            pct(0.1),
            extra(flat(2), Stat.CARRY),
        ),
        note="Merged: egyptians_3",
    ),
    Boon(
        civ=Civ.EGYPTIANS,
        number=4,
        title="Chariots: HP",
        stat=Stat.HP,
        targets=(
            "chariot",
            "chariot_archer",
            "scythe_chariot",
        ),
        domain=Domain.MILITARY,
        kind=Kind.COMBAT,
        subjects=(Subject.CHARIOT,),
        buildings=(
            Building.STABLE,
            Building.ARCHERY_RANGE,
        ),
        rarity=Rarity.COMMON,
        effects=(pct(0.08),),
    ),
    Boon(
        civ=Civ.EGYPTIANS,
        number=5,
        title="Priest: Range, pierce armour",
        stat=Stat.RANGE,
        targets=("priest",),
        domain=Domain.MILITARY,
        kind=Kind.FAITH,
        subjects=(Subject.PRIEST,),
        buildings=(Building.TEMPLE,),
        rarity=Rarity.RARE,
        effects=(
            flat(1),
            extra(flat(1), Stat.PIERCE_ARMOUR),
        ),
        note="Merged: egyptians_6",
    ),
)
