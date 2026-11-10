"""Romans: "Infantry civilization" (RoR string 120162).

• Buildings cost -10%, except for towers, walls and Wonders
• Towers cost -40%
• Swordsmen attack 50% faster
• Ballista and Helepolis +1 range
Team Bonus:
Priests +50% heal speed
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=pct(-0.1),
        stat=Stat.COST,
        targets=(
            "town_center",
            "house",
            "barracks",
            "dock",
            "granary",
            "storage_pit",
            "market",
            "farm",
            "archery_range",
            "stable",
            "academy",
            "siege_workshop",
            "temple",
            "government_center",
        ),
        tags=(Tag.BUILDING, Tag.ECONOMY),
        civ=Civ.ROMANS,
        name="Romans 1",
        subject="Buildings (except towers, walls and Wonders)",
        icon=Icon.BUILDING,
    ),
    Modifier(
        change=pct(-0.4),
        stat=Stat.COST,
        groups=(Group.TOWERS,),
        tags=(Tag.TOWER, Tag.DEFENCE, Tag.BUILDING),
        civ=Civ.ROMANS,
        name="Romans 2",
        icon=Icon.TOWER,
    ),
    Modifier(
        change=pct(0.5),
        stat=Stat.ATTACK_SPEED,
        targets=("short_swordsman", "broad_swordsman", "long_swordsman", "legionary"),
        tags=(Tag.INFANTRY, Tag.SWORDSMAN, Tag.BARRACKS, Tag.UNIT),
        civ=Civ.ROMANS,
        name="Romans 3",
        icon=Icon.INFANTRY,
    ),
    Modifier(
        change=flat(1),
        stat=Stat.RANGE,
        targets=("ballista", "helepolis"),
        tags=(Tag.SIEGE, Tag.SIEGE_WORKSHOP, Tag.UNIT),
        civ=Civ.ROMANS,
        name="Romans 4",
        icon=Icon.SIEGE,
    ),
    Modifier(
        change=pct(0.5),
        stat=Stat.HEAL_SPEED,
        targets=("priest",),
        tags=(Tag.PRIEST, Tag.TEMPLE, Tag.UNIT, Tag.TEAM),
        civ=Civ.ROMANS,
        name="Romans 5",
        icon=Icon.PRIEST,
    ),
)
