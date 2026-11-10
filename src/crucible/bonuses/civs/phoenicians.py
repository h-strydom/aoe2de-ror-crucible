"""Phoenicians: "Elephant and Naval civilization" (RoR string 120156).

• Woodcutters work 15% faster and carry +2 wood
• Elephant units cost -25%
• Catapult Trireme and Juggernaut fire 33% faster
• Docks +150 HP, +4 line of sight
Team Bonus:
Archers +2 line of sight
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=pct(0.15),
        stat=Stat.WORK_RATE,
        groups=(Group.WOODCUTTERS,),
        tags=(Tag.WOOD, Tag.ECONOMY, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.PHOENICIANS,
        name="Phoenicians 1",
        icon=Icon.WOOD,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.CARRY,
        groups=(Group.WOODCUTTERS,),
        tags=(Tag.WOOD, Tag.ECONOMY, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.PHOENICIANS,
        name="Phoenicians 2",
        icon=Icon.WOOD,
    ),
    Modifier(
        change=pct(-0.25),
        stat=Stat.COST,
        targets=("war_elephant", "armored_elephant", "elephant_archer"),
        tags=(Tag.ELEPHANT, Tag.STABLE, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.PHOENICIANS,
        name="Phoenicians 3",
        icon=Icon.ELEPHANT,
    ),
    Modifier(
        change=pct(0.33),
        stat=Stat.ATTACK_SPEED,
        targets=("catapult_trireme", "juggernaut"),
        tags=(Tag.SHIP, Tag.DOCK, Tag.SIEGE, Tag.UNIT),
        civ=Civ.PHOENICIANS,
        name="Phoenicians 4",
        icon=Icon.SHIP,
    ),
    Modifier(
        change=flat(150),
        stat=Stat.HP,
        targets=("dock",),
        tags=(Tag.DOCK, Tag.BUILDING),
        civ=Civ.PHOENICIANS,
        name="Phoenicians 5",
        icon=Icon.DOCK,
    ),
    Modifier(
        change=flat(4),
        stat=Stat.LINE_OF_SIGHT,
        targets=("dock",),
        tags=(Tag.DOCK, Tag.BUILDING),
        civ=Civ.PHOENICIANS,
        name="Phoenicians 6",
        icon=Icon.DOCK,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.LINE_OF_SIGHT,
        groups=(Group.ARCHERS,),
        tags=(Tag.ARCHER, Tag.UNIT, Tag.TEAM),
        civ=Civ.PHOENICIANS,
        name="Phoenicians 7",
        icon=Icon.ARCHER,
    ),
)
