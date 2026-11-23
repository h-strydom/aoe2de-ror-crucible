"""Palmyrans: "Camel and Trading civilization" (RoR string 120164)."""

from crucible.bonuses.model import Civ, Group, Stat, flat, pct
from crucible.boons.model import Boon, Building, Domain, Flag, Kind, Rarity, Subject, extra

BOONS = (
    Boon(
        civ=Civ.PALMYRANS,
        number=2,
        title="Villager: Melee and pierce armour",
        stat=Stat.MELEE_ARMOUR,
        groups=(Group.VILLAGERS,),
        domain=Domain.ECONOMY,
        kind=Kind.DURABILITY,
        subjects=(Subject.VILLAGER,),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.COMMON,
        effects=(
            flat(1),
            extra(flat(1), Stat.PIERCE_ARMOUR),
        ),
        note="Merged: palmyrans_3",
    ),
    Boon(
        civ=Civ.PALMYRANS,
        number=4,
        title="Villager: Work speed",
        stat=Stat.WORK_RATE,
        groups=(Group.VILLAGERS,),
        domain=Domain.ECONOMY,
        kind=Kind.GATHERING,
        subjects=(Subject.VILLAGER,),
        buildings=(Building.TOWN_CENTER,),
        rarity=Rarity.LEGENDARY,
        effects=(pct(0.06),),
    ),
    Boon(
        civ=Civ.PALMYRANS,
        number=8,
        title="Trade Boats: Trade gold",
        stat=Stat.TRADE_GOLD,
        targets=(
            "trade_boat",
            "merchant_ship",
        ),
        domain=Domain.ECONOMY,
        kind=Kind.RESOURCES,
        subjects=(
            Subject.TRADE,
            Subject.SHIP,
            Subject.GOLD,
        ),
        buildings=(Building.DOCK,),
        rarity=Rarity.COMMON,
        effects=(pct(0.1),),
    ),
    Boon(
        civ=Civ.PALMYRANS,
        number=9,
        title="Research speed",
        stat=Stat.RESEARCH_SPEED,
        domain=Domain.RESEARCH,
        kind=Kind.PRODUCTION,
        subjects=(Subject.TECHNOLOGY,),
        flags=(Flag.TEAM,),
        rarity=Rarity.LEGENDARY,
        effects=(pct(0.5),),
        levels=1,
    ),
)
