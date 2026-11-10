"""Minoans: "Archer and Naval civilization" (RoR string 120154).

• Ships cost -15/-20/-25/-30% in Stone/Tool/Bronze/Iron Age
• Improved Bowman-line +1/+2 range in Bronze/Iron Age
• Farmers work 10% faster
Team Bonus:
Docks cost -20%
"""

from crucible.bonuses.model import Civ, Group, Icon, Modifier, Rarity, Stat, Tag, flat, pct

MODIFIERS = (
    Modifier(
        change=pct(-0.3),
        stat=Stat.COST,
        groups=(Group.SHIPS,),
        tags=(Tag.SHIP, Tag.DOCK, Tag.UNIT),
        civ=Civ.MINOANS,
        name="Minoans 1",
        icon=Icon.SHIP,
        rarity=Rarity.COMMON,
    ),
    Modifier(
        change=flat(2),
        stat=Stat.RANGE,
        targets=("improved_bowman", "composite_bowman"),
        tags=(Tag.ARCHER, Tag.ARCHERY_RANGE, Tag.UNIT),
        civ=Civ.MINOANS,
        name="Minoans 2",
        icon=Icon.ARCHER,
        rarity=Rarity.LEGENDARY,
    ),
    Modifier(
        change=pct(0.1),
        stat=Stat.WORK_RATE,
        groups=(Group.FARMERS,),
        tags=(Tag.FOOD, Tag.ECONOMY, Tag.VILLAGER, Tag.UNIT),
        civ=Civ.MINOANS,
        name="Minoans 3",
        icon=Icon.FARM,
        rarity=Rarity.RARE,
    ),
    Modifier(
        change=pct(-0.2),
        stat=Stat.COST,
        targets=("dock",),
        tags=(Tag.DOCK, Tag.SHIP, Tag.BUILDING, Tag.TEAM),
        civ=Civ.MINOANS,
        name="Minoans 4",
        icon=Icon.DOCK,
        rarity=Rarity.COMMON,
    ),
)
