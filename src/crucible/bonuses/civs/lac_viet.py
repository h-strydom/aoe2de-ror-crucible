"""Lac Viet: "Archer civilization" (RoR string 120166).

• Foragers work 15% faster
• Military Units created 25% faster
• Archery Range units and Ballista +2 armor
Team Bonus:
Houses and farms built 50% faster
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=pct(0.15),
        stat=Stat.WORK_RATE,
        groups=(Group.FORAGERS,),
        tags=(Tag.FOOD, Tag.ECONOMY, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.LAC_VIET,
        name="Lac Viet 1",
        icon=Icon.FOOD,
    ),
    Modifier(
        change=pct(0.25),
        stat=Stat.TRAINING_SPEED,
        groups=(Group.MILITARY,),
        tags=(Tag.UNIT,),
        civ=Civ.LAC_VIET,
        name="Lac Viet 2",
        icon=Icon.BARRACKS,
    ),
    Modifier(
        change=flat(2),
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
        tags=(Tag.ARCHER, Tag.ARCHERY_RANGE, Tag.SIEGE, Tag.UNIT),
        civ=Civ.LAC_VIET,
        name="Lac Viet 3",
        subject="Archery Range units and Ballistas",
        icon=Icon.ARCHER,
    ),
    Modifier(
        change=pct(0.5),
        stat=Stat.BUILD_SPEED,
        targets=("house", "farm"),
        tags=(Tag.BUILDING, Tag.ECONOMY, Tag.TEAM),
        civ=Civ.LAC_VIET,
        name="Lac Viet 4",
        icon=Icon.HOUSE,
    ),
)
