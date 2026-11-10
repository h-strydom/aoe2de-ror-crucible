"""Macedonians: "Infantry civilization" (RoR string 120165).

• All non-ranged units +2 line of sight
• Academy units +1P armor in Bronze Age, +2 in Iron Age
• Siege Workshop units cost -25%
• All units 4 times more resistant to conversion
Team Bonus:
Houses +50 HP
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=flat(2),
        stat=Stat.LINE_OF_SIGHT,
        groups=(Group.NON_RANGED,),
        tags=(Tag.UNIT, Tag.INFANTRY, Tag.CAVALRY),
        civ=Civ.MACEDONIANS,
        name="Macedonians 1",
        icon=Icon.INFANTRY,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.PIERCE_ARMOUR,
        targets=("hoplite", "phalangite", "centurion"),
        tags=(Tag.ACADEMY, Tag.INFANTRY, Tag.HOPLITE, Tag.UNIT),
        civ=Civ.MACEDONIANS,
        name="Macedonians 2",
        icon=Icon.ACADEMY,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(-0.25),
        stat=Stat.COST,
        targets=("stone_thrower", "catapult", "heavy_catapult", "ballista", "helepolis"),
        tags=(Tag.SIEGE, Tag.SIEGE_WORKSHOP, Tag.UNIT),
        civ=Civ.MACEDONIANS,
        name="Macedonians 3",
        icon=Icon.SIEGE,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=pct(3),
        stat=Stat.CONVERSION_RESISTANCE,
        groups=(Group.ALL_UNITS,),
        tags=(Tag.UNIT, Tag.PRIEST),
        civ=Civ.MACEDONIANS,
        name="Macedonians 4",
        icon=Icon.TEMPLE,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=flat(50),
        stat=Stat.HP,
        targets=("house",),
        tags=(Tag.BUILDING, Tag.TEAM),
        civ=Civ.MACEDONIANS,
        name="Macedonians 5",
        icon=Icon.HOUSE,
        rarity=Rarity.COMMON,
    ),
)
