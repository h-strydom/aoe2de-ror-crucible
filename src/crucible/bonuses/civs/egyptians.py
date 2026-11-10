"""Egyptians: "Chariot and Priest civilization" (RoR string 120150).

• Farms cost -20%
• Gold Miners work 20% faster and carry +2 gold
• Chariot units +33% hit points
• Priests +2/+3 range in Bronze/Iron Age
Team Bonus:
Priests +1P Armor
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=pct(-0.2),
        stat=Stat.COST,
        targets=("farm",),
        tags=(Tag.ECONOMY, Tag.FOOD, Tag.BUILDING),
        civ=Civ.EGYPTIANS,
        name="Egyptians 1",
        icon=Icon.FARM,
    ),
    Modifier(
        change=pct(0.2),
        stat=Stat.WORK_RATE,
        groups=(Group.GOLD_MINERS,),
        tags=(Tag.ECONOMY, Tag.GOLD, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.EGYPTIANS,
        name="Egyptians 2",
        icon=Icon.GOLD,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.CARRY,
        groups=(Group.GOLD_MINERS,),
        tags=(Tag.ECONOMY, Tag.GOLD, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.EGYPTIANS,
        name="Egyptians 3",
        icon=Icon.GOLD,
    ),
    Modifier(
        change=pct(0.33),
        stat=Stat.HP,
        targets=("chariot", "chariot_archer", "scythe_chariot"),
        tags=(Tag.CHARIOT, Tag.STABLE, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.EGYPTIANS,
        name="Egyptians 4",
        icon=Icon.CHARIOT,
    ),
    Modifier(
        change=flat(3),
        stat=Stat.RANGE,
        targets=("priest",),
        tags=(Tag.PRIEST, Tag.TEMPLE, Tag.UNIT),
        civ=Civ.EGYPTIANS,
        name="Egyptians 5",
        icon=Icon.PRIEST,
    ),
    Modifier(
        change=flat(1),
        stat=Stat.PIERCE_ARMOUR,
        targets=("priest",),
        tags=(Tag.PRIEST, Tag.TEMPLE, Tag.UNIT, Tag.TEAM),
        civ=Civ.EGYPTIANS,
        name="Egyptians 6",
        icon=Icon.PRIEST,
    ),
)
